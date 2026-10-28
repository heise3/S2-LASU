"""Audit-only implementation repair; retain frozen inherited run and all old outputs.
clidinium substring falsely included aclidinium / umeclidinium. No therapeutic
class or threshold changes. Original a/c remain in the requested main comparison;
corrected a/c are supplied as a separate integrity sensitivity.
"""
from pathlib import Path
import sys,json,datetime,hashlib,os
sys.dont_write_bytecode=True
import pandas as pd,numpy as np
from lasu_models import fe_fit
from definitions import STATE_CODES
O=Path(__file__).resolve().parents[1];BASE=O/'tables';T=BASE/'corrected';T.mkdir(exist_ok=True);E=O/'evidence';B=O.parent/'S2_BEERS_precheck'
scs=['observed','primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower']
raw=pd.read_csv(B/'tables/matched_published_rows.csv.gz',dtype={'Prscrbr_Geo_Cd':str});d=raw[raw.entry.eq('antispasmodics')].copy();names=pd.read_csv(BASE/'numerator_names_frozen.csv',keep_default_na=False);d=d.merge(names[names.entry.eq('antispasmodics')],on=['entry','year','Gnrc_Name','Brnd_Name'],how='inner',validate='many_to_one');d=d[d.Prscrbr_Geo_Lvl.eq('State')].copy();d.Prscrbr_Geo_Cd=d.Prscrbr_Geo_Cd.fillna('').str.zfill(2);d=d[d.Prscrbr_Geo_Cd.isin(STATE_CODES)];d['state']=d.Prscrbr_Geo_Cd.map(STATE_CODES)
badmask=d.Gnrc_Name.str.contains(r'aclidinium|umeclidinium',case=False,regex=True);bad=d[badmask].copy();good=d[~badmask].copy();bad.to_csv(T/'excluded_false_positive_respiratory_rows.csv.gz',index=False,compression='gzip');bad[['Gnrc_Name','Brnd_Name']].drop_duplicates().to_csv(T/'excluded_false_positive_names.csv',index=False)
mp=pd.read_csv(BASE/'generic_atc_matches_frozen.csv');assert not mp[mp.ATC_class.eq('A03')].Gnrc_Name.isin(bad.Gnrc_Name.unique()).any(),'Do not subtract a valid denominator-class member'
def bounds(x):
 x=x.copy();F=x.Tot_30day_Fills;C=x.Tot_Clms;v=x.GE65_Tot_30day_Fills;star=x.GE65_Sprsn_Flag.eq('*');U=np.minimum(120,np.maximum(0,F-np.maximum(C-10,0)));lo=v.where(v.notna(),np.where(star,0,F-U));hi=v.where(v.notna(),np.where(star,U,F))
 for sc,a in {'observed':v,'primary_small_lower':np.where(star,lo,hi),'primary_small_upper':np.where(star,hi,lo),'old_lower_young_upper':lo,'old_upper_young_lower':hi}.items():x[sc]=a
 return x
bad=bounds(bad);good=bounds(good);pan=pd.read_csv(BASE/'state_age_year_share_panel.csv');original=pan.copy()
for i,r in pan[pan.entry.eq('antispasmodics')].iterrows():
 removed=bad[bad.state.eq(r.state)&bad.year.eq(r.year)];valid=good[good.state.eq(r.state)&good.year.eq(r.year)]
 pan.loc[i,'numerator_rows']=len(valid);pan.loc[i,'numerator_suppressed_rows']=valid.observed.isna().sum();pan.loc[i,'denominator_rows']-=len(removed);pan.loc[i,'denominator_suppressed_rows']-=removed.observed.isna().sum()
 for sc in scs:
  rem=removed[sc] if r.age=='ge65' else removed.Tot_30day_Fills-removed[sc];nv=valid[sc] if r.age=='ge65' else valid.Tot_30day_Fills-valid[sc]
  pan.loc[i,'num_'+sc]=nv.sum(min_count=1);pan.loc[i,'den_'+sc]-=rem.sum()
