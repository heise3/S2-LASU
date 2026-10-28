"""Independent numerical and provenance checks for the frozen precheck bundle."""
from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
import numpy as np,pandas as pd,statsmodels.api as sm,openpyxl
from statsmodels.stats.sandwich_covariance import cov_cluster
from scipy.stats import t
O=Path(__file__).resolve().parents[1];E=O/'evidence';T=O/'tables/drug_filtered'
c=pd.read_csv(T/'K2_entry_results.csv');p=pd.read_csv(T/'K2_primary_model_panel.csv.gz');checks=[]
for entry,z in p.groupby('entry'):
 w=z.pivot(index=['state','year'],columns='old',values='share_pct').reset_index();X=sm.add_constant(w.year-2013);fit=sm.OLS(w[1]-w[0],X).fit();V=cov_cluster(fit,w.state,use_correction=False);r=c[c.entry.eq(entry)].iloc[0]
 # Paired differences have the same uncorrected sandwich as the full FE model.
 # Retain the prespecified full state-year FE CR1 degrees-of-freedom correction.
 se=np.sqrt(V[1,1]*r.CR1_factor);crit=t.ppf(.975,r.n_states-1)
 assert np.isclose(fit.params.iloc[1],r.coefficient,atol=1e-10)
 assert np.isclose(se,r.se,atol=1e-10)
 assert np.isclose(r.coefficient-crit*se,r.ci_low,atol=1e-10)
 checks.append(dict(entry=entry,beta_abs_error=abs(fit.params.iloc[1]-r.coefficient),se_abs_error=abs(se-r.se)))
pd.DataFrame(checks).to_csv(T/'independent_model_checks.csv',index=False)
d=pd.read_csv(O/'tables/enrollment_denominators.csv');bookcache={}
for _,r in d.iterrows():
 src=Path(r.workbook);f=E/'enrollment_source_files'/src.parent.name/src.name
 assert hashlib.sha256(f.read_bytes()).hexdigest()==r.sha256_workbook
 if f not in bookcache:bookcache[f]=openpyxl.load_workbook(f,read_only=True,data_only=True)
 v=bookcache[f][r.sheet][r.cell].value
 assert float(v)==r.enrollee_person_years,(r.year,r.age,v)
main=c[c.role.eq('Table2_entry')];assert len(main)==33 and int(main.ci_high.lt(0).sum())==19
k1=pd.read_csv(T/'K1_feasibility.csv');assert ((k1.ge65_suppressed_rows_pct.dropna()>=0)&(k1.ge65_suppressed_rows_pct.dropna()<=100)).all()
before=json.loads((E/'prior_outputs_manifest.json').read_text());changed=[]
for r in before:
 f=O.parent/r['path']
 if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=r['sha256']:changed.append(r['path'])
assert not changed,changed
q=json.loads((E/'validation.json').read_text());q.update(independent_statsmodels_paired_beta_SE_CI_checks=len(checks),official_denominator_cells_verified=len(d),prior_files_changed=changed,prior_files_checked=len(before),forest_visual_inspection='All labels, intervals, benchmark and footnotes visible; PDF vector output')
(E/'validation.json').write_text(json.dumps(q,indent=2));print(json.dumps(q,indent=2))
