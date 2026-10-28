"""S2-LASU K0–K3. pandas/numpy only. Missing age cells remain missing.
National intervals allow each suppressed age volume in [0, all-age volume].
Intervals cover published national rows only; never recover suppressed individuals.
"""
from pathlib import Path
import json,re,math,hashlib,sys
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs';DATA=OUT/'data'
LONG=r'glimepiride|glyburide|chlorpropamide';SHORT=r'glipizide'
OTHER=r'tolbutamide|tolazamide|gliclazide|gliquidone|glibenclamide|acetohexamide|glibornuride|glisoxepide|glyclopyramide'
ER=r'(?<![A-Za-z])(?:ER|XL|XR)(?![A-Za-z])|extended[ -]?release'
NUM=['Tot_Clms','Tot_30day_Fills','Tot_Benes','GE65_Tot_Clms','GE65_Tot_30day_Fills','GE65_Tot_Benes']
STATES=set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())
METRICS={'fills30':'30day_Fills','claims':'Clms'}
def load(s,y):
 d=pd.read_csv(DATA/f'{s}_{y}_su.csv.gz',dtype=str,keep_default_na=False)
 for k in NUM:d[k]=pd.to_numeric(d[k],errors='coerce')
 d['class']=np.select([d.Gnrc_Name.str.contains(LONG,case=False,regex=True),d.Gnrc_Name.str.contains(SHORT,case=False,regex=True),d.Gnrc_Name.str.contains(OTHER,case=False,regex=True)],['long','short','other'],default='UNMATCHED')
 assert not (d['class']=='UNMATCHED').any()
 d['glipizide_er_xl']=d['class'].eq('short')&d.Brnd_Name.str.contains(ER,case=False,regex=True)
 for suffix in ['Clms','30day_Fills','Benes']:d['LT65_Tot_'+suffix]=d['Tot_'+suffix]-d['GE65_Tot_'+suffix]
 return d

def national(d,y,metric='fills30',exclude_er=False):
 if exclude_er:d=d[~d.glipizide_er_xl].copy()
 suf=METRICS[metric];total=d['Tot_'+suf];old=d['GE65_Tot_'+suf];miss=old.isna();long=d['class'].eq('long')
 assert total.notna().all()
 r={'year':y,'metric':metric,'sensitivity':'exclude_glipizide_ER_XL' if exclude_er else 'primary','n_rows':len(d),'age_suppressed_rows':int(miss.sum()),'all_age_su':total.sum(),'all_age_long':total[long].sum(),'suppressed_all_age_volume':total[miss].sum(),'suppressed_long_all_age_volume':total[miss&long].sum(),'node':str(y) if y in [2015,2019,2023] else ''}
 # Conservative per-age bounds: suppression allocations independently relaxed.
 for age,v in [('ge65',old),('lt65',total-old)]:
  S=v.sum(min_count=1);L=v[long].sum(min_count=1);uL=total[miss&long].sum();uN=total[miss&~long].sum()
  r.update({f'{age}_su_observed':S,f'{age}_long_observed':L,f'{age}_su_lower':S,f'{age}_su_upper':S+uL+uN,f'{age}_long_lower':L,f'{age}_long_upper':L+uL,f'{age}_share_observed_pct':100*L/S,f'{age}_share_lower_pct':100*L/(S+uN),f'{age}_share_upper_pct':100*(L+uL)/(S+uL),f'{age}_su_exact':S if not miss.any() else np.nan,f'{age}_long_exact':L if not miss.any() else np.nan,f'{age}_share_exact_pct':100*L/S if not miss.any() else np.nan})
 r['age_gap_observed_pp']=r['ge65_share_observed_pct']-r['lt65_share_observed_pct']
 r['age_gap_lower_pp']=r['ge65_share_lower_pct']-r['lt65_share_upper_pct'];r['age_gap_upper_pp']=r['ge65_share_upper_pct']-r['lt65_share_lower_pct']
 return r

