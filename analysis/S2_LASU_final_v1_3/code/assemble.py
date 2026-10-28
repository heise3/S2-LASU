"""Rebuild delivery views from frozen local tables. No model fitting or data refresh."""
from pathlib import Path
import json,re
import pandas as pd,numpy as np
O=Path(__file__).resolve().parents[1];T=O/'tables/main';V=O/'tables/details/lasu_v1';R=O/'tables/details/robustness_v1_1';B=O/'tables/details/beers_corrected'
def read(p):return pd.read_csv(p)
def save(d,n):d.to_csv(T/n,index=False,float_format='%.12g')
def tab(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(x).replace('|','/') for x in row)+' |' for row in rows)+'\n'
n=read(V/'A1_national_long.csv').query("metric=='fills30' and scenario=='primary'")
base=n.query("family=='long'").copy();base=base.rename(columns={'share_pct':'long_share_pct','su_observed':'SU_fills30_observed','target_observed':'long_fills30_observed'})
fam=n.pivot(index=['year','age'],columns='family',values='share_pct')[['glimepiride','glyburide']].rename(columns=lambda x:x+'_share_pct').reset_index()
rates=read(R/'R1_rates_wide.csv').rename(columns={c:c+'_fills30_per1000_enrollee_py' for c in ['SU','long','glimepiride','glyburide','glipizide']})
t1=base[['year','age','long_share_pct','SU_fills30_observed','long_fills30_observed','age_suppressed_rows','share_lower_pct','share_upper_pct']].merge(fam,on=['year','age'],validate='one_to_one').merge(rates,on=['year','age'],validate='one_to_one');save(t1,'T1_national_age_trends.csv')
a2=read(V/'A2_model_coefficients.csv');t2=a2[(a2.metric=='fills30')&(a2.scenario=='primary')&a2['sample'].isin(['observed_age_rows','post2023_descriptive'])];save(t2,'T2_state_panel_main_and_post2023.csv')
t3=read(V/'A4_profiles.csv').query("age=='all_age' and scenario=='primary'");save(t3,'T3a_prescriber_profiles.csv')
for name,fn in [('A4_recovery.csv','T3b_prescriber_coverage.csv'),('A4_specialties.csv','T3c_prescriber_specialties.csv'),('A4_correlations.csv','T3d_prescriber_correlations.csv')]:
 d=read(V/name);save(d.query("age=='all_age' and scenario=='primary'"),fn)
save(read(V/'A4_state_ICC.csv').query("age=='all_age' and continuity==0.5"),'T3e_prescriber_state_ICC.csv')
s=read(R/'R2_model2_coefficients.csv').query("term=='old_t'").copy();s['analysis']='suppression';s['variant']=s.scenario
r3=read(R/'R3_model2_coefficients.csv').query("term=='old_t'").copy();r3['analysis']='definition';r3['variant']=r3.definition
save(pd.concat([s,r3],ignore_index=True),'T4a_robustness_interactions.csv');save(read(R/'R1_direction_comparison.csv'),'T4b_standardization_direction_checks.csv');save(read(R/'R4_segment_slopes.csv'),'T4c_piecewise_slopes.csv')
save(read(R/'R5_beneficiary_union_bounds.csv'),'T5_beneficiary_scale_bounds.csv')
save(read(B/'fully_corrected_three_approach_comparison.csv'),'T6a_BEERS_three_approach_comparison.csv');ac=read(B/'corrected_all_approaches_sensitivity.csv');save(ac,'T6b_BEERS_three_approach_long.csv');rank=read(B/'corrected_all_approaches_percentiles.csv');save(rank,'T6c_BEERS_percentiles.csv')
# Effective numerator rule and names are separated from the frozen pre-repair audit copies.
c=read(O/'provenance/beers/inherited_numerator_manifest_AUDIT_ONLY.csv');c=c[c.status.eq('INCLUDED')].copy();c['effective_definition_note']='Inherited included entry; class denominators unchanged'
c.loc[c.entry.eq('antispasmodics'),'regex']=c.loc[c.entry.eq('antispasmodics'),'regex'].str.replace('clidinium',r'(?<![A-Za-z])clidinium(?![A-Za-z])',regex=False);c.loc[c.entry.eq('antispasmodics'),'effective_definition_note']='Corrected ingredient boundary; exclude aclidinium and umeclidinium respiratory products'
c.to_csv(O/'definitions/BEERS_numerator_manifest_effective.csv',index=False)
names=read(O/'provenance/beers/numerator_names_frozen_AUDIT_ONLY.csv');bad=names.entry.eq('antispasmodics')&names.Gnrc_Name.str.contains('aclidinium|umeclidinium',case=False,regex=True);names.loc[~bad].to_csv(O/'definitions/BEERS_numerator_names_effective.csv',index=False)
# One main-result ledger; retain units and source keys, never combine unlike estimands.
ledger=[]
def add(id,domain,estimate,unit,src,flt,lo=np.nan,hi=np.nan,status='DESCRIPTIVE'):
 ledger.append(dict(result_id=id,domain=domain,estimate=estimate,ci_low=lo,ci_high=hi,unit=unit,status=status,source_table=src,source_filter=flt))
