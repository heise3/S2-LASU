from pathlib import Path
import sys,json,hashlib,math,platform,os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
O=Path(__file__).resolve().parents[1];PRE=O.parent
os.environ.setdefault('MPLCONFIGDIR',str(O/'evidence/matplotlib_cache'))
sys.path.insert(0,str(PRE/'code'))
import analyze as base
from models import fe_fit,weighted_logit_reml
for folder in ['tables','figures','evidence']:(O/folder).mkdir(exist_ok=True)
T=O/'tables'
STATE_CODES=dict(x.split(':') for x in '01:AL 02:AK 04:AZ 05:AR 06:CA 08:CO 09:CT 10:DE 12:FL 13:GA 15:HI 16:ID 17:IL 18:IN 19:IA 20:KS 21:KY 22:LA 23:ME 24:MD 25:MA 26:MI 27:MN 28:MS 29:MO 30:MT 31:NE 32:NV 33:NH 34:NJ 35:NM 36:NY 37:NC 38:ND 39:OH 40:OK 41:OR 42:PA 44:RI 45:SC 46:SD 47:TN 48:TX 49:UT 50:VT 51:VA 53:WA 54:WV 55:WI 56:WY'.split())
def save(d,name):
    d=d if isinstance(d,pd.DataFrame) else pd.DataFrame(d)
    d.to_csv(T/name,index=False,float_format='%.12g');return d
def mask(d,family):
    if family=='long':return d['class'].eq('long')
    return d.Gnrc_Name.str.contains(family,case=False,regex=True)
def aggregate(d,year,family='long',metric='fills30',scenario='primary'):
    if scenario=='exclude_ER_XL':d=d[~d.glipizide_er_xl]
    suf=base.METRICS[metric];total=d['Tot_'+suf];old=d['GE65_Tot_'+suf];m=old.isna();target=mask(d,family)
    U=total[m].sum();UL=total[m&target].sum();UN=U-UL
    out=[]
    for age,v in [('ge65',old),('lt65',total-old)]:
        S=v.sum(min_count=1);L=v[target].sum() # no matching published target row means zero within published universe
        r=dict(year=year,age=age,old=int(age=='ge65'),family=family,metric=metric,scenario=scenario,n_drug_rows=len(d),age_suppressed_rows=int(m.sum()),all_age_su=total.sum(),suppressed_all_age_volume=U,suppressed_target_volume=UL,suppressed_nontarget_volume=UN,su_observed=S,target_observed=L,su_lower=S,su_upper=S+U,target_lower=L,target_upper=L+UL,share_pct=100*L/S,share_lower_pct=100*L/(S+UN),share_upper_pct=100*(L+UL)/(S+UL),su_exact=S if not m.any() else np.nan,target_exact=L if not m.any() else np.nan,share_exact_pct=100*L/S if not m.any() else np.nan)
        out.append(r)
    return out

