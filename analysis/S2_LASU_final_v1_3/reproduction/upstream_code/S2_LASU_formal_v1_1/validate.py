"""Independent paired-gap regression check, denominator and preservation audit."""
from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
import numpy as np,pandas as pd,statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster
from scipy.stats import t
O=Path(__file__).resolve().parents[1];V=O.parent/'S2_LASU_formal_v1';T=O/'tables';E=O/'evidence';checks=[]
def check(name,condition,detail=''):
    checks.append(dict(check=name,passed=bool(condition),detail=detail));print(name,bool(condition),detail,flush=True);assert condition,name
before=json.load(open(E/'v1_before_manifest.json'));now={str(p.relative_to(V)):hashlib.sha256(p.read_bytes()).hexdigest() for p in V.rglob('*') if p.is_file()}
check('v1 directory file set and bytes unchanged',now=={x['path']:x['sha256'] for x in before},len(now))
for original,copy in [('run_analysis.py','v1_analysis.py'),('models.py','models.py')]:check('Exact v1 code reuse '+original,(V/'code'/original).read_bytes()==(O/'code'/copy).read_bytes())
den=pd.read_csv(T/'R1_enrollment_denominators.csv');check('All 24 age-year denominators',len(den)==24 and not den.duplicated(['year','age']).any() and den.enrollee_person_years.gt(0).all())
qa=pd.read_csv(T/'R1_enrollment_rounding_audit.csv');check('Age denominators add to total within rounding',qa.rounding_difference.abs().le(1).all(),qa.rounding_difference.tolist())
check('2024 old denominator equals v1',float(den[(den.year==2024)&(den.age=='ge65')].enrollee_person_years.iloc[0])==json.load(open(V/'evidence/enrollment_denominator.json'))['denominator'])
rates=pd.read_csv(T/'R1_rates_long.csv');check('120 rate cells and arithmetic',len(rates)==120 and np.allclose(rates.rate_observed_per1000py,1000*rates.fills30_observed/rates.enrollee_person_years))
check('Rule-based rate bounds ordered',(rates.rate_rule_lower_per1000py<=rates.rate_rule_upper_per1000py+1e-8).all())
v1=pd.read_csv(V/'tables/A1_national_annual.csv');v1=v1[v1.metric.eq('fills30')&v1.scenario.eq('primary')&v1.family.eq('long')].set_index('year')
for age in ['ge65','lt65']:
    for fam,col in [('SU',age+'_SU'),('long',age+'_target')]:
        z=rates[rates.age.eq(age)&rates.family.eq(fam)].set_index('year');check(f'R1 visible numerator matches v1 {age} {fam}',np.allclose(z.fills30_observed,v1[col]))
alloc=pd.read_csv(T/'R2_imputed_drug_rows.csv');check('R2 age conservation',np.allclose(alloc.old_imputed+alloc.young_imputed,alloc.Tot_30day_Fills))
check('R2 allocation within derived volume bounds',((alloc.old_imputed>=alloc.old_lower-1e-8)&(alloc.old_imputed<=alloc.old_upper+1e-8)&(alloc.young_imputed>=0)).all())
small=np.where(alloc.primary_small_age.eq('ge65'),alloc.old_imputed,alloc.young_imputed)
check('Small-age imputed fills bounded by claims-based envelope',((small>=-1e-8)&(small<=alloc.small_fills_upper+1e-8)&(small<=120+1e-8)).all())
check('R2 uses original flags separately',set(alloc.GE65_Sprsn_Flag)=={'*','#'},alloc.groupby('GE65_Sprsn_Flag').size().to_dict())
pan=pd.read_csv(T/'R2_endpoint_panels.csv');coef=pd.read_csv(T/'R2_model2_coefficients.csv');ind=[]
def paired(d,label,row):
    x=d.pivot(index=['state','year'],columns='old',values=['share_pct','su_observed'])
    gap=x['share_pct'][1]-x['share_pct'][0];w=x['su_observed'][1]*x['su_observed'][0]/(x['su_observed'][1]+x['su_observed'][0])
    time=x.index.get_level_values('year').to_numpy()-2013;X=sm.add_constant(time)
    fit=sm.WLS(gap,X,weights=w).fit();g=x.index.get_level_values('state');G=len(set(g));n=len(x)
    cv=cov_cluster(fit,g,use_correction=False)*G/(G-1)*(2*n-1)/(n-2)
    se=np.sqrt(cv[1,1]);b=float(fit.params.iloc[1]);lo=b-t.ppf(.975,G-1)*se;hi=b+t.ppf(.975,G-1)*se
    ind.append(dict(scenario=label,independent_coefficient=b,independent_se=se,independent_ci_low=lo,independent_ci_high=hi,beta_abs_error=abs(b-row.coefficient),se_abs_error=abs(se-row.se),n_state_years=n,n_states=G))