for age in ['ge65','lt65']:
 z=t1[(t1.year==2024)&(t1.age==age)].iloc[0];add('2024_long_share_'+age,'national',z.long_share_pct,'percent','T1_national_age_trends.csv',f'year=2024;age={age}')
z=t1.query('year==2024').set_index('age');add('2024_age_gap','national',z.loc['ge65','long_share_pct']-z.loc['lt65','long_share_pct'],'percentage_points','T1_national_age_trends.csv','year=2024;ge65-lt65')
q=t2[(t2.model==2)&t2['sample'].eq('observed_age_rows')&t2.term.eq('old_t')];assert len(q)==1;z=q.iloc[0];add('A2_model2_age_year','state_panel',z.coefficient,'percentage_points/year','T2_state_panel_main_and_post2023.csv','model=2;sample=observed_age_rows;term=old_t',z.ci_low,z.ci_high,'PASS')
for _,z in pd.concat([s,r3],ignore_index=True).iterrows():add('robustness_'+z.analysis+'_'+z.variant,'robustness',z.coefficient,'percentage_points/year','T4a_robustness_interactions.csv',f'analysis={z.analysis};variant={z.variant}',z.ci_low,z.ci_high)
for _,z in t3.iterrows():
 for col,unit in [('n_prescribers','prescribers'),('p50','percent'),('top10_pct_of_recovered_long','percent'),('top1_pct_of_recovered_long','percent'),('SU_coverage_pct','percent')]:add(f'A4_{int(z.year)}_{col}','prescribers',z[col],unit,'T3a_prescriber_profiles.csv',f'year={int(z.year)};column={col}')
for _,z in read(T/'T3d_prescriber_correlations.csv').iterrows():add(f'A4_rho_{int(z.year_previous)}_{int(z.year_current)}','prescribers',z.spearman_rho,'Spearman_rho','T3d_prescriber_correlations.csv',f'years={int(z.year_previous)}-{int(z.year_current)}')
for _,z in read(T/'T3e_prescriber_state_ICC.csv').iterrows():add(f'A4_ICC_{int(z.year)}','prescribers',z.ICC_mean_volume,'ICC_at_mean_volume','T3e_prescriber_state_ICC.csv',f'year={int(z.year)};continuity=0.5')
z=read(R/'R1_direction_comparison.csv').query("age=='ge65' and family=='SU' and start_year==2013 and end_year==2024").iloc[0]
for col in ['raw_volume_change_pct','standardized_rate_change_pct']:add('R1_ge65_SU_'+col,'standardization',z[col],'percent_change_2013_to_2024','T4b_standardization_direction_checks.csv',f'age=ge65;family=SU;start_year=2013;column={col}')
for _,z in read(T/'T5_beneficiary_scale_bounds.csv').iterrows():
 for col in ['published_union_lower','published_union_upper']:add('R5_'+z.family+'_'+col,'beneficiary_scale',z[col],'beneficiaries_published_rows_union_bound','T5_beneficiary_scale_bounds.csv',f'family={z.family};column={col}')
for _,z in rank.iterrows():
 add('BEERS_beta_'+z.approach,'benchmark',z.benchmark_beta,'log/year' if z.approach!='b_share_logit' else 'log_odds/year','T6c_BEERS_percentiles.csv',f'approach={z.approach}',z.benchmark_ci_low,z.benchmark_ci_high,'INCLUDE_CONTEXT_ONLY')
 add('BEERS_percentile_'+z.approach,'benchmark',z.percentile,'percentile','T6c_BEERS_percentiles.csv',f'approach={z.approach};reference=33','', '', 'Q4')