def qa_rows(d,s,y,level):
 r={'source':s,'year':y,'level':level,'su_rows':len(d),'age65_flagged_rows':int(d.GE65_Sprsn_Flag.ne('').sum()),'age65_flagged_pct':100*d.GE65_Sprsn_Flag.ne('').mean(),'age65_missing_fills_rows':int(d.GE65_Tot_30day_Fills.isna().sum()),'age65_flag_star':int(d.GE65_Sprsn_Flag.eq('*').sum()),'age65_flag_hash':int(d.GE65_Sprsn_Flag.eq('#').sum()),'age65_flag_other':int((~d.GE65_Sprsn_Flag.isin(['','*','#'])).sum())}
 if s=='A':
  known=d[d.GE65_Tot_30day_Fills.notna()].groupby('Prscrbr_NPI').GE65_Tot_30day_Fills.sum()
  r['npi_any_ge65_fills_data']=len(known);r['npi_positive_ge65_fills']=int(known.gt(0).sum());r['npi_known_but_zero_ge65_fills']=int(known.eq(0).sum())
 for suf in ['Clms','30day_Fills','Benes']:
  r['lt65_missing_'+suf]=int(d['LT65_Tot_'+suf].isna().sum());r['lt65_negative_'+suf]=int(d['LT65_Tot_'+suf].lt(-1e-7).sum())
 return r

def providers(d,metric='fills30',exclude_er=False,complete=False):
 if exclude_er:d=d[~d.glipizide_er_xl].copy()
 v='GE65_Tot_'+METRICS[metric]
 if complete:
  bad=set(d.loc[d[v].isna(),'Prscrbr_NPI']);d=d[~d.Prscrbr_NPI.isin(bad)].copy()
 assert d.groupby('Prscrbr_NPI').Prscrbr_Type.nunique().le(1).all()
 assert d.groupby('Prscrbr_NPI').Prscrbr_State_Abrvtn.nunique().le(1).all()
 d=d[d[v].notna()].copy();d['long_volume']=d[v].where(d['class'].eq('long'),0)
 p=d.groupby('Prscrbr_NPI').agg(su=(v,'sum'),long=('long_volume','sum'),specialty=('Prscrbr_Type','first'),state=('Prscrbr_State_Abrvtn','first'))
 p=p[p.su>0];p['share_pct']=(p.long/p.su)*100
 assert p.share_pct.between(0,100).all();return p

def profile(p,y,metric,scenario):
 r={'year':y,'metric':metric,'scenario':scenario,'n_prescribers':len(p),'n_with_positive_long':int(p.long.gt(0).sum()),'su_volume':p.su.sum(),'long_volume':p.long.sum()}
 for q in [0,.01,.1,.25,.5,.75,.9,.99,1]:r['p'+str(int(q*100))]=p.share_pct.quantile(q)
 sort=p.sort_values(['long'],ascending=False,kind='stable')
 for q in [.1,.01]:
  k=math.ceil(len(p)*q);r[f'top{int(q*100)}_n']=k;r[f'top{int(q*100)}_pct_of_recovered_long']=100*sort.long.iloc[:k].sum()/p.long.sum()
  pp=p[p.long>0].sort_values('long',ascending=False);kp=math.ceil(len(pp)*q);r[f'top{int(q*100)}_positive_long_only_pct']=100*pp.long.iloc[:kp].sum()/pp.long.sum()
 return r

def save(rows,name):
 df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
 df.to_csv(OUT/name,index=False,float_format='%.10g');return df