for scenario,d in pan.groupby('scenario'):
    check('R2 panel completeness '+scenario,len(d)==1200 and not d.duplicated(['state','year','age']).any())
    row=coef[coef.scenario.eq(scenario)&coef.term.eq('old_t')].iloc[0];paired(d,scenario,row)
complete=pd.read_csv(T/'R2_complete_state_year_age_panel.csv');check('Complete subset 103 state-years in 41 states',len(complete)==206 and complete.state.nunique()==41)
paired(complete,'complete_subset',coef[coef.scenario.eq('complete_published_state_years')&coef.term.eq('old_t')].iloc[0])
p3=pd.read_csv(T/'R3_state_age_panels.csv');c3=pd.read_csv(T/'R3_model2_coefficients.csv')
for definition,d in p3.groupby('definition'):paired(d,definition,c3[c3.definition.eq(definition)&c3.term.eq('old_t')].iloc[0])
ind=pd.DataFrame(ind);ind.to_csv(T/'independent_paired_model_checks.csv',index=False,float_format='%.12g')
check('All 10 model fits vs independent paired-age WLS',(ind.beta_abs_error<1e-8).all() and (ind.se_abs_error<1e-8).all(),{'max_beta_error':ind.beta_abs_error.max(),'max_se_error':ind.se_abs_error.max()})
n3=pd.read_csv(T/'R3_national_annual.csv');b=n3[n3.definition.eq('v1_primary')].set_index('year');er=n3[n3.definition.eq('ER_XL_as_long')].set_index('year')
check('R3 baseline reproduces v1',np.allclose(b.gap_pp,v1.gap_pp))
check('ER reclassification preserves SU denominator',np.allclose(b[['ge65_SU','lt65_SU']],er[['ge65_SU','lt65_SU']]))
defs=pd.read_csv(T/'drug_definition_audit.csv');com=set(defs[defs.is_combination].Gnrc_Name)
check('Actual combination generic names verified',com=={'Glipizide/Metformin Hcl','Glyburide/Metformin Hcl','Pioglitazone Hcl/Glimepiride','Rosiglitazone/Glimepiride'},sorted(com))
Y=v1.sort_index();year=Y.index.to_numpy();X=np.column_stack([np.ones(12),year-2013,*[np.maximum(year-k,0) for k in [2015,2019,2023]]]);sl=pd.read_csv(T/'R4_segment_slopes.csv').sort_values('start')
for age,col in [('ge65','ge65_share_pct'),('lt65','lt65_share_pct'),('gap','gap_pp')]:
    beta=np.linalg.lstsq(X,Y[col],rcond=None)[0];expected=np.array([beta[1]+beta[2:2+i].sum() for i in range(4)]);check('R4 independent spline '+age,np.allclose(expected,sl[age],atol=1e-8))
union=pd.read_csv(T/'R5_beneficiary_union_bounds.csv');check('Published beneficiary union bounds ordered',(union.published_union_lower<=union.published_union_upper).all())
rr=pd.read_csv(T/'R5_long_drug_beneficiary_rows.csv');r=union[union.family.eq('long')].iloc[0]
check('R5 long max/sum verified',r.published_union_lower==rr.GE65_Tot_Benes.max() and r.published_union_upper==rr.GE65_Tot_Benes.sum())
main=coef[coef.role.eq('primary_four')&coef.term.eq('old_t')];status='FRAGILE' if (main.coefficient<=1e-8).any() else ('ROBUST' if main.ci_low.gt(0).all() else 'DIRECTIONAL')
check('R2 decision matches prespecified four-scenario rule',status==json.load(open(O/'R2_decision.json'))['status'],status)
(E/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print('ALL CHECKS PASSED',len(checks))
