"""Independent stdlib/Decimal reconciliation of extracts and output tables."""
from pathlib import Path
import csv,gzip,json,hashlib,re,math
from decimal import Decimal as D
from collections import defaultdict
O=Path(__file__).resolve().parents[1]
def rows(p):
 with p.open() as f:return list(csv.DictReader(f))
def close(a,b,tol='0.01'):
 assert abs(D(str(a))-D(str(b)))<=D(tol),(a,b)
def dec(s):return D(s) if s else None
nat={int(x['year']):x for x in rows(O/'national_annual_primary.csv')}
qa={(x['source'],int(x['year']),x['level']):x for x in rows(O/'K0_row_QA.csv')}
rec={(int(x['year']),x['class']):x for x in rows(O/'K0_recovery.csv')}
prof={(int(x['year']),x['metric'],x['scenario']):x for x in rows(O/'K3_provider_profiles.csv')}
report={'status':'PASS','method':'Independent standard-library CSV + Decimal sums; no pandas analysis functions imported','year_checks':[]}
for y in range(2013,2025):
 sums={};details={}
 for source in 'AB':
  path=O/f'data/{source}_{y}_su.csv.gz';ev=json.loads((O/f'evidence/{source}_{y}_completeness.json').read_text())
  assert hashlib.sha256(path.read_bytes()).hexdigest()==ev['data_sha256']
  count=0;missing=0;neg=0;total=D(0);old=D(0);long=D(0);young=D(0);younglong=D(0);u=D(0);ul=D(0);providers=defaultdict(lambda:[D(0),D(0)])
  with gzip.open(path,'rt') as f:
   for row in csv.DictReader(f):
    count+=1
    if source=='B' and row['Prscrbr_Geo_Lvl']!='National':continue
    t=dec(row['Tot_30day_Fills']);o=dec(row['GE65_Tot_30day_Fills']);islong=bool(re.search(r'glimepiride|glyburide|chlorpropamide',row['Gnrc_Name'],re.I));total+=t
    if o is None:missing+=1;u+=t;ul+=t if islong else D(0);continue
    assert not row['GE65_Sprsn_Flag']
    neg+=int(t-o<0);old+=o;young+=t-o
    if islong:long+=o;younglong+=t-o
    if source=='A' and y in [2015,2024]:
     providers[row['Prscrbr_NPI']][0]+=o;providers[row['Prscrbr_NPI']][1]+=o if islong else D(0)
  assert count==ev['api_filtered_rows']==ev['downloaded_rows']==ev['unique_keys']
  q=qa[(source,y,'provider_drug' if source=='A' else 'National')]
  assert missing==int(q['age65_missing_fills_rows']);assert neg==0
  sums[source]=(total,old,long);details[source]={'rows':count,'missing_ge65_fills':missing,'negative_lt65_fills':neg}
  if source=='B':
   n=nat[y]
   for name,val in [('all_age_su',total),('ge65_su_observed',old),('ge65_long_observed',long),('lt65_su_observed',young),('lt65_long_observed',younglong),('ge65_su_upper',old+u),('ge65_long_upper',long+ul)]:close(n[name],val)
   close(n['ge65_share_observed_pct'],100*long/old,'0.0000001')
   close(n['lt65_share_observed_pct'],100*younglong/young,'0.0000001')
   assert bool(n['ge65_su_exact'])==(missing==0)
   valid=json.loads((O/f'evidence/B_{y}_CSV_API_validation.json').read_text());assert valid['value_mismatches']==0;assert valid['regex_matched_rows']==count
  if providers:
   pp=[v for v in providers.values() if v[0]>0];pr=prof[(y,'fills30','observed')]
   assert len(pp)==int(pr['n_prescribers']);close(pr['long_volume'],long);close(pr['su_volume'],old)
   sv=sorted((v[1] for v in pp),reverse=True)
   for pct in [1,10]:
    k=math.ceil(len(pp)*pct/100);close(pr[f'top{pct}_pct_of_recovered_long'],100*sum(sv[:k])/long,'0.0000001')
 for idx in range(3):assert sums['A'][idx]<=sums['B'][idx]+D('0.01'),(y,idx,sums)
 close(rec[(y,'all')]['a_recovered_ge65_fills30'],sums['A'][1])
 close(rec[(y,'all')]['recovery_upper_pct'],100*sums['A'][1]/sums['B'][1],'0.0000001')
 report['year_checks'].append({'year':y,**details})
 print('QA',y,flush=True)
assert len(rows(O/'national_annual.csv'))==48
assert len(rows(O/'K3_adjacent_year_spearman.csv'))==44
assert len(rows(O/'K4_screening_ledger.csv'))==205
k4=json.loads((O/'K4_final_decision.json').read_text())
assert len(rows(O/'K4_key_studies.csv'))==k4['key_studies']==18
assert len(rows(O/'K4_Scholar_screening_ledger.csv'))==k4['scholar_records']==1440
assert k4['scholar_queries_completed']==3 and k4['exact_kill_studies']==0
assert all(float(x['spearman_rho'])>=-1 and float(x['spearman_rho'])<=1 for x in rows(O/'K3_adjacent_year_spearman.csv'))
manifest=json.loads((O/'evidence/source_manifest.json').read_text());assert len(manifest)==24
assert all(x['fields']==x['api_fields'] for x in manifest)
report.update({'verified_source_versions':24,'B_full_CSV_API_validations':12,'B_value_mismatches':0,'national_primary_rows':12,'national_sensitivity_rows':48,'adjacent_year_pairs':11,'pubmed_unique_records':205,'K4_status':k4['status'],'K4_review_date':k4['review_date'],'scholar_records':k4['scholar_records'],'limitations':'QA checks engineering and arithmetic consistency only; not scientific validation or correction of suppression bias.'})
(O/'QA_validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
with (O/'SHA256SUMS').open('w') as f:
 for p in sorted(O.rglob('*')):
  if p.is_file() and p.name!='SHA256SUMS' and '__pycache__' not in p.parts and not p.name.endswith('.part'):f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(O))+'\n')
print('All independent QA checks passed; SHA256SUMS written.')
