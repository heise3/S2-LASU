from pathlib import Path
import sys,os,json,hashlib,re,shutil,platform
sys.dont_write_bytecode=True
import numpy as np,pandas as pd
from scipy.stats import t,norm
from scipy.optimize import minimize_scalar
from definitions import SPECS,STATE_CODES,exclusion
from lasu_models import fe_fit
O=Path(__file__).resolve().parents[1];ROOT=O.parents[1];T=O/'tables';E=O/'evidence'
os.environ['MPLCONFIGDIR']=str(E/'matplotlib_cache')
def save(d,n):
 d=pd.DataFrame(d);d.to_csv(T/n,index=False,float_format='%.12g');return d
def prepare():
 cache=T/'matched_published_rows.csv.gz'
 if cache.exists():return pd.read_csv(cache,dtype={'Prscrbr_Geo_Cd':str},keep_default_na=True)
 rows=[];exc=[];inv=[];inputs=[];geo=[]
 need=['Prscrbr_Geo_Lvl','Prscrbr_Geo_Cd','Prscrbr_Geo_Desc','Gnrc_Name','Brnd_Name','Tot_Clms','Tot_30day_Fills','GE65_Tot_Clms','GE65_Tot_30day_Fills','GE65_Sprsn_Flag']
 for y in range(2013,2025):
  f=ROOT/f'work/full_csv/B_{y}.csv';d=pd.read_csv(f,dtype=str,keep_default_na=False);inv += [dict(year=y,field=c,position=i) for i,c in enumerate(d.columns)];assert set(need)<=set(d)
  inputs.append(dict(year=y,path=str(f.relative_to(ROOT)),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),n_rows=len(d)))
  d=d[need].copy();d['year']=y;d['source_row']=np.arange(len(d))+2
  for col in ['Tot_Clms','Tot_30day_Fills','GE65_Tot_Clms','GE65_Tot_30day_Fills']:d[col]=pd.to_numeric(d[col].str.replace(',','',regex=False),errors='coerce')
  for lvl,code,name in d[['Prscrbr_Geo_Lvl','Prscrbr_Geo_Cd','Prscrbr_Geo_Desc']].drop_duplicates().itertuples(index=False,name=None):
   if lvl!='State' or code not in STATE_CODES:geo.append(dict(year=y,level=lvl,code=code,name=name,reason='national_used_separately' if lvl=='National' else 'not_one_of_50_states'))
  for id,organ,label,pat,page,first,scope,qual in SPECS:
   z=d[d.Gnrc_Name.str.contains(pat,case=False,regex=True)].copy();z['entry']=id
   z['exclusion']=[exclusion(id,g,b) for g,b in zip(z.Gnrc_Name,z.Brnd_Name)];exc.append(z[z.exclusion.ne('')]);rows.append(z[z.exclusion.eq('')])
  print('read',y,flush=True)
 d=pd.concat(rows,ignore_index=True);d.to_csv(cache,index=False,compression='gzip');pd.concat(exc).to_csv(T/'excluded_formulation_rows.csv.gz',index=False,compression='gzip');save(inv,'actual_field_inventory.csv');save(geo,'excluded_geographic_units.csv');(E/'input_manifest.json').write_text(json.dumps(inputs,indent=2))
 return d

def bounds(d):
 d=d.copy();F=d.Tot_30day_Fills;C=d.Tot_Clms;v=d.GE65_Tot_30day_Fills;m=v.isna();star=d.GE65_Sprsn_Flag.eq('*')
 assert d.loc[m,'GE65_Sprsn_Flag'].isin(['*','#']).all();assert (F>=C-.11).all() and (F<=12*C+.11).all()
 U=np.minimum(120,np.maximum(0,F-np.maximum(C-10,0)))
 d['lo']=v.where(~m,np.where(star,0,F-U));d['hi']=v.where(~m,np.where(star,U,F))
 for sc,values in {'observed':v,'primary_small_lower':np.where(star,d.lo,d.hi),'primary_small_upper':np.where(star,d.hi,d.lo),'old_lower_young_upper':d.lo,'old_upper_young_lower':d.hi}.items():d[sc]=values
 assert (d.lo>=-.11).all() and (d.hi<=F+.11).all()
 return d

