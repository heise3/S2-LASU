"""Frozen-specification descriptive glimepiride addendum. No old output is modified."""
from pathlib import Path
import sys, json, hashlib, datetime, importlib.metadata
sys.dont_write_bytecode=True
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy.stats import t
from statsmodels.stats.sandwich_covariance import cov_cluster
O=Path(__file__).resolve().parents[1];ROOT=O.parents[1];F=ROOT/'outputs/S2_LASU_final_v1_3';T=O/'tables';A=O/'audit'
sys.path.insert(0,str(O/'code/legacy'))
import loader
from rule_bounds import rule_bounds
from original_models import fe_fit
loader.DATA=ROOT/'outputs/data'
STATES=dict(x.split(':') for x in '01:AL 02:AK 04:AZ 05:AR 06:CA 08:CO 09:CT 10:DE 12:FL 13:GA 15:HI 16:ID 17:IL 18:IN 19:IA 20:KS 21:KY 22:LA 23:ME 24:MD 25:MA 26:MI 27:MN 28:MS 29:MO 30:MT 31:NE 32:NV 33:NH 34:NJ 35:NM 36:NY 37:NC 38:ND 39:OH 40:OK 41:OR 42:PA 44:RI 45:SC 46:SD 47:TN 48:TX 49:UT 50:VT 51:VA 53:WA 54:WV 55:WI 56:WY'.split())
def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item())+'\n')
def save(d,name):
    d=pd.DataFrame(d);d.to_csv(T/name,index=False,float_format='%.14g');return d