save(pd.DataFrame(ledger),'MAIN_RESULTS.csv')
figs=[('F1','全国两年龄组长效SU份额','F1_national_long_acting_share','T1_national_age_trends.csv','2013–2024；Beers2015/2019/2023节点。阴影为v1公开行宽松抑制界。'),('F2','glimepiride与glyburide份额','F2_glimepiride_glyburide_share','T1_national_age_trends.csv','分母均为全部SU；原始年度份额，不是分段拟合线。'),('F3','2024州级年龄份额差','F3_state_age_gap_2024','../details/lasu_v1/A2_state_gaps_2024.csv','横线是v1宽松抑制界，不是统计CI；v1.1规则端点结果见T4a。'),('F4','修正版Beers同类内份额基准','F4_BEERS_within_class_benchmark','T6a_BEERS_three_approach_comparison.csv','单张双面板log/logit；33条目+额外长效SU；两面板84.85百分位。')]
pd.DataFrame([dict(figure_id=i,title=t,pdf=f'figures/{f}.pdf',png=f'figures/{f}.png',table=tb,legend_note=no) for i,t,f,tb,no in figs]).to_csv(O/'FIGURE_INDEX.csv',index=False)
(O/'FIGURES.md').write_text('# 最终图号 F1–F4\n\n'+tab(['图号','图','对应表','解释'],[[i,f'[{t}](figures/{f}.pdf)',tb,no] for i,t,f,tb,no in figs]))
# Retired artifacts stay at their original paths; none is an active table or figure.
dep=[('S2_BEERS_precheck/tables/K*.csv; figures/*; SUMMARY.md','DEPRECATED_FOR_ANALYTIC_USE','含GI clidinium子串误匹配，且独立BEERS论文路线停用','tables/main/T6a_BEERS_three_approach_comparison.csv'),('S2_BEERS_precheck/tables/drug_filtered/*','DEPRECATED_FOR_ANALYTIC_USE','低量过滤没有修复aclidinium/umeclidinium误匹配','tables/details/beers_corrected/'),('S2_LASU_BEERS_benchmark/tables/three_approach*.csv; tables/share_*.csv','DEPRECATED_INHERITED_RUN','冻结初算保留错误GI条目','tables/main/T6a_BEERS_three_approach_comparison.csv'),('S2_LASU_BEERS_benchmark/tables/corrected/three_approach_comparison.csv; three_approach_results_long.csv; benchmark_percentile_and_decision_inputs.csv','AUDIT_ONLY_NOT_MAIN','份额已修正，但(a)/(c)仍保留错误旧基线，含75.76百分位','tables/main/T6c_BEERS_percentiles.csv'),('S2_LASU_BEERS_benchmark/figures/frozen_inherited_not_for_use/*','DEPRECATED_FIGURE','错误GI项森林图','figures/F4_BEERS_within_class_benchmark.pdf'),('S2_LASU_BEERS_benchmark/evidence/decision.json','SUPERSEDED_DECISION','初算决定；当前使用全口径更正后的Q4核验','DECISIONS.json')]
pd.DataFrame(dep,columns=['old_artifact_relative_to_original_outputs','status','reason','replacement_in_this_release']).to_csv(O/'DEPRECATED.csv',index=False)
(O/'DEPRECATED.md').write_text('# 明确停用含 clidinium 误匹配的旧结果\n\n旧文件原样保留用于追溯，不删除、不覆盖。下列结果不得从原路径复制进主结果、图或新稿。旧GI项误将aclidinium/umeclidinium呼吸系统产品作为GI解痉药；最新三口径均须使用已纠正版本。\n\n'+tab(['旧产物','状态','理由','替代'],dep)+'\n原75.76百分位属于保留错误旧基线的审计比较，不是本最终包的主百分位；统一使用78.79/84.85/84.85/78.79。冻结映射原件及历史代码仅为审计，不是有效药名规则；有效清单在definitions/BEERS_numerator_*_effective.csv。LASU自身SU药名定义不含该clidinium规则，原LASU A1–A4结果未因此失效。\n')
dec=dict(version='v1.3',LASU_A2='PASS',LASU_R2='ROBUST',LASU_R2_caveat='103 fully visible state-years in41states; CI crosses0; four endpoint gate is not global optimization',BEERS='INCLUDE_AS_LASU_DESCRIPTIVE_CONTEXT',BEERS_independent_paper='STOP',benchmark_percentiles=rank[['approach','percentile','quartile']].to_dict('records'),warning='Under65 PartD predominantly disability-based eligibility; interactions are age-group trend differences, not Beers policy effects',results_source='VERIFIED_FULL_STATISTICAL_RECOMPUTE',statistical_reproduction_status='PASS',freeze_step_refits_models=False)
(O/'DECISIONS.json').write_text(json.dumps(dec,ensure_ascii=False,indent=2))
index=[]
for p in sorted(T.glob('*.csv')):
 d=read(p);index.append(dict(table=p.name,path=str(p.relative_to(O)),rows=len(d),columns=len(d.columns),status='ACTIVE'))
pd.DataFrame(index).to_csv(O/'TABLE_INDEX.csv',index=False)
(O/'TABLE_INDEX.md').write_text('# 最终主结果表\n\nMAIN_RESULTS.csv为统一主结果定位表；T1–T7为完整主题表。全部数字来自通过统计复现的源表；本脚本仅组装视图，实际重拟合状态见REPRODUCTION_RECEIPT.json。\n\n'+tab(['表','行数','列数'],[[f'[{x["table"]}]({x["path"]})',x['rows'],x['columns']] for x in index])+'\n完整原始敏感性、抑制/排除、处方者与官方分母记录见tables/details/。原A3受益人数行合计不能当作去重人数；最终规模界以T5为准。\n')
print('Assembled',len(index),'main CSVs; figures F1-F4; active BEERS uses corrected a/b/c only')
if __name__=='__main__':pass