def run():
 global T,E
 d=bounds(prepare());
 if '--filter-low-generics' in sys.argv:
  originalT=T;T=T/'drug_filtered';E=E/'drug_filtered';T.mkdir(exist_ok=True);E.mkdir(exist_ok=True);(O/'figures/drug_filtered').mkdir(exist_ok=True)
  shutil.copy2(originalT/'enrollment_denominators.csv',T/'enrollment_denominators.csv')
  raw=d[d.Prscrbr_Geo_Lvl.eq('National')].drop_duplicates(['year','source_row']);gv=raw.groupby('Gnrc_Name').GE65_Tot_30day_Fills.sum();low=gv[gv<100000].index
  save(gv.rename('national_ge65_2013_2024').reset_index(),'generic_volume_audit.csv');d[d.Gnrc_Name.isin(low)].to_csv(T/'excluded_low_volume_generic_rows.csv.gz',index=False,compression='gzip');save(gv[gv<100000].rename('national_ge65_2013_2024').reset_index(),'excluded_low_volume_generics.csv');d=d[~d.Gnrc_Name.isin(low)].copy()
 d['Prscrbr_Geo_Cd']=d.Prscrbr_Geo_Cd.fillna('').str.zfill(2);d.GE65_Sprsn_Flag=d.GE65_Sprsn_Flag.fillna('')
 den=pd.read_csv(T/'enrollment_denominators.csv').set_index(['year','age']).enrollee_person_years
 names=d[['entry','year','Gnrc_Name','Brnd_Name']].drop_duplicates();save(names,'matched_names_by_year.csv')
 d[d.GE65_Tot_30day_Fills.isna()].to_csv(T/'suppressed_rows_with_bounds.csv.gz',index=False,compression='gzip')
 overlap=d[d.entry.ne('long_su')].groupby(['year','source_row']).entry.agg(list);save([dict(year=k[0],source_row=k[1],entries=';'.join(v),n_entries=len(v)) for k,v in overlap.items() if len(v)>1],'cross_entry_overlap.csv')
 panels=[];national=[];summ=[];dictionary=[]
 for id,organ,label,pat,page,first,scope,qual in SPECS:
  z=d[d.entry.eq(id)];nat=z[z.Prscrbr_Geo_Lvl.eq('National')];state=z[z.Prscrbr_Geo_Lvl.eq('State')&z.Prscrbr_Geo_Cd.isin(STATE_CODES)]
  volume=nat.GE65_Tot_30day_Fills.sum();lo=nat.lo.sum();hi=nat.hi.sum();included=volume>=100000 and id!='estrogens'
  reason='INCLUDED' if included else ('NOT_ESTIMABLE_ROUTE' if id=='estrogens' else ('NO_MATCHED_PUBLISHED_ROWS' if len(nat)==0 else 'LOW_VOLUME_LT100000'))
  dic=dict(entry=id,organ=organ,label=label,regex=pat,source_2023=f'AGS2023 Table2 PDF p{page}',source_2023_url='https://geriatrictoolkit.missouri.edu/drug/Beers-Criteria-AGS-2023.pdf',first_Table2_family_reviewed=first,current_scope_version=scope,first_ever_Beers='UNVERIFIED',qualification=qual,role='benchmark' if id=='long_su' else 'Table2_entry',status=reason,national_ge65_2013_2024=volume,national_lower=lo,national_upper=hi,threshold_ambiguous=lo<100000<=hi,n_unique_generic=z.Gnrc_Name.nunique())
  dictionary.append(dic)
  sm=dict(entry=id,label=label,role=dic['role'],status=reason,national_ge65_fills=volume,n_state_published_rows=len(state),ge65_suppressed_rows=state.GE65_Tot_30day_Fills.isna().sum(),lt65_unrecoverable_rows=state.GE65_Tot_30day_Fills.isna().sum(),ge65_primary_suppressed_rows=state.GE65_Sprsn_Flag.eq('*').sum(),lt65_primary_suppressed_rows=state.GE65_Sprsn_Flag.eq('#').sum())
  for key in ['ge65_suppressed_rows','lt65_unrecoverable_rows','ge65_primary_suppressed_rows','lt65_primary_suppressed_rows']:sm[key+'_pct']=100*sm[key]/len(state) if len(state) else np.nan
  summ.append(sm)
  for year,g in nat.groupby('year'):
   for age in ['ge65','lt65']:
    old=age=='ge65';v=g.observed if old else g.Tot_30day_Fills-g.observed;lower=g.lo.sum() if old else (g.Tot_30day_Fills-g.hi).sum();upper=g.hi.sum() if old else (g.Tot_30day_Fills-g.lo).sum();D=den.loc[(year,age)]
    national.append(dict(entry=id,year=year,age=age,n_rows=len(g),n_suppressed=int(g.observed.isna().sum()),fills_observed=v.sum(min_count=1),fills_lower=lower,fills_upper=upper,enrollee_person_years=D,rate_observed_per1000py=1000*v.sum(min_count=1)/D,rate_lower=1000*lower/D,rate_upper=1000*upper/D))
  for year in range(2013,2025):
   for code,st in STATE_CODES.items():
    g=state[state.year.eq(year)&state.Prscrbr_Geo_Cd.eq(code)]
    for age in ['ge65','lt65']:
     old=age=='ge65';D=den.loc[(year,age)];r=dict(entry=id,state=st,year=year,age=age,old=int(old),n_rows=len(g),n_suppressed=int(g.observed.isna().sum()),enrollee_person_years=D)
     for sc in ['observed','primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower']:
      v=g[sc] if old else g.Tot_30day_Fills-g[sc];r[sc]=v.sum(min_count=1) if len(g) else np.nan
     r['row_complete']=bool(len(g)>0 and not g.observed.isna().any());panels.append(r)
 cat=save(dictionary,'drug_criteria_manifest.csv');save(summ,'K1_feasibility.csv');save(national,'national_annual_rates.csv');pan=save(panels,'state_age_panel_volumes.csv');save(cat[~cat.status.eq('INCLUDED')],'excluded_entries.csv')
 eligible=cat[cat.status.eq('INCLUDED')];coeff=[];sample=[];fits={};modelpan=[]
 if len(eligible[eligible.role.eq('Table2_entry')])<10:raise RuntimeError('K1 KILL: fewer than 10 entries; downstream not run')
 for _,c in eligible.iterrows():
  p=pan[pan.entry.eq(c.entry)].copy()
  for sc in ['observed','primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower','complete_published']:
   v=p['observed' if sc=='complete_published' else sc];ok=np.isfinite(v)&(v>0)
   if sc=='complete_published':ok &= p.row_complete
   ok=ok & ok.groupby([p.state,p.year]).transform('all');q=p[ok].copy();q['su_observed']=1.;q['share_pct']=np.log(v[ok]*1000/q.enrollee_person_years)
   for idx,r in p[~ok].iterrows():sample.append(dict(entry=c.entry,scenario=sc,state=r.state,year=r.year,age=r.age,reason='unpublished_group' if r.n_rows==0 else 'incomplete_published_group' if sc=='complete_published' and not r.row_complete else 'nonpositive_or_missing_age_volume_or_partner'))
   if q.state.nunique()<3 or q.year.nunique()<3 or len(q)//2<5:
    coeff.append(dict(entry=c.entry,scenario=sc,model='trend',term='old_t',status='NOT_ESTIMABLE',n_cells=len(q),n_states=q.state.nunique()));continue
   rr,f=fe_fit(q,2);coeff.extend(r|dict(entry=c.entry,scenario=sc,model='trend',status='OK') for r in rr)
   if sc=='observed':
    fits[c.entry]=q;modelpan.append(q.assign(scenario=sc))
    # Algebraically equivalent paired-age regression is an independent numeric check.
    w=q.pivot(index=['state','year'],columns='old',values='share_pct').reset_index();b=np.linalg.lstsq(np.c_[np.ones(len(w)),w.year-2013],w[1]-w[0],rcond=None)[0];assert np.allclose(b,f['beta'],atol=1e-10)
    # National denominator contribution is identical across entries given their sample.
    raw=q.copy();raw.share_pct=np.log(v[ok]);rr,_=fe_fit(raw,2);coeff.extend(r|dict(entry=c.entry,scenario='raw_volume',model='trend',status='OK') for r in rr)
    # New full-scope criteria plus documented scope expansion are explicitly labeled.
    nodes=sorted(set(int(a) for a in [c.first_Table2_family_reviewed,c.current_scope_version] if int(a)>2013))
    for node in nodes:
     rr,_=fe_fit(q,2,post=node);coeff.extend(r|dict(entry=c.entry,scenario='observed',model=f'post_{node}',status='OK',node_type='new_Table2' if node==c.first_Table2_family_reviewed else 'scope_expansion') for r in rr)
 cf=save(coeff,'K2_all_coefficients.csv');save(sample,'model_excluded_cells.csv');pd.concat(modelpan).to_csv(T/'K2_primary_model_panel.csv.gz',index=False,compression='gzip')
 main=cf[cf.scenario.eq('observed')&cf.model.eq('trend')&cf.term.eq('old_t')].merge(cat[['entry','organ','label','role','qualification','current_scope_version']],on='entry');main['relative_change_pct_per_year']=100*np.expm1(main.coefficient);main['negative_CI_excludes0']=main.ci_high.lt(0);main['positive_CI_excludes0']=main.ci_low.gt(0)
 from statsmodels.stats.multitest import multipletests
 good=main.status.eq('OK');main.loc[good,'p_BH_FDR']=multipletests(main.loc[good,'p_value'],method='fdr_bh')[1];save(main,'K2_entry_results.csv')
 effects=main[main.role.eq('Table2_entry')&good];beta=effects.coefficient.to_numpy();vi=effects.se.to_numpy()**2
 def meta(b,v):
  def loss(tau):
   w=1/(v+tau);mu=np.sum(w*b)/sum(w);return np.log(v+tau).sum()+np.log(w.sum())+np.sum(w*(b-mu)**2)
  opt=minimize_scalar(loss,bounds=(0,max(.1,float(np.var(b))*10)),method='bounded',options={'xatol':1e-12});tau=opt.x if opt.fun<loss(0) else 0.;w=1/(v+tau);mu=np.sum(w*b)/sum(w);se=np.sqrt(1/sum(w));q=np.sum((b-np.sum(b/v)/sum(1/v))**2/v);return dict(k=len(b),pooled_beta=mu,se_independence=se,ci_low_independence=mu-1.96*se,ci_high_independence=mu+1.96*se,tau2=tau,Q=q,I2_pct=max(0,(q-len(b)+1)/q)*100,method='REML; independent-entry conventional CI descriptive')
 met=meta(beta,vi)
 # Same state resampling across entries retains cross-entry covariance. Bootstrap point estimates only;
 # keep original within-entry variance as descriptive meta weights in each replicate.
 rng=np.random.default_rng(20261027);states=list(STATE_CODES.values());arrays=[]
 for ent in effects.entry:
  q=fits[ent];w=q.pivot(index=['state','year'],columns='old',values='share_pct').reset_index();arrays.append((np.c_[np.ones(len(w)),w.year-2013],(w[1]-w[0]).to_numpy(),w.state.to_numpy()))
 boot=[]
 for rep in range(1000):
  draws=rng.choice(states,50,replace=True);ct={s:int(np.sum(draws==s)) for s in states};bs=[]
  for X,y,st in arrays:
   w=np.array([ct[s] for s in st]);bs.append(np.linalg.lstsq(X*np.sqrt(w[:,None]),y*np.sqrt(w),rcond=None)[0][1])
  boot.append(meta(np.array(bs),vi)['pooled_beta'])
 met['state_bootstrap_low'],met['state_bootstrap_high']=np.quantile(boot,[.025,.975]);met['bootstrap_reps']=1000;save([met],'K3_random_effects_meta.csv');save({'replicate':np.arange(1000),'pooled_beta':boot},'K3_state_bootstrap.csv')
 bench=main[main.entry.eq('long_su')].iloc[0];(E/'summary_numbers.json').write_text(json.dumps(dict(n_Table2=36,n_eligible=len(eligible[eligible.role.eq('Table2_entry')]),n_estimable=len(effects),negative_significant=int(effects.negative_CI_excludes0.sum()),positive_significant=int(effects.positive_CI_excludes0.sum()),negative_fraction=float(effects.negative_CI_excludes0.mean()),long_su_beta=float(bench.coefficient),long_su_percentile=float(100*np.mean(beta<bench.coefficient)),meta=met),indent=2))
 forest=main[main.status.eq('OK')].sort_values(['organ','entry']).reset_index(drop=True);save(forest,'K3_forest_data.csv')
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'font.size':9})
 fig,ax=plt.subplots(figsize=(11,13));ys=np.arange(len(forest));colors=['#b54a24' if e=='long_su' else '#21658b' for e in forest.entry]
 for i,r in forest.iterrows():ax.errorbar(r.coefficient,i,xerr=[[r.coefficient-r.ci_low],[r.ci_high-r.coefficient]],fmt='o',ms=4,color=colors[i],capsize=2,lw=1.1)
 ax.set_yticks(ys,forest.label);ax.invert_yaxis();ax.axvline(0,color='#555555',lw=.8,ls='--');ax.set_xlabel('Older vs younger annual difference in log volume per national age-specific enrollee-year\nState × year fixed effects; state-cluster 95% CI');ax.set_title('S2-BEERS: Table 2 drug-exposure trends, 2013–2024',loc='left',weight='bold');ax.grid(axis='x',alpha=.18)
 for i in range(1,len(forest)):
  if forest.organ.iloc[i]!=forest.organ.iloc[i-1]:ax.axhline(i-.5,color='#dddddd',lw=.7)
 fig.text(.02,.015,'Exposure proxies, not adjudicated PIM use. Orange: nested LASU benchmark (excluded from meta).\nPrimary estimates use recoverable age-visible rows; suppression and complete-row sensitivity results supplied separately.',fontsize=8)
 fig.subplots_adjust(left=.43,right=.97,top=.95,bottom=.1);fp=O/('figures/drug_filtered' if '--filter-low-generics' in sys.argv else 'figures');fig.savefig(fp/'K3_forest.pdf');fig.savefig(fp/'K3_forest.png',dpi=220);plt.close(fig)
 print(json.dumps(json.loads((E/'summary_numbers.json').read_text()),indent=2),flush=True)
if __name__=='__main__':run()