def national_and_panel():
    national=[];panel=[];excluded=[];suppressed=[];sources=[];b2024=None
    for y in range(2013,2025):
        b=base.load('B',y);bn=b[b.Prscrbr_Geo_Lvl.eq('National')]
        sources.append(PRE/f'data/B_{y}_su.csv.gz')
        sup=b[b.GE65_Tot_30day_Fills.isna()|b.GE65_Tot_Benes.isna()].copy();sup['year']=y;suppressed.append(sup)
        for metric in ['fills30','claims']:
            for scenario in ['primary','exclude_ER_XL']:
                for fam in ['long','glimepiride','glyburide']:national+=aggregate(bn,y,fam,metric,scenario)
                for (code,name),g in b[b.Prscrbr_Geo_Lvl.eq('State')].groupby(['Prscrbr_Geo_Cd','Prscrbr_Geo_Desc']):
                    if code not in STATE_CODES:continue
                    for r in aggregate(g,y,'long',metric,scenario):r.update(state=STATE_CODES[code],state_name=name,geo_code=code);panel.append(r)
        for (lvl,code,name),g in b.groupby(['Prscrbr_Geo_Lvl','Prscrbr_Geo_Cd','Prscrbr_Geo_Desc']):
            if lvl=='State' and code in STATE_CODES:continue
            excluded.append(dict(year=y,level=lvl,geo_code=code,unit=name,n_drug_rows=len(g),all_age_SU_fills30=g.Tot_30day_Fills.sum(),reason='National aggregate used in A1; not a state observation' if lvl=='National' else 'Not one of the 50 US states'))
        if y==2024:b2024=bn
    nat=save(national,'A1_national_long.csv');pan=save(panel,'A2_state_age_panel_all_scenarios.csv');save(excluded,'A2_excluded_geographic_units.csv');save(pd.concat(suppressed),'B_age_suppression_rows.csv')
    gaps=[]
    for key,g in nat.groupby(['year','family','metric','scenario']):
        a=g.set_index('age');o=a.loc['ge65'];u=a.loc['lt65']
        gaps.append(dict(zip(['year','family','metric','scenario'],key))|dict(ge65_share_pct=o.share_pct,lt65_share_pct=u.share_pct,gap_pp=o.share_pct-u.share_pct,gap_lower_pp=o.share_lower_pct-u.share_upper_pct,gap_upper_pp=o.share_upper_pct-u.share_lower_pct,ge65_SU=o.su_observed,lt65_SU=u.su_observed,ge65_target=o.target_observed,lt65_target=u.target_observed,age_suppressed_rows=o.age_suppressed_rows))
    gaps=save(gaps,'A1_national_annual.csv')
    slopes=[];overall=[];fits=[]
    for (fam,metric,sc),g in gaps.groupby(['family','metric','scenario']):
        g=g.sort_values('year');yr=g.year.to_numpy();X=np.column_stack([np.ones(len(g)),yr-2013,*[np.maximum(yr-node,0) for node in [2015,2019,2023]]]);H=np.linalg.pinv(X)
        for age,column in [('ge65','ge65_share_pct'),('lt65','lt65_share_pct'),('gap','gap_pp')]:
            b=H@g[column].to_numpy();ols=np.polyfit(yr-2013,g[column],1)[0]
            overall.append(dict(family=fam,metric=metric,scenario=sc,age=age,ols_pp_per_year=ols))
            for i,(start,end) in enumerate([(2013,2015),(2015,2019),(2019,2023),(2023,2024)]):
                c=np.array([0,1,int(i>=1),int(i>=2),int(i>=3)])
                slopes.append(dict(family=fam,metric=metric,scenario=sc,age=age,segment=f'{start}–{end}',start=start,end=end,annual_points_in_interval=end-start+1,slope_pp_per_year=c@b,model='continuous_hinge_OLS_12_years'))
            for y,value in zip(yr,X@b):fits.append(dict(year=y,family=fam,metric=metric,scenario=sc,age=age,fitted_share_or_gap=value))
    save(slopes,'A1_segment_slopes.csv');save(overall,'A1_overall_slopes.csv');save(fits,'A1_piecewise_fitted.csv')
    # All suppression allocations below concern published rows only.
    results=[];boundfits=[];samplelogs=[]
    for (metric,sc),d in pan.groupby(['metric','scenario']):
        d=d.copy();bad=~np.isfinite(d.share_pct)|(d.su_observed<=0)
        for r in d[bad].to_dict('records'):samplelogs.append(r|{'reason':'nonpositive_or_missing_observed_age_SU'})
        d=d[~bad].copy()
        for model in [1,2]:
            rr,_=fe_fit(d,model);results += [r|dict(metric=metric,scenario=sc,sample='observed_age_rows') for r in rr]
        rr,fit=fe_fit(d,2,correction='exclude_nested_FE');results += [r|dict(metric=metric,scenario=sc,sample='CR1_nested_FE_sensitivity') for r in rr]
        complete=d[d.age_suppressed_rows.eq(0)]
        if complete.state.nunique()>2:
            rr,_=fe_fit(complete,2);results += [r|dict(metric=metric,scenario=sc,sample='complete_published_state_years') for r in rr]
        rr,fit=fe_fit(d,2)
        j=fit['names'].index('old_t');a=fit['influence'][j]
        # Relaxed age-cell bounds at fixed observed volume weights; not confidence intervals.
        lo=d.share_lower_pct.to_numpy();hi=d.share_upper_pct.to_numpy()
        boundfits.append(dict(metric=metric,scenario=sc,term='old_t',observed_coefficient=fit['beta'][j],fixed_weight_lower=np.sum(np.where(a>=0,a*lo,a*hi)),fixed_weight_upper=np.sum(np.where(a>=0,a*hi,a*lo)),note='Conservative independent-cell relaxation; weights fixed at visible SU volumes; not a CI'))
        for alloc in ['all_missing_to_old','all_missing_to_young','long_to_old_other_to_young','long_to_young_other_to_old']:
            z=d.copy();old=z.old.eq(1);ul=z.suppressed_target_volume;un=z.suppressed_nontarget_volume
            if alloc=='all_missing_to_old':Ladd=ul.where(old,0);Sadd=(ul+un).where(old,0)
            elif alloc=='all_missing_to_young':Ladd=ul.where(~old,0);Sadd=(ul+un).where(~old,0)
            elif alloc=='long_to_old_other_to_young':Ladd=ul.where(old,0);Sadd=ul.where(old,un)
            else:Ladd=ul.where(~old,0);Sadd=un.where(old,ul)
            z['su_observed']+=Sadd;z['target_observed']+=Ladd;z['share_pct']=100*z.target_observed/z.su_observed
            rr,_=fe_fit(z,2);results += [r|dict(metric=metric,scenario=sc,sample=alloc) for r in rr]
        for start in [2023,2024]:
            rr,_=fe_fit(d,2,post=start);results += [r|dict(metric=metric,scenario=sc,sample=f'post{start}_descriptive') for r in rr]
    mod=save(results,'A2_model_coefficients.csv');save(boundfits,'A2_interaction_suppression_bounds.csv');save(pd.DataFrame(samplelogs,columns=list(pan.columns)+['reason']),'A2_excluded_age_cells.csv')
    p=pan[(pan.metric=='fills30')&(pan.scenario=='primary')];save(p,'A2_state_age_panel.csv')
    state2024=[]
    for state,g in p[p.year.eq(2024)].groupby('state'):
        a=g.set_index('age');o=a.loc['ge65'];u=a.loc['lt65'];state2024.append(dict(state=state,state_name=o.state_name,ge65_share_pct=o.share_pct,lt65_share_pct=u.share_pct,gap_pp=o.share_pct-u.share_pct,gap_lower_pp=o.share_lower_pct-u.share_upper_pct,gap_upper_pp=o.share_upper_pct-u.share_lower_pct,age_suppressed_rows=o.age_suppressed_rows,unallocated_all_age_fills=o.suppressed_all_age_volume,ge65_SU=o.su_observed,lt65_SU=u.su_observed))
    st=save(pd.DataFrame(state2024).sort_values('gap_pp'),'A2_state_gaps_2024.csv')
    m=mod[(mod.model==2)&mod.term.eq('old_t')&mod.metric.eq('fills30')&mod.scenario.eq('primary')&mod['sample'].eq('observed_age_rows')].iloc[0]
    ref=[r['ols_pp_per_year'] for r in overall if r['family']=='long' and r['age']=='gap' and r['metric']=='fills30' and r['scenario']=='primary'][0]
    status='KILL' if abs(m.coefficient)<=1e-8 or np.sign(m.coefficient)!=np.sign(ref) else ('PASS' if m.ci_low*m.ci_high>0 else 'WEAK')
    decision=dict(status=status,model2_interaction_pp_per_year=m.coefficient,ci_low=m.ci_low,ci_high=m.ci_high,n_states=int(m.n_states),n_cells=int(m.n_cells),national_age_gap_slope_pp_per_year=ref,states_old_above_young=int(st.gap_pp.gt(0).sum()),states_robust_old_above_young=int(st.gap_lower_pp.gt(0).sum()),state_total=len(st),rule='User-prespecified direction + state-cluster 95% CI rule; numerical zero 1e-8 pp/year')
    (O/'A2_decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n')
    # A3 sums are drug-row beneficiary counts, not deduplicated individuals.
    a3=[]
    for family in ['glimepiride','glyburide','chlorpropamide','long']:
        z=b2024[mask(b2024,family)];a3.append(dict(year=2024,age='ge65',family=family,published_drug_rows=len(z),beneficiary_row_count_sum=z.GE65_Tot_Benes.sum(),beneficiary_suppressed_rows=int(z.GE65_Tot_Benes.isna().sum()),fills30_observed=z.GE65_Tot_30day_Fills.sum(),fills30_suppressed_rows=int(z.GE65_Tot_30day_Fills.isna().sum()),count_definition='sum of published generic-brand beneficiary counts; overlap possible within and across families',status='PUBLISHED_ROWS' if len(z) else 'NO_MATCHED_PUBLISHED_ROWS_NOT_PROOF_OF_ZERO'))
    save(a3,'A3_national_scale_2024.csv');save(b2024,'A3_national_drug_rows_2024.csv')
    return nat,sources