contract=json.loads((O/'ANALYSIS_CONTRACT.json').read_text());assert sha(O/'ANALYSIS_CONTRACT.json')==(O/'CONTRACT_SHA256').read_text().split()[0]
for rec in json.loads((A/'INPUT_MANIFEST.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256'],rec['path']
req=json.loads((F/'reproduction/source_requirements.json').read_text())
for rec in req:
    if rec['path'].startswith('outputs/data/B_') or rec['path']=='outputs/code/analyze.py':assert sha(ROOT/rec['path'])==rec['sha256'],rec['path']
dump(A/'RUN_STARTED.json',{'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'contract_sha256':sha(O/'ANALYSIS_CONTRACT.json'),'versions':{x:importlib.metadata.version(x) for x in ['numpy','pandas','scipy','statsmodels']}})

def aggregate(g,y,state=None,scenario='observed',values=None):
    if values is None:old=g.GE65_Tot_30day_Fills.to_numpy();young=g.Tot_30day_Fills.to_numpy()-old
    else:old=np.asarray(values);young=g.Tot_30day_Fills.to_numpy()-old
    ans=[]
    for age,oldflag,v in [('ge65',1,old),('lt65',0,young)]:
        S=np.nansum(v);assert S>0
        row=dict(year=y,state=state or 'National',state_name=g.Prscrbr_Geo_Desc.iloc[0],age=age,old=oldflag,scenario=scenario,su_observed=S,age_suppressed_rows=int(g.GE65_Tot_30day_Fills.isna().sum()),n_drug_rows=len(g))
        for fam in ['glimepiride','glyburide','glipizide','chlorpropamide','long']:
            mask=g['class'].eq('long').to_numpy() if fam=='long' else g.Gnrc_Name.str.contains(fam,case=False,regex=True).to_numpy()
            vol=np.nansum(v[mask]);row[fam+'_volume']=vol;row[fam+'_share_pct']=100*vol/S
        row['share_pct']=row['glimepiride_share_pct'];ans.append(row)
    return ans

raw=[];ns=[];ps=[];excluded=[];invalid=[];names=[];erpan=[];scenario_rows=[];alloclog=[]
scenarios=['primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower','target_share_old_low_young_high','target_share_old_high_young_low']
for y in range(2013,2025):
    d=rule_bounds(loader.load('B',y));d['year']=y;raw.append(d)
    names.append(d[['year','Gnrc_Name','Brnd_Name','class','glipizide_er_xl']].drop_duplicates())
    ns+=aggregate(d[d.Prscrbr_Geo_Lvl.eq('National')],y)
    for (level,code),g in d.groupby(['Prscrbr_Geo_Lvl','Prscrbr_Geo_Cd']):
        if level!='State' or code not in STATES:
            excluded.append(dict(year=y,level=level,code=code,name=g.Prscrbr_Geo_Desc.iloc[0],n_rows=len(g),reason='National used separately' if level=='National' else 'Not one of50 states'));continue
        st=STATES[code];ps+=aggregate(g,y,st)
        er=g.copy();er.loc[er.glipizide_er_xl,'class']='long';erpan+=aggregate(er,y,st,'ER_XL_as_long')
        star=g.GE65_Sprsn_Flag.eq('*');target=g.Gnrc_Name.str.contains('glimepiride',case=False)
        for scenario in scenarios:
            if scenario=='primary_small_lower':v=np.where(star,g.old_lower,g.old_upper)
            elif scenario=='primary_small_upper':v=np.where(star,g.old_upper,g.old_lower)
            elif scenario=='old_lower_young_upper':v=g.old_lower.to_numpy()
            elif scenario=='old_upper_young_lower':v=g.old_upper.to_numpy()
            elif scenario=='target_share_old_low_young_high':v=np.where(target,g.old_lower,g.old_upper)
            else:v=np.where(target,g.old_upper,g.old_lower)
            assert np.all(v>=-1e-9) and np.all(v<=g.Tot_30day_Fills.to_numpy()+1e-9)
            known=g.GE65_Tot_30day_Fills.notna();assert np.allclose(v[known],g.loc[known,'GE65_Tot_30day_Fills'])
            scenario_rows+=aggregate(g,y,st,scenario,v)
            z=g.loc[~known,['year','Prscrbr_Geo_Cd','Gnrc_Name','Brnd_Name','GE65_Sprsn_Flag','Tot_30day_Fills','old_lower','old_upper']].copy()
            z['old_allocated']=v[~known];z['young_allocated']=z.Tot_30day_Fills-z.old_allocated;z['scenario']=scenario;alloclog.append(z)
raw=pd.concat(raw,ignore_index=True);save(raw,'matched_geography_drug_rows.csv.gz');save(pd.concat(names),'matched_names.csv')
save(raw[raw.GE65_Tot_30day_Fills.isna()],'suppressed_rows_with_rule_bounds.csv');save(pd.concat(alloclog),'suppression_allocations.csv.gz');save(excluded,'excluded_geographic_units.csv')
nat=save(ns,'national_family_shares.csv');p=save(ps,'state_age_year_observed.csv');sp=save(scenario_rows,'state_age_year_allocations.csv');er=save(erpan,'state_age_year_ER_reclassified.csv')
assert len(p)==1200 and p.state.nunique()==50 and not p[['state','year','age']].duplicated().any()
for col in ['share_pct','su_observed','glimepiride_volume']:assert np.array_equal(p[col].to_numpy(),er[col].to_numpy()),col
save(pd.DataFrame(columns=['state','year','age','reason']), 'excluded_age_cells.csv')

# Verify the regenerated denominators and old endpoints against frozen source products.
orig=pd.read_csv(F/'tables/details/lasu_v1/A2_state_age_panel.csv')
z=p.merge(orig,on=['state','year','age'],suffixes=('_new','_old'),validate='one_to_one')
assert np.allclose(z.su_observed_new,z.su_observed_old,rtol=1e-10)
assert np.allclose(z.long_share_pct,z.share_pct_old,atol=1e-8)
ref=pd.read_csv(F/'tables/main/T1_national_age_trends.csv');n=nat.merge(ref,on=['year','age'],suffixes=('_new','_old'))
for fam in ['long','glimepiride','glyburide']:assert np.allclose(n[fam+'_share_pct_new'],n[fam+'_share_pct_old'],atol=1e-8)
original_complete=pd.read_csv(F/'tables/details/robustness_v1_1/R2_complete_state_years.csv')
cp=p[p.age_suppressed_rows.eq(0)].copy();keys=lambda d:set(map(tuple,d[['state','year']].drop_duplicates().to_numpy()))
assert keys(cp)==keys(original_complete) and len(cp)==206 and cp.state.nunique()==41
save(original_complete,'fully_visible_state_years.csv');save(cp,'fully_visible_panel.csv')

def fit(d,periods=False):
    d=d.sort_values(['state','year','old']).copy();n=len(d)
    period=np.select([d.year.le(2018),d.year.le(2022)],['2013-2018','2019-2022'],default='2023-2024')
    names=['2013-2018','2019-2022','2023-2024'] if periods else ['overall']
    X=np.column_stack([d.old.to_numpy()*(period==name) for name in names]) if periods else d.old.to_numpy()[:,None]
    y=d.share_pct.to_numpy();w=d.su_observed.to_numpy();w=w/w.mean()
    groups=pd.factorize(d.state+'_'+d.year.astype(str))[0];cl=pd.factorize(d.state)[0];G=cl.max()+1;ng=groups.max()+1;k=ng+X.shape[1]
    mass=np.bincount(groups,weights=w);ym=np.bincount(groups,weights=w*y)/mass
    xm=np.column_stack([np.bincount(groups,weights=w*X[:,j])/mass for j in range(X.shape[1])]);xx=X-xm[groups];yy=y-ym[groups]
    bread=np.linalg.inv(xx.T@(w[:,None]*xx));beta=bread@(xx.T@(w*yy));res=yy-xx@beta
    score=np.column_stack([np.bincount(cl,weights=w*xx[:,j]*res,minlength=G) for j in range(X.shape[1])])
    factor=G/(G-1)*(n-1)/(n-k);cov=factor*bread@(score.T@score)@bread;se=np.sqrt(np.diag(cov));crit=t.ppf(.975,G-1)
    # Independent paired-age WLS, explicitly using the identical full-FE CR1 factor.
    wide=d.pivot(index=['state','year'],columns='old',values=['share_pct','su_observed']);gap=wide['share_pct'][1]-wide['share_pct'][0];pw=wide['su_observed'][1]*wide['su_observed'][0]/wide['su_observed'].sum(axis=1)
    yrs=wide.index.get_level_values('year');pp=np.select([yrs<=2018,yrs<=2022],['2013-2018','2019-2022'],default='2023-2024')
    px=np.column_stack([pp==name for name in names]).astype(float) if periods else np.ones((len(wide),1))
    independent=sm.WLS(gap,px,weights=pw).fit();cv=cov_cluster(independent,wide.index.get_level_values('state'),use_correction=False)*factor
    assert np.allclose(beta,independent.params,atol=1e-9) and np.allclose(cov,cv,atol=1e-9)
    rows=[dict(period=name,estimate_pp=beta[j],se=se[j],ci_low=beta[j]-crit*se[j],ci_high=beta[j]+crit*se[j],p_value=2*t.sf(abs(beta[j]/se[j]),G-1),n_cells=n,n_state_years=ng,n_states=G,full_FE_rank=k,CR1_factor=factor,df_cluster=G-1,paired_beta_max_error=float(np.max(abs(beta-independent.params))),paired_cov_max_error=float(np.max(abs(cov-cv)))) for j,name in enumerate(names)]
    return rows
models=[]
for scenario,d in [('observed',p),*list(sp.groupby('scenario')),('fully_visible_103',cp),('ER_XL_as_long_invariant',er)]:
    for byperiod in [False,True]:models.extend([row|{'scenario':scenario,'model':'period_levels' if byperiod else 'pooled_level'} for row in fit(d,byperiod)])
models=save(models,'glimepiride_state_models.csv')
gp=p.pivot(index=['state','state_name','year'],columns='age',values=['share_pct','su_observed']).reset_index();gp.columns=['_'.join(c).strip('_') for c in gp.columns]
gp['gap_pp']=gp.share_pct_ge65-gp.share_pct_lt65
for scenario,col in [('target_share_old_low_young_high','gap_lower_pp'),('target_share_old_high_young_low','gap_upper_pp')]:
    q=sp[sp.scenario.eq(scenario)].pivot(index=['state','year'],columns='age',values='share_pct');q[col]=q.ge65-q.lt65;gp=gp.merge(q[[col]],on=['state','year'],validate='one_to_one')
gp['bound_width_pp']=gp.gap_upper_pp-gp.gap_lower_pp;assert gp.bound_width_pp.ge(-1e-9).all();save(gp,'state_annual_glimepiride_gaps.csv')
counts=gp.groupby('year').agg(states=('state','size'),positive=('gap_pp',lambda x:int(x.gt(0).sum())),positive_lower_bound=('gap_lower_pp',lambda x:int(x.gt(0).sum())),min_gap=('gap_pp','min'),max_gap=('gap_pp','max'),max_bound_width=('bound_width_pp','max')).reset_index();save(counts,'state_annual_positive_counts.csv')
by=gp.groupby('state').agg(positive_years=('gap_pp',lambda x:int(x.gt(0).sum())),n_years=('year','size'));save(by.reset_index(),'state_positive_year_counts.csv')
ep=gp[gp.year.isin([2019,2024])].pivot(index=['state','state_name'],columns='year',values=['gap_pp','gap_lower_pp','gap_upper_pp','bound_width_pp']).reset_index();ep.columns=['_'.join(map(str,c)).strip('_') for c in ep.columns];ep['change_2019_2024']=ep.gap_pp_2024-ep.gap_pp_2019;save(ep.sort_values('gap_pp_2024'),'state_2019_2024_figure_data.csv')

wide=nat.pivot(index='year',columns='age',values=[x+'_share_pct' for x in ['glimepiride','glyburide','glipizide','chlorpropamide','long']]);nw=pd.DataFrame({'year':wide.index})
for fam in ['glimepiride','glyburide','glipizide','chlorpropamide','long']:
    for age in ['ge65','lt65']:nw[fam+'_'+age]=wide[fam+'_share_pct'][age].to_numpy()
    nw[fam+'_gap_pp']=nw[fam+'_ge65']-nw[fam+'_lt65']
assert np.allclose(nw.long_gap_pp,nw.glimepiride_gap_pp+nw.glyburide_gap_pp+nw.chlorpropamide_gap_pp)
save(nw,'national_annual_gaps.csv');decomp=[]
for start,end in [(2013,2024),(2015,2019),(2019,2024),(2019,2023)]:
    w=nw.set_index('year');tot=w.loc[end,'long_gap_pp']-w.loc[start,'long_gap_pp']
    for fam in ['glimepiride','glyburide','chlorpropamide','long']:
        delta=w.loc[end,fam+'_gap_pp']-w.loc[start,fam+'_gap_pp'];decomp.append(dict(start=start,end=end,family=fam,gap_start=w.loc[start,fam+'_gap_pp'],gap_end=w.loc[end,fam+'_gap_pp'],gap_change_pp=delta,share_of_total_gap_change_pct=100*delta/tot if abs(tot)>1e-12 else np.nan,note='Exact arithmetic endpoint decomposition, not model attribution or causal contribution'))
save(decomp,'national_gap_change_decomposition.csv')
rates=[]
for age in ['ge65','lt65']:
    rr=ref[ref.age.eq(age)].set_index('year')
    for fam in ['SU','long','glimepiride','glyburide','glipizide']:
        k=fam+'_fills30_per1000_enrollee_py';rates.append(dict(age=age,family=fam,rate_2013=rr.loc[2013,k],rate_2024=rr.loc[2024,k],change_pct=100*(rr.loc[2024,k]/rr.loc[2013,k]-1)))
save(rates,'national_rate_changes.csv')
legacy=p.copy();legacy['share_pct']=legacy.long_share_pct;legacyfit,_=fe_fit(legacy,2);save(legacyfit,'legacy_long_trend_verification.csv')
primary=models[models.scenario.eq('observed')&models.period.eq('overall')].iloc[0];four=models[models.scenario.isin(scenarios[:4])&models.period.eq('overall')]
decision='NATIONAL_ONLY_FALLBACK' if primary.estimate_pp<=1e-8 else ('WEAK' if primary.ci_low<=0 else ('SUPPORTED_STATE_LEVEL' if four.ci_low.gt(0).all() else 'MIXED_SENSITIVITY'))
dump(O/'DECISION.json',dict(status=decision,primary=primary.to_dict(),four_allocation_CIs_positive=bool(four.ci_low.gt(0).all()),states_positive_all12=int((by.positive_years==12).sum()),states_2024_positive=int(counts.set_index('year').loc[2024,'positive']),states_2019_to2024_gap_decreased=int(ep.change_2019_2024.lt(0).sum()),ER_XL='EXACT_INVARIANCE_NOT_DISTINCT_SENSITIVITY',scope='Descriptive weighted within-state-year level difference, no causal age effect or Beers policy effect'))
before=json.loads((A/'PROTECTED_BEFORE.json').read_text());assert all(sha(ROOT/path)==h for path,h in before.items())
dump(A/'ANALYSIS_QA.json',dict(status='PASS',protected_files=len(before),protected_changes=0,original_complete_subset_state_years=103,complete_states=41,primary_cells=1200,coefficient_rows=len(models),model_fits=18,independent_max_beta_error=float(models.paired_beta_max_error.max()),independent_max_cov_error=float(models.paired_cov_max_error.max()),ER_reclassification_invariant=True,national_matches_frozen=True,state_denominators_match_frozen=True,unmatched_drug_names=0,excluded_age_cells=0,contract_sha256=sha(O/'ANALYSIS_CONTRACT.json')))
dump(O/'STATUS.json',dict(status='ANALYSIS_COMPLETE',decision=decision,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_source_unchanged=True,manuscript_publication='NOT_SUBMITTED',public_archive_updated=False))
print(models[models.period.eq('overall')][['scenario','estimate_pp','ci_low','ci_high']].to_string(index=False));print(models[(models.scenario=='observed')&(models.model=='period_levels')][['period','estimate_pp','ci_low','ci_high']].to_string(index=False));print('DECISION',decision)