def main():
 years=range(2013,2025);nat=[];qa=[];names=[];brands=[];classes=[];bmissing=[];ap={};profiles=[];specialties=[];states=[];recover=[]
 for y in years:
  b=load('B',y);bn=b[b.Prscrbr_Geo_Lvl=='National'].copy()
  assert len(bn)>0
  for metric in METRICS:
   for ex in [False,True]:nat.append(national(bn,y,metric,ex))
  qa.extend([qa_rows(b,'B',y,'all_geographies'),qa_rows(bn,'B',y,'National')])
  tmp=bn[bn.GE65_Tot_30day_Fills.isna()].copy();tmp.insert(0,'year',y);bmissing.append(tmp)
  for s,d in [('B',b)]+([('A',load('A',y))] if (DATA/f'A_{y}_su.csv.gz').exists() else []):
   for n,g in d.groupby('Gnrc_Name'):
    names.append({'source':s,'year':y,'Gnrc_Name':n,'class':g['class'].iloc[0],'rows':len(g)})
   for (n,br,c,er),g in d.groupby(['Gnrc_Name','Brnd_Name','class','glipizide_er_xl']):brands.append({'source':s,'year':y,'Gnrc_Name':n,'Brnd_Name':br,'class':c,'glipizide_er_xl':er,'rows':len(g)})
   if s=='A':
    qa.append(qa_rows(d,'A',y,'provider_drug'))
    for cls in ['all','long','short','other']:
     ad=d if cls=='all' else d[d['class'].eq(cls)];bd=bn if cls=='all' else bn[bn['class'].eq(cls)]
     lo=bd.GE65_Tot_30day_Fills.sum();hi=lo+bd.loc[bd.GE65_Tot_30day_Fills.isna(),'Tot_30day_Fills'].sum();v=ad.GE65_Tot_30day_Fills.sum()
     recover.append({'year':y,'class':cls,'a_recovered_ge65_fills30':v,'b_ge65_lower':lo,'b_ge65_upper':hi,'recovery_lower_pct':100*v/hi if hi else np.nan,'recovery_upper_pct':100*v/lo if lo else np.nan})
    ap[y]=providers(d)
    ap[(y,'claims')]=providers(d,'claims')
    ap[(y,'claims','complete')]=providers(d,'claims',complete=True)
    for complete in [False,True]:
     pc=providers(d,complete=complete)
     # Spearman on complete published rows kept separately.
     if complete:ap[(y,'complete')]=pc
    if y in [2015,2024]:
     for metric in METRICS:
      for scenario,ex,complete in [('observed',False,False),('exclude_glipizide_ER_XL',True,False),('complete_published_SU_rows',False,True)]:
       p=providers(d,metric,ex,complete);profiles.append(profile(p,y,metric,scenario))
       sp=p.groupby('specialty').agg(n_prescribers=('su','size'),su_volume=('su','sum'),long_volume=('long','sum'));sp['share_pct']=100*sp.long_volume/sp.su_volume;sp=sp.sort_values('su_volume',ascending=False).reset_index();sp.insert(0,'rank_by_SU_volume',range(1,len(sp)+1));sp['year']=y;sp['metric']=metric;sp['scenario']=scenario;specialties.append(sp)
       st=p[p.state.isin(STATES)].groupby('state').agg(n_prescribers=('su','size'),su_volume=('su','sum'),long_volume=('long','sum'));st['share_pct']=100*st.long_volume/st.su_volume;st=st.sort_values('share_pct',ascending=False).reset_index();st['year']=y;st['metric']=metric;st['scenario']=scenario;st['rank_high_to_low']=range(1,len(st)+1);states.append(st)
  for cls in ['long','short','other']:
   g=bn[bn['class'].eq(cls)]
   classes.append({'year':y,'class':cls,'n_rows':len(g),'published_rows_status':'PRESENT' if len(g) else 'NO_MATCHED_PUBLISHED_ROWS','all_age_fills30':g.Tot_30day_Fills.sum(),'ge65_observed_fills30':g.GE65_Tot_30day_Fills.sum(),'lt65_observed_fills30':g.LT65_Tot_30day_Fills.sum(),'suppressed_rows':int(g.GE65_Tot_30day_Fills.isna().sum())})
 ndf=save(nat,'national_annual.csv');save(ndf[(ndf.metric=='fills30')&(ndf.sensitivity=='primary')],'national_annual_primary.csv');save(qa,'K0_row_QA.csv');save(names,'matched_generic_names.csv');save(brands,'matched_generic_brand_names.csv');save(classes,'national_by_class.csv');save(pd.concat(bmissing),'national_suppressed_rows.csv');save(recover,'K0_recovery.csv')
 slopes=[]
 for (metric,scenario),g in ndf.groupby(['metric','sensitivity']):
  x=g.year.values.astype(float);w=(x-x.mean())/np.sum((x-x.mean())**2)
  for age in ['ge65','lt65','age_gap']:
   key=age+'_share_' if age!='age_gap' else 'age_gap_';unit='_pct' if age!='age_gap' else '_pp'
   obs=g[key+'observed'+unit].values;lo=g[key+'lower'+unit].values;hi=g[key+'upper'+unit].values
   slopes.append({'metric':metric,'scenario':scenario,'age':age,'years':'2013-2024','n_years':len(g),'ols_slope_pp_per_year':np.dot(w,obs),'slope_lower_pp_per_year':np.sum(np.where(w>=0,w*lo,w*hi)),'slope_upper_pp_per_year':np.sum(np.where(w>=0,w*hi,w*lo)),'endpoint_change_divided_by_11_pp_per_year':(obs[-1]-obs[0])/11})
 save(slopes,'K2_slopes.csv')
 if profiles:save(profiles,'K3_provider_profiles.csv');save(pd.concat(specialties),'K3_specialties.csv');save(pd.concat(states),'K3_states.csv')
 corr=[]
 for y in range(2014,2025):
  if y not in ap or y-1 not in ap:continue
  for metric in METRICS:
   for scenario in ['observed','complete_published_SU_rows']:
    if metric=='fills30':
     a=ap[y-1] if scenario=='observed' else ap[(y-1,'complete')];b=ap[y] if scenario=='observed' else ap[(y,'complete')]
    else:
     a=ap[(y-1,'claims')] if scenario=='observed' else ap[(y-1,'claims','complete')];b=ap[(y,'claims')] if scenario=='observed' else ap[(y,'claims','complete')]
    pair=a[['share_pct']].join(b[['share_pct']],how='inner',lsuffix='_previous',rsuffix='_current')
    rho=pair.share_pct_previous.rank(method='average').corr(pair.share_pct_current.rank(method='average'))
    corr.append({'year_previous':y-1,'year_current':y,'metric':metric,'scenario':scenario,'matched_npi':len(pair),'spearman_rho':rho})
 save(corr,'K3_adjacent_year_spearman.csv')
 # Metadata mapping is validated against actual CSV and API fields, never inferred from vintage.
 manifest=json.loads((OUT/'evidence/source_manifest.json').read_text());mapping=[]
 common={'generic':'Gnrc_Name','brand':'Brnd_Name','total_claims':'Tot_Clms','total_fills30':'Tot_30day_Fills','total_beneficiaries':'Tot_Benes','ge65_volume_suppression_flag':'GE65_Sprsn_Flag','ge65_claims':'GE65_Tot_Clms','ge65_fills30':'GE65_Tot_30day_Fills','ge65_beneficiaries':'GE65_Tot_Benes','ge65_beneficiary_suppression_flag':'GE65_Bene_Sprsn_Flag'}
 text=['# 每年实际字段表（CSV Range 表头与 API 单行样本一致）','']
 for r in manifest:
  assert r['fields']==r['api_fields'];m={**common,**({'provider_id':'Prscrbr_NPI','provider_type':'Prscrbr_Type','state':'Prscrbr_State_Abrvtn'} if r['source']=='A' else {'geography_level':'Prscrbr_Geo_Lvl','geography_code':'Prscrbr_Geo_Cd','state_or_national':'Prscrbr_Geo_Desc'})}
  for canonical,field in m.items():
   assert field in r['fields'];mapping.append({'source':r['source'],'year':r['year'],'canonical':canonical,'actual_field':field})
  if r['source']=='B':mapping.append({'source':'B','year':r['year'],'canonical':'provider_type','actual_field':'NOT_AVAILABLE_NOT_REQUIRED'})
  text+=['## '+r['source']+' '+str(r['year']),f"版本元数据 modified: {r['modified']}；[CSV]({r['csv_url']})",'', '|序号|实际字段|','|---|---|']+[f'|{i}|`{f}`|' for i,f in enumerate(r['fields'],1)]+['']
 save(mapping,'field_mapping.csv');(OUT/'annual_fields.md').write_text('\n'.join(text))
 print('Analysis refreshed. A complete years:',[y for y in years if y in ap],flush=True)
 print(ndf[(ndf.metric=='fills30')&(ndf.sensitivity=='primary')][['year','ge65_share_observed_pct','lt65_share_observed_pct','age_gap_observed_pp']].to_string(index=False))
if __name__=='__main__':main()
