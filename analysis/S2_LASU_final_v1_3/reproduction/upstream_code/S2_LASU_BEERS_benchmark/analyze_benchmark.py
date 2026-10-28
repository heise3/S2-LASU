from pathlib import Path
import sys,json,hashlib,datetime,os
sys.dont_write_bytecode=True
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from lasu_models import fe_fit
from definitions import STATE_CODES
O=Path(__file__).resolve().parents[1];ROOT=O.parents[1];T=O/'tables';E=O/'evidence';B=O.parent/'S2_BEERS_precheck';BT=B/'tables/drug_filtered'
freeze=json.loads((E/'mapping_freeze.json').read_text())
for r in freeze['files']:assert hashlib.sha256((O/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
(E/('analysis_started_resume.json' if '--reuse-panel' in sys.argv else 'analysis_started.json')).write_text(json.dumps(dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mapping_frozen_utc=freeze['frozen_utc'],frozen_files_verified=len(freeze['files'])),indent=2))
m=pd.read_csv(T/'therapeutic_class_map_frozen.csv');nm=pd.read_csv(T/'numerator_names_frozen.csv',keep_default_na=False);match=pd.read_csv(T/'generic_atc_matches_frozen.csv');cat=pd.read_csv(T/'inherited_numerator_manifest.csv')
def save(d,name):pd.DataFrame(d).to_csv(T/name,index=False,float_format='%.12g')
scenarios=['observed','primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower']
need=['Prscrbr_Geo_Lvl','Prscrbr_Geo_Cd','Prscrbr_Geo_Desc','Gnrc_Name','Brnd_Name','Tot_Clms','Tot_30day_Fills','GE65_Tot_30day_Fills','GE65_Sprsn_Flag']
if '--reuse-panel' in sys.argv:
 pan=pd.read_csv(T/'state_age_year_share_panel.csv')
else:
 records=[];geo=[];memex=[]
 for year in range(2013,2025):
  f=ROOT/f'work/full_csv/B_{year}.csv';d=pd.read_csv(f,usecols=need,dtype=str,keep_default_na=False);d['source_row']=np.arange(len(d))+2
  for c in ['Tot_Clms','Tot_30day_Fills','GE65_Tot_30day_Fills']:d[c]=pd.to_numeric(d[c].str.replace(',','',regex=False),errors='coerce')
  d.Prscrbr_Geo_Cd=d.Prscrbr_Geo_Cd.str.zfill(2)
  keep=d.Prscrbr_Geo_Lvl.eq('State')&d.Prscrbr_Geo_Cd.isin(STATE_CODES)
  geo.extend(d.loc[~keep,['Prscrbr_Geo_Lvl','Prscrbr_Geo_Cd','Prscrbr_Geo_Desc']].drop_duplicates().assign(year=year).to_dict('records'));d=d[keep].copy();d['state']=d.Prscrbr_Geo_Cd.map(STATE_CODES)
  v=d.GE65_Tot_30day_Fills;F=d.Tot_30day_Fills;C=d.Tot_Clms;small=d.GE65_Sprsn_Flag.eq('*');miss=v.isna();assert d.loc[miss,'GE65_Sprsn_Flag'].isin(['*','#']).all()
  U=np.minimum(120,np.maximum(0,F-np.maximum(C-10,0)));lo=v.where(~miss,np.where(small,0,F-U));hi=v.where(~miss,np.where(small,U,F));d['lo']=lo;d['hi']=hi
  for sc,a in {'observed':v,'primary_small_lower':np.where(small,lo,hi),'primary_small_upper':np.where(small,hi,lo),'old_lower_young_upper':lo,'old_upper_young_lower':hi}.items():d[sc]=a
  pairs=pd.MultiIndex.from_frame(d[['Gnrc_Name','Brnd_Name']])
  for _,r in m.iterrows():
   n=nm[nm.entry.eq(r.entry)&nm.year.eq(year)][['Gnrc_Name','Brnd_Name']].drop_duplicates();num=pairs.isin(pd.MultiIndex.from_frame(n));base=d.Gnrc_Name.isin(set(match[match.ATC_class.isin(r.ATC_classes.split(';'))].Gnrc_Name));den=base|num
   ex=d[num&~base][['state','Gnrc_Name','Brnd_Name','Tot_30day_Fills','GE65_Tot_30day_Fills','source_row']].copy();ex['year']=year;ex['entry']=r.entry;memex.append(ex)
   for state in STATE_CODES.values():
    ns=d[num&d.state.eq(state)];ds=d[den&d.state.eq(state)]
    for age in ['ge65','lt65']:
     rr=dict(entry=r.entry,state=state,year=year,age=age,old=int(age=='ge65'),numerator_rows=len(ns),denominator_rows=len(ds),numerator_suppressed_rows=int(ns.observed.isna().sum()),denominator_suppressed_rows=int(ds.observed.isna().sum()))
     for sc in scenarios:
      nv=ns[sc] if age=='ge65' else ns.Tot_30day_Fills-ns[sc];dv=ds[sc] if age=='ge65' else ds.Tot_30day_Fills-ds[sc]
      rr['num_'+sc]=nv.sum(min_count=1);rr['den_'+sc]=dv.sum(min_count=1)
     records.append(rr)
  print('Panel year',year,flush=True)
 pan=pd.DataFrame(records);save(pan,'state_age_year_share_panel.csv');save(geo,'excluded_geographic_units.csv');pd.concat(memex).to_csv(T/'numerator_membership_exception_rows.csv.gz',index=False,compression='gzip')
# Numerators must exactly reproduce the prior frozen panel.
prior=pd.read_csv(BT/'state_age_panel_volumes.csv');j=pan.merge(prior[['entry','state','year','age','observed']],on=['entry','state','year','age'],validate='one_to_one');assert len(j)==len(pan);assert np.allclose(j.num_observed,j.observed,equal_nan=True,atol=1e-6)
coeff=[];excluded=[];primary_pan=[]
for ent,g in pan.groupby('entry'):
 for sc in scenarios:
  share=g['num_'+sc]/g['den_'+sc];assert (share.dropna()>=-1e-12).all() and (share.dropna()<=1+1e-12).all()
  for scale in ['log','logit']:
   ok=share.gt(0)&share.le(1)&np.isfinite(share)
   if scale=='logit':ok &= share.lt(1)
   ok &= ok.groupby([g.state,g.year]).transform('all')
   for _,rr in g.loc[~ok].iterrows():excluded.append(dict(entry=ent,scenario=sc,scale=scale,state=rr.state,year=rr.year,age=rr.age,numerator=rr['num_'+sc],denominator=rr['den_'+sc],reason='boundary_zero_one_or_missing_or_partner; no pseudocount'))
   q=g[ok].copy();p=share[ok];q['share_pct']=np.log(p) if scale=='log' else np.log(p/(1-p));q['su_observed']=1.;q['share']=p
   if q.state.nunique()<3 or q.year.nunique()<3:
    coeff.append(dict(entry=ent,scenario=sc,scale=scale,term='old_t',status='NOT_ESTIMABLE',n_cells=len(q),n_states=q.state.nunique()));continue
   rr,fit=fe_fit(q,2);coeff.extend(x|dict(entry=ent,scenario=sc,scale=scale,status='OK') for x in rr)
   w=q.pivot(index=['state','year'],columns='old',values='share_pct').reset_index();bb=np.linalg.lstsq(np.c_[np.ones(len(w)),w.year-2013],w[1]-w[0],rcond=None)[0];assert np.allclose(bb,fit['beta'],atol=1e-10)
   if sc=='observed':primary_pan.append(q.assign(scale=scale))
cf=pd.DataFrame(coeff);save(cf,'share_all_coefficients.csv');save(excluded,'share_model_excluded_cells.csv');pd.concat(primary_pan).to_csv(T/'share_primary_model_panel.csv.gz',index=False,compression='gzip')
# The two original comparators are reused without alteration.
orig=pd.read_csv(BT/'K2_all_coefficients.csv');a=orig.query("scenario=='observed' and model=='trend' and term=='old_t'").copy();a['approach']='a_national_denominator'
c=orig.query("scenario=='raw_volume' and model=='trend' and term=='old_t'").copy();c['approach']='c_raw_state_volume'
b=cf.query("scenario=='observed' and term=='old_t'").copy();b['approach']='b_share_'+b.scale
allr=pd.concat([a,b,c],ignore_index=True).merge(cat[['entry','label','organ','role']],on='entry',validate='many_to_one');allr['direction']=np.where(allr.coefficient>0,'positive',np.where(allr.coefficient<0,'negative','zero'));allr['CI_excludes_zero']=(allr.ci_low>0)|(allr.ci_high<0);allr['negative_significant']=allr.ci_high<0
for app,z in allr.groupby('approach'):
 allr.loc[z.index,'within_approach_rank_desc']=z.coefficient.rank(ascending=False,method='min')
save(allr,'three_approach_results_long.csv');fields=['coefficient','se','ci_low','ci_high','direction','CI_excludes_zero','n_cells','n_states'];wide=allr.pivot(index=['entry','label','role'],columns='approach',values=fields);wide.columns=['__'.join(col) for col in wide.columns];wide.reset_index().to_csv(T/'three_approach_comparison.csv',index=False,float_format='%.12g')
rank=[]
for app,z in allr.groupby('approach'):
 refs=z[z.role.eq('Table2_entry')&z.status.eq('OK')];bench=z[z.entry.eq('long_su')].iloc[0];beta=bench.coefficient
 complete=len(refs)==33 and bench.status=='OK';ties=np.isclose(refs.coefficient,beta,atol=1e-12,rtol=0);below=(refs.coefficient<beta)&~ties;pc=100*(below.sum()+.5*ties.sum())/33 if complete else np.nan;quart=int(min(4,np.floor(pc/25)+1)) if complete else None
 rank.append(dict(approach=app,n_estimable_Table2=len(refs),benchmark_beta=beta,benchmark_ci_low=bench.ci_low,benchmark_ci_high=bench.ci_high,benchmark_n_cells=bench.n_cells,n_below=int(below.sum()),n_tied=int(ties.sum()),percentile=pc,quartile=quart,negative_significant_n=int(refs.negative_significant.sum()),negative_significant_fraction=refs.negative_significant.sum()/33 if complete else np.nan,status='OK' if complete else 'NOT_ESTIMABLE_FULL33'))
ranks=pd.DataFrame(rank);save(ranks,'benchmark_percentile_and_decision_inputs.csv')
complete=ranks.status.eq('OK').all();consistent=complete and ranks.quartile.nunique()==1;decision=dict(decision='INCLUDE' if consistent else 'DO_NOT_INCLUDE',reason='All four representations place LASU in the same quartile' if consistent else 'LASU quartile differs across prespecified representations' if complete else 'At least one representation does not estimate all33 entries; full33 percentile unavailable',rule='same quartile for a, b_log, b_logit, c; all33 retained; exact user-approved rule',rank_inputs=rank,estimand='Age-group trend differences; not a Beers policy effect',freeze_utc=freeze['frozen_utc'],decision_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(E/'decision.json').write_text(json.dumps(decision,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)));print(json.dumps(decision,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),flush=True)
# Overall rank correlation is descriptive, not the inclusion gate.
corr=[]
for aa in allr.approach.unique():
 for bb in allr.approach.unique():
  zz=allr[allr.role.eq('Table2_entry')].pivot(index='entry',columns='approach',values='coefficient')[[aa]] if aa==bb else allr[allr.role.eq('Table2_entry')].pivot(index='entry',columns='approach',values='coefficient')[[aa,bb]].dropna()
  rho=1. if aa==bb else spearmanr(zz[aa],zz[bb]).statistic;corr.append(dict(approach_a=aa,approach_b=bb,n=len(zz),Spearman_rho=rho))
save(corr,'overall_rank_correlations.csv')
# Only an accepted benchmark generates a forest for inclusion in LASU.
if consistent:
 os.environ['MPLCONFIGDIR']=str(E/'matplotlib_cache');import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'font.size':8})
 for scale in ['log','logit']:
  z=allr[allr.approach.eq('b_share_'+scale)].sort_values(['organ','entry']).reset_index(drop=True);fig,ax=plt.subplots(figsize=(11,13))
  for i,r in z.iterrows():
   color='#b54a24' if r.entry=='long_su' else '#21658b';ax.errorbar(r.coefficient,i,xerr=[[r.coefficient-r.ci_low],[r.ci_high-r.coefficient]],fmt='o',ms=4,color=color,capsize=2)
  pc=ranks[ranks.approach.eq('b_share_'+scale)].percentile.iloc[0];ax.set_yticks(range(len(z)),z.label);ax.invert_yaxis();ax.axvline(0,ls='--',color='grey',lw=.8);ax.set_xlabel(f'Older vs younger annual difference in {scale}(within-class share)\nState × year FE; state-cluster 95% CI');ax.set_title(f'S2-LASU benchmark: 33 Beers exposure entries; LASU percentile {pc:.1f}',loc='left');fig.text(.02,.02,'Age-group trends, not Beers policy effects. ATC therapeutic classes frozen before fitting.\nOrange: LASU benchmark, excluded from reference distribution; 30-day fills; age-visible rows.',fontsize=8);fig.subplots_adjust(left=.44,right=.98,top=.95,bottom=.11)
  fig.savefig(O/f'figures/within_class_share_forest_{scale}.pdf');fig.savefig(O/f'figures/within_class_share_forest_{scale}.png',dpi=220);plt.close(fig)
