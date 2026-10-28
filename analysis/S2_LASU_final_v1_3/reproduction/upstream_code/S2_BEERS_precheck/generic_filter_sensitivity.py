"""Stricter drug-level application of the 100,000 threshold within each criterion.
Main criterion-level model and its denominators remain separately available.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import pandas as pd,numpy as np
from definitions import STATE_CODES
from lasu_models import fe_fit
O=Path(__file__).resolve().parents[1];T=O/'tables';v=pd.read_csv(T/'generic_volume_audit.csv');low=set(v.loc[v.low_volume,'Gnrc_Name']);d=pd.read_csv(T/'matched_published_rows.csv.gz',dtype={'Prscrbr_Geo_Cd':str});ex=d[d.Gnrc_Name.isin(low)];ex.to_csv(T/'excluded_low_volume_generic_rows.csv.gz',index=False,compression='gzip');v[v.low_volume].to_csv(T/'excluded_low_volume_generics.csv',index=False)
d=d[~d.Gnrc_Name.isin(low)].copy();d['state']=d.Prscrbr_Geo_Cd.str.zfill(2).map(STATE_CODES);d=d[d.Prscrbr_Geo_Lvl.eq('State')&d.state.notna()]
cat=pd.read_csv(T/'drug_criteria_manifest.csv');den=pd.read_csv(T/'enrollment_denominators.csv').set_index(['year','age']).enrollee_person_years
rows=[];pp=[]
for ent in cat.loc[cat.status.eq('INCLUDED'),'entry']:
 z=d[d.entry.eq(ent)];r=[]
 for (st,y),g in z.groupby(['state','year']):
  a=g.GE65_Tot_30day_Fills.sum(min_count=1);b=(g.Tot_30day_Fills-g.GE65_Tot_30day_Fills).sum(min_count=1)
  if not(np.isfinite(a) and np.isfinite(b) and a>0 and b>0):continue
  for age,F in [('ge65',a),('lt65',b)]:r.append(dict(entry=ent,state=st,year=y,old=int(age=='ge65'),su_observed=1,share_pct=np.log(F*1000/den.loc[(y,age)])))
 q=pd.DataFrame(r);rr,_=fe_fit(q,2);rows.extend(x|dict(entry=ent,scenario='exclude_generic_lt100000') for x in rr);pp.append(q)
x=pd.DataFrame(rows);x.to_csv(T/'K2_low_volume_generic_filtered.csv',index=False);pd.concat(pp).to_csv(T/'K2_low_volume_filtered_panel.csv.gz',index=False,compression='gzip');a=x[x.term.eq('old_t')&x.entry.ne('long_su')];print(len(a),(a.ci_high<0).sum(),(a.ci_low>0).sum())