def provider_frame(d,age='all_age',exclude_er=False,complete=False):
    if exclude_er:d=d[~d.glipizide_er_xl].copy()
    if age=='all_age_GE65_visible_subset':
        visible=d.groupby('Prscrbr_NPI').GE65_Tot_30day_Fills.apply(lambda x:x.notna().any())
        d=d[d.Prscrbr_NPI.isin(visible[visible].index)]
    v='Tot_30day_Fills' if age.startswith('all_age') else 'GE65_Tot_30day_Fills'
    if complete:
        bad=d.groupby('Prscrbr_NPI')[v].apply(lambda x:x.isna().any());d=d[~d.Prscrbr_NPI.isin(bad[bad].index)]
    d=d[d[v].notna()].copy();d['long_vol']=d[v].where(d['class'].eq('long'),0)
    for k in ['Prscrbr_Type','Prscrbr_State_Abrvtn']:assert d.groupby('Prscrbr_NPI')[k].nunique().le(1).all()
    p=d.groupby('Prscrbr_NPI').agg(su=(v,'sum'),long=('long_vol','sum'),specialty=('Prscrbr_Type','first'),state=('Prscrbr_State_Abrvtn','first'))
    p=p[p.su>0].copy();p['share_pct']=100*p.long/p.su
    return p