assert pan.loc[pan.entry.ne('antispasmodics')].equals(original.loc[original.entry.ne('antispasmodics')]);pan.to_csv(T/'state_age_year_share_panel.csv',index=False,float_format='%.12g')
rows=[];primary=[];excluded=[];g=pan[pan.entry.eq('antispasmodics')]
for sc in scs:
 p=g['num_'+sc]/g['den_'+sc];assert p.dropna().between(0,1).all()
 for scale in ['log','logit']:
  ok=p.gt(0)&p.le(1)&np.isfinite(p)
  if scale=='logit':ok &=p.lt(1)
  ok &=ok.groupby([g.state,g.year]).transform('all');q=g[ok].copy();q['share']=p[ok];q['share_pct']=np.log(p[ok]) if scale=='log' else np.log(p[ok]/(1-p[ok]));q['su_observed']=1.
  rr,_=fe_fit(q,2);rows.extend(x|dict(entry='antispasmodics',scenario=sc,scale=scale,status='OK') for x in rr)
  excluded.append(g[~ok].assign(scenario=sc,scale=scale));
  if sc=='observed':primary.append(q.assign(scale=scale))
cf=pd.read_csv(BASE/'share_all_coefficients.csv');cf=pd.concat([cf[cf.entry.ne('antispasmodics')],pd.DataFrame(rows)],ignore_index=True);cf.to_csv(T/'share_all_coefficients.csv',index=False,float_format='%.12g')
pp=pd.read_csv(BASE/'share_primary_model_panel.csv.gz');pp=pd.concat([pp[pp.entry.ne('antispasmodics')]]+primary,ignore_index=True);pp.to_csv(T/'share_primary_model_panel.csv.gz',index=False,compression='gzip')
pd.concat(excluded).to_csv(T/'antispasmodic_model_exclusions.csv',index=False)
allr=pd.read_csv(BASE/'three_approach_results_long.csv');newrows=pd.DataFrame(rows).query("scenario=='observed' and term=='old_t'")
for _,r in newrows.iterrows():
 idx=allr.index[allr.entry.eq('antispasmodics')&allr.approach.eq('b_share_'+r.scale)][0]
 for col in ['coefficient','se','ci_low','ci_high','p_value','n_cells','n_states','n_FE_groups','full_rank','df_cluster','CR1_factor','status']:allr.loc[idx,col]=r[col]
allr['direction']=np.where(allr.coefficient>0,'positive','negative');allr['CI_excludes_zero']=(allr.ci_low>0)|(allr.ci_high<0);allr['negative_significant']=allr.ci_high<0
allr['baseline_integrity_note']=np.where(allr.entry.eq('antispasmodics')&~allr.approach.str.startswith('b_'),'Original requested baseline retains inherited name-collision error; see corrected_all_approaches sensitivity','')
for app,z in allr.groupby('approach'):allr.loc[z.index,'within_approach_rank_desc']=z.coefficient.rank(ascending=False,method='min')
allr.to_csv(T/'three_approach_results_long.csv',index=False,float_format='%.12g')
flds=['coefficient','se','ci_low','ci_high','direction','CI_excludes_zero','n_cells','n_states'];w=allr.pivot(index=['entry','label','role'],columns='approach',values=flds);w.columns=['__'.join(x) for x in w.columns];w.reset_index().to_csv(T/'three_approach_comparison.csv',index=False,float_format='%.12g')
def ranks(z):
 out=[]
 for app,a in z.groupby('approach'):
  ref=a[a.role.eq('Table2_entry')];b=a[a.entry.eq('long_su')].iloc[0];ties=np.isclose(ref.coefficient,b.coefficient,atol=1e-12,rtol=0);n=int(((ref.coefficient<b.coefficient)&~ties).sum());pc=100*(n+.5*ties.sum())/33
  assert len(ref)==33 and ref.status.eq('OK').all()
  out.append(dict(approach=app,n_estimable_Table2=33,benchmark_beta=b.coefficient,benchmark_ci_low=b.ci_low,benchmark_ci_high=b.ci_high,n_below=n,n_tied=int(ties.sum()),percentile=float(pc),quartile=int(min(4,np.floor(pc/25)+1)),negative_significant_n=int(ref.ci_high.lt(0).sum()),negative_significant_fraction=float(ref.ci_high.lt(0).mean())))
 return pd.DataFrame(out)
r=ranks(allr);r.to_csv(T/'benchmark_percentile_and_decision_inputs.csv',index=False,float_format='%.12g')
# Correct the one faulty criterion in old national-PY/raw comparators as a sensitivity, not overwrite originals.
ac=allr.copy();den=pd.read_csv(B/'tables/enrollment_denominators.csv').set_index(['year','age']).enrollee_person_years
for app in ['a_national_denominator','c_raw_state_volume']:
 q=g[g.num_observed.gt(0)].copy();ok=q.groupby(['state','year']).old.transform('count').eq(2);q=q[ok];q['su_observed']=1.;q['share_pct']=np.log(q.num_observed)
 if app.startswith('a_'):q.share_pct=np.log(q.num_observed*1000/np.array([den.loc[(y,a)] for y,a in zip(q.year,q.age)]))
 rr,_=fe_fit(q,2);x=[v for v in rr if v['term']=='old_t'][0];i=ac.index[ac.entry.eq('antispasmodics')&ac.approach.eq(app)][0]
 for key in ['coefficient','se','ci_low','ci_high','p_value','n_cells','n_states']:ac.loc[i,key]=x[key]
