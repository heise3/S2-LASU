"""Independent numerical and provenance validation; no network calls."""
from pathlib import Path
import json,hashlib,sys
import numpy as np,pandas as pd
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster
from models import fe_fit,weighted_logit_reml
O=Path(__file__).resolve().parents[1];PRE=O.parent;T=O/'tables';checks=[]
def check(name,condition,detail=''):
    checks.append(dict(check=name,passed=bool(condition),detail=str(detail)))
    print(name, bool(condition), detail,flush=True)
    assert condition,name
manifest=json.load(open(O/'evidence/reused_input_manifest.json'))
check('Reused input hashes',all(hashlib.sha256((PRE/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest),len(manifest))
# Prior precheck deliverables must remain byte-identical.
old=[]
for line in (PRE/'SHA256SUMS').read_text().splitlines():
    sha,path=line.split(maxsplit=1);p=PRE/path.lstrip('*')
    old.append(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==sha)
check('Prior precheck SHA256 preservation',all(old),len(old))
d=pd.read_csv(T/'A2_state_age_panel.csv')
check('50 states x 12 years x 2 age cells',len(d)==1200 and d.state.nunique()==50 and not d.duplicated(['state','year','age']).any())
check('Age shares within suppression bounds',((d.share_pct>=d.share_lower_pct-1e-8)&(d.share_pct<=d.share_upper_pct+1e-8)).all())
check('Positive observed state age SU and bounded long volume',(d.su_observed>0).all() and (d.target_observed>=0).all() and (d.target_observed<=d.su_observed).all())
# Independent full dummy-matrix WLS + statsmodels cluster sandwich, versus absorbed implementation.
for model in [1,2]:
    dd=d.copy();dd['t']=dd.year-2013;dd['old_t']=dd.old*dd.t
    cols=['old','t','old_t'] if model==1 else ['old','old_t']
    group=dd.state if model==1 else dd.state+'_'+dd.year.astype(str)
    X=pd.concat([dd[cols],pd.get_dummies(group,prefix='FE',dtype=float)],axis=1)
    fit=sm.WLS(dd.share_pct,X,weights=dd.su_observed).fit()
    cv=cov_cluster(fit,dd.state,use_correction=True)
    rr,ours=fe_fit(dd,model)
    diff=float(np.max(np.abs(fit.params[cols].values-ours['beta'])))
    sediff=float(np.max(np.abs(np.sqrt(np.diag(cv)[:len(cols)])-np.sqrt(np.diag(ours['cov'])))))
    check(f'M{model} absorbed coefficients vs full WLS',diff<1e-8,diff)
    check(f'M{model} clustered SE vs statsmodels',sediff<1e-8,sediff)
# Independent random-effects likelihood implementation on a deterministic weighted fixture.
rng=np.random.default_rng(20261027);G=16;n=1600
state=np.repeat(np.arange(G),n//G);cat=rng.integers(0,3,n)
S=rng.uniform(30,500,n);weight=S/S.mean()
z=np.array([-.5,.2,.6])[cat]+rng.normal(0,.8,G)[state]+rng.normal(size=n)*.8/np.sqrt(weight)
L=(S+1)/(1+np.exp(-z))-.5
valid=(L>=0)&(L<=S)
p=pd.DataFrame(dict(su=S[valid],long=L[valid],specialty=cat[valid].astype(str),state=state[valid].astype(str)))
m,_,_=weighted_logit_reml(p)
z=np.log((p.long+.5)/(p.su-p.long+.5)).values;sw=np.sqrt(p.su/p.su.mean()).values
X=pd.get_dummies(p.specialty,dtype=float).values
ind=sm.MixedLM(z*sw,X*sw[:,None],groups=p.state,exog_re=sw[:,None]).fit(reml=True,method='lbfgs',disp=False)
check('Independent MixedLM converged',ind.converged)
check('Weighted REML state variance vs statsmodels',abs(m['tau2_state']-float(ind.cov_re[0,0]))<2e-4,{'ours':m['tau2_state'],'independent':float(ind.cov_re[0,0])})
check('Weighted REML residual variance vs statsmodels',abs(m['sigma2_at_mean_volume']-ind.scale)<2e-4,{'ours':m['sigma2_at_mean_volume'],'independent':ind.scale})
mix=pd.read_csv(T/'A4_state_ICC.csv')
check('All production mixed models converged',mix.optimizer_success.all() and np.isfinite(mix.ICC_mean_volume).all() and mix.ICC_mean_volume.between(0,1).all(),len(mix))
sys.path.insert(0,str(PRE/'code'));import analyze as base
negative=0;missing=0
for y in range(2013,2025):
    b=base.load('B',y);negative+=int((b.LT65_Tot_30day_Fills<0).sum());missing+=int(b.LT65_Tot_30day_Fills.isna().sum())
check('B all years LT65 no negative fills',negative==0,{'negative':negative,'missing_preserved':missing})
for y in [2019,2023,2024]:
    a=base.load('A',y)
    check(f'A {y} LT65 no negative fills',not (a.LT65_Tot_30day_Fills<0).any(),{'missing_preserved':int(a.LT65_Tot_30day_Fills.isna().sum())})
    check(f'A {y} specialty/state present',a.Prscrbr_Type.notna().all() and a.Prscrbr_State_Abrvtn.notna().all())
for y in [2019,2024]:
    p=pd.read_csv(T/f'A4_providers_{y}_all_age_primary.csv.gz')
    r=pd.read_csv(T/'A4_profiles.csv');r=r[(r.year==y)&(r.age=='all_age')&(r.scenario=='primary')].iloc[0]
    check(f'A4 {y} profile count and volume',len(p)==r.n_prescribers and np.isclose(p.long.sum(),r.long_volume))
    for pct in [1,10]:
        ntop=int(np.ceil(len(p)*pct/100));c=100*p.long.nlargest(ntop).sum()/p.long.sum()
        check(f'A4 {y} top {pct}% concentration',abs(c-r[f'top{pct}_pct_of_recovered_long'])<1e-8)
e=json.load(open(O/'evidence/enrollment_denominator.json'))
check('Enrollment source workbook unchanged',hashlib.sha256((O/'evidence/MDCR ENROLL D_CPS_03EPD_2024.xlsx').read_bytes()).hexdigest()==e['sha256'])
scale=pd.read_csv(T/'A3_scale_with_enrollment_2024.csv');scale=scale[scale.published_drug_rows.gt(0)]
check('A3 rate arithmetic',np.allclose(scale.beneficiary_row_counts_per_1000_enrollee_person_years,1000*scale.beneficiary_row_count_sum/e['denominator']))
from pypdf import PdfReader
for pdf in sorted((O/'figures').glob('*.pdf')):
    r=PdfReader(pdf)
    check(pdf.name+' is one-page vector PDF',len(r.pages)==1 and len(list(r.pages[0].images))==0 and bool(r.pages[0].get('/Resources').get('/Font')))
(O/'evidence/validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print('ALL VALIDATIONS PASSED',flush=True)