def provider_analysis(nat):
    frames={};recovery=[];profiles=[];specialties=[];visibility=[];modelmeta=[];fix=[];ran=[];exclude=[];sources=[];supstats=[]
    for y in [2019,2023,2024]:
        print('A4 loading',y,flush=True);d=base.load('A',y);sources.append(PRE/f'data/A_{y}_su.csv.gz')
        vis=d.groupby('Prscrbr_NPI').GE65_Tot_30day_Fills.agg(any_visible=lambda x:x.notna().any(),visible_sum='sum',n_visible=lambda x:x.notna().sum(),n_rows='size')
        missing=d[d.GE65_Tot_30day_Fills.isna()].copy();missing['year']=y;save(missing,f'A4_suppressed_provider_drug_rows_{y}.csv.gz')
        supstats.append(dict(year=y,provider_drug_rows=len(d),suppressed_age_rows=len(missing),all_age_SU_fills=d.Tot_30day_Fills.sum(),age_visible_SU_fills=d.GE65_Tot_30day_Fills.sum()))
        for age,sc,ex,complete in [('all_age','primary',False,False),('all_age','exclude_ER_XL',True,False),('all_age_GE65_visible_subset','primary',False,False),('all_age_GE65_visible_subset','exclude_ER_XL',True,False),('ge65_visible','primary',False,False),('ge65_visible','exclude_ER_XL',True,False),('ge65_visible','complete_published_SU_rows',False,True)]:
            p=provider_frame(d,age,ex,complete);frames[(y,age,sc)]=p
            if y not in [2019,2024]:continue
            nn=nat[nat.year.eq(y)&nat.family.eq('long')&nat.metric.eq('fills30')&nat.scenario.eq('exclude_ER_XL' if ex else 'primary')].set_index('age')
            if age.startswith('all_age'):bS=nn.loc['ge65','all_age_su'];bL=nn.target_observed.sum()+nn.loc['ge65','suppressed_target_volume'];bShi=bS;bLhi=bL
            else:bS=nn.loc['ge65','su_lower'];bL=nn.loc['ge65','target_lower'];bShi=nn.loc['ge65','su_upper'];bLhi=nn.loc['ge65','target_upper']
            rec=dict(year=y,age=age,scenario=sc,n_prescribers=len(p),A_SU=p.su.sum(),B_SU_lower=bS,B_SU_upper=bShi,SU_recovery_lower_pct=100*p.su.sum()/bShi,SU_recovery_upper_pct=100*p.su.sum()/bS,A_long=p.long.sum(),B_long_lower=bL,B_long_upper=bLhi,long_recovery_lower_pct=100*p.long.sum()/bLhi,long_recovery_upper_pct=100*p.long.sum()/bL)
            recovery.append(rec)
            pr=base.profile(p,y,'fills30',sc);pr.update(age=age,SU_coverage_pct=rec['SU_recovery_lower_pct']);profiles.append(pr)
            sp=p.groupby('specialty').agg(n_prescribers=('su','size'),su_volume=('su','sum'),long_volume=('long','sum')).sort_values('su_volume',ascending=False).reset_index();sp['rank_by_SU']=np.arange(1,len(sp)+1);sp['share_pct']=100*sp.long_volume/sp.su_volume;sp['is_endocrinology']=sp.specialty.str.contains('Endocrin',case=False);sp['display_top10_or_endocrine']=sp.rank_by_SU.le(10)|sp.is_endocrinology;sp['year']=y;sp['age']=age;sp['scenario']=sc;sp['SU_coverage_pct']=rec['SU_recovery_lower_pct'];specialties.append(sp)
            out=p.reset_index();out['year']=y;out['age']=age;out['scenario']=sc;save(out,f'A4_providers_{y}_{age}_{sc}.csv.gz')
            if sc=='primary':
                non=p[~p.state.isin(base.STATES)]
                for state,g in non.groupby('state'):exclude.append(dict(year=y,age=age,state=state,n_prescribers=len(g),SU_volume=g.su.sum(),long_volume=g.long.sum(),reason='Non-50-state unit excluded only from random-intercept model'))
                pp=p[p.state.isin(base.STATES)]
                for c in [.5,.1,1.]:
                    meta,fx,rx=weighted_logit_reml(pp,c);meta.update(year=y,age=age,SU_coverage_pct=rec['SU_recovery_lower_pct'],model_50_state_SU_volume=pp.su.sum(),model_SU_recovery_pct=100*pp.su.sum()/bShi);modelmeta.append(meta)
                    if c==.5:
                        fx['year']=y;fx['age']=age;fix.append(fx);rx['year']=y;rx['age']=age;ran.append(rx)
                print('A4 mixed complete',y,age,flush=True)
        if y in [2019,2024]:
            p=frames[(y,'all_age','primary')].join(vis)
            p['visibility_group']=np.where(p.any_visible,'at_least_one_GE65_value','no_GE65_values')
            for group,g in p.groupby('visibility_group'):
                r=dict(year=y,visibility_group=group,n_prescribers=len(g),all_age_SU_sum=g.su.sum(),all_age_SU_mean=g.su.mean(),visible_but_zero_n=int((g.any_visible&g.visible_sum.eq(0)).sum()))
                for q in [.01,.1,.25,.5,.75,.9,.99]:r[f'p{int(q*100)}_all_age_SU']=g.su.quantile(q)
                visibility.append(r)
            save(p.reset_index(),f'A4_visibility_NPI_{y}.csv.gz')
    cors=[]
    for first,last in [(2019,2024),(2023,2024)]:
        for age in ['all_age','all_age_GE65_visible_subset','ge65_visible']:
            for sc in ['primary','exclude_ER_XL']+(['complete_published_SU_rows'] if age=='ge65_visible' else []):
                a=frames[(first,age,sc)];b=frames[(last,age,sc)];j=a[['share_pct']].join(b[['share_pct']],lsuffix='_previous',rsuffix='_current',how='inner');rho=spearmanr(j.share_pct_previous,j.share_pct_current).statistic
                cors.append(dict(year_previous=first,year_current=last,age=age,scenario=sc,matched_npi=len(j),spearman_rho=rho))
    save(recovery,'A4_recovery.csv');save(profiles,'A4_profiles.csv');save(pd.concat(specialties),'A4_specialties.csv');save(visibility,'A4_visibility_distributions.csv');save(cors,'A4_correlations.csv');save(modelmeta,'A4_state_ICC.csv');save(pd.concat(fix),'A4_mixed_fixed_effects.csv');save(pd.concat(ran),'A4_state_random_intercepts.csv');save(exclude,'A4_model_excluded_units.csv');save(supstats,'A4_suppression_summary.csv')
    return sources

if __name__=='__main__':
    nat,sources=national_and_panel();print('A1–A3 tables and A2 decision complete',flush=True)
    sources+=provider_analysis(nat)
    sources += [PRE/'code/analyze.py',PRE/'field_mapping.csv',PRE/'matched_generic_names.csv',PRE/'matched_generic_brand_names.csv',PRE/'evidence/source_manifest.json']
    manifest=[dict(path=str(p.relative_to(PRE)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sources]
    (O/'evidence/reused_input_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    import scipy,matplotlib,statsmodels
    (O/'evidence/runtime.json').write_text(json.dumps(dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,statsmodels=statsmodels.__version__),indent=2)+'\n')
    print('All analysis tables complete',flush=True)