ac['direction']=np.where(ac.coefficient>0,'positive','negative');ac['CI_excludes_zero']=(ac.ci_low>0)|(ac.ci_high<0);ac['negative_significant']=ac.ci_high<0
ac.loc[ac.entry.eq('antispasmodics'),'baseline_integrity_note']='Name collision corrected in this new sensitivity; original outputs untouched'
for app,z in ac.groupby('approach'):ac.loc[z.index,'within_approach_rank_desc']=z.coefficient.rank(ascending=False,method='min')
wc=ac.pivot(index=['entry','label','role'],columns='approach',values=flds);wc.columns=['__'.join(x) for x in wc.columns];wc.reset_index().to_csv(T/'fully_corrected_three_approach_comparison.csv',index=False,float_format='%.12g')
ac.to_csv(T/'corrected_all_approaches_sensitivity.csv',index=False,float_format='%.12g');rs=ranks(ac);rs.to_csv(T/'corrected_all_approaches_percentiles.csv',index=False,float_format='%.12g')
include=r.quartile.nunique()==1 and rs.quartile.nunique()==1
receipt=dict(decision='INCLUDE' if include else 'DO_NOT_INCLUDE',rule='User-approved same quartile across a,b_log,b_logit,c',requested_original_baselines_plus_corrected_share=r.to_dict('records'),all_approaches_name_corrected_sensitivity=rs.to_dict('records'),mapping_changed=False,repair='Remove aclidinium and umeclidinium false positives from GI antispasmodics; clidinium must have ingredient token boundaries',discovery='Name-only exception audit before first inspection of new effect estimates; numeric files had already been computed. This is a documented implementation correction, not a claim of a new blinded preregistration.',removed_state_rows=len(bad),removed_generic_names=sorted(bad.Gnrc_Name.unique()),corrected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=['https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6f92cceb-a63f-4470-99b6-56179d98f10f','https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=dbb64747-1505-49d7-9a33-99dd402e96d3'])
(E/'corrected_decision.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
# Accepted result: one two-panel figure, both prespecified transformations, corrected GI entry.
if include:
 os.environ['MPLCONFIGDIR']=str(E/'matplotlib_cache');import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'font.size':8})
 order=allr[allr.approach.eq('b_share_log')].sort_values(['organ','entry']).entry.tolist();fig,axes=plt.subplots(1,2,figsize=(15,13),sharey=True)
 for ax,scale in zip(axes,['log','logit']):
  z=allr[allr.approach.eq('b_share_'+scale)].set_index('entry').loc[order].reset_index()
  for i,row in z.iterrows():
   col='#b54a24' if row.entry=='long_su' else '#21658b';ax.errorbar(row.coefficient,i,xerr=[[row.coefficient-row.ci_low],[row.ci_high-row.coefficient]],fmt='o',ms=4,color=col,capsize=2)
  p=r[r.approach.eq('b_share_'+scale)].percentile.iloc[0];ax.set_title(f'{scale}(share) | LASU percentile {p:.1f} (Q4)',loc='left',weight='bold');ax.axvline(0,color='grey',ls='--',lw=.8);ax.set_xlabel('Older vs younger annual trend difference\nState × year FE; state-cluster 95% CI');ax.grid(axis='x',alpha=.15)
 axes[0].set_yticks(range(len(order)),z.label);axes[0].invert_yaxis();fig.suptitle('S2-LASU context benchmark: within-therapeutic-class shares, 2013–2024',x=.02,ha='left',weight='bold');fig.text(.02,.015,'33 Table 2 exposure entries; orange LASU benchmark is additional and excluded from the percentile reference. 30-day fills.\nATC therapeutic denominators frozen before fitting; GI name-collision corrected. Age-group trends, not Beers policy effects.\nUnder-65 Part D largely reflects disability-based eligibility; class membership does not establish indication-matched alternatives.',fontsize=8);fig.subplots_adjust(left=.33,right=.98,top=.93,bottom=.105,wspace=.12)
 for ext in ['pdf','png']:fig.savefig(O/f'figures/S2_LASU_BEERS_within_class_forest.{ext}',dpi=220)
 plt.close(fig)
