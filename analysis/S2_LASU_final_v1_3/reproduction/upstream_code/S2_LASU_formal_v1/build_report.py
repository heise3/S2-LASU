"""Assemble a numerical analysis report from saved results; no manuscript prose."""
from pathlib import Path
import json
import pandas as pd,numpy as np
O=Path(__file__).resolve().parents[1];T=O/'tables'
def read(name):return pd.read_csv(T/(name+'.csv'))
def primary(d):return d[d.metric.eq('fills30')&d.scenario.eq('primary')]
def tab(d,cols,dec=3):
    a=d[list(cols)].rename(columns=cols);lines=['| '+' | '.join(a.columns)+' |','| '+' | '.join(['---']*len(a.columns))+' |']
    for row in a.itertuples(index=False,name=None):
        cells=[]
        for column,v in zip(a.columns,row):
            if pd.isna(v):v='—'
            elif isinstance(v,(int,float,np.integer,np.floating)) and column in ['年','前一年','后一年','最早年','最晚年','post起始年']:v=str(int(v))
            elif isinstance(v,(int,np.integer)):v=f'{v:,}'
            elif isinstance(v,(float,np.floating)):v=f'{v:,.{dec}f}'
            cells.append(str(v).replace('|','/').replace('\n',' '))
        lines.append('| '+' | '.join(cells)+' |')
    return '\n'.join(lines)
R=[]
def add(s):R.append(s)
def table(d,cols,dec=3):add(tab(d,cols,dec))
D=json.load(open(O/'A2_decision.json'));E=json.load(open(O/'evidence/enrollment_denominator.json'))
A=primary(read('A1_national_annual'));a=A[A.family.eq('long')].sort_values('year');last=a[a.year.eq(2024)].iloc[0]
M=read('A2_model_coefficients');P=read('A4_profiles');C=read('A4_correlations');I=read('A4_state_ICC');SP=read('A4_specialties');RC=read('A4_recovery')
age_names={'all_age':'全年龄主分析','all_age_GE65_visible_subset':'≥65可见NPI子集／全年龄份额','ge65_visible':'≥65可见量份额'}
add('# S2-LASU 正式分析 v1：A1–A4 数字报告')
add('分析日期：2026-10-27。复用预检2013–2024的CMS文件、实际字段映射、已核对药名和ER/XL定义；不写稿。主指标为长效30天量/全部磺脲类（SU）30天量。百分比差和斜率分别用百分点、百分点/年。')
add(f'**A2 判定：{D["status"]}。一句话理由：州×年固定效应模型的年龄×年份交互为 +{D["model2_interaction_pp_per_year"]:.3f} 个百分点/年（州聚类95%CI {D["ci_low"]:.3f}–{D["ci_high"]:.3f}），方向与全国年龄差趋势一致且区间不跨0，符合预设 PASS 规则。**')
add(f'2024年≥65与<65长效份额分别为 **{last.ge65_share_pct:.3f}%、{last.lt65_share_pct:.3f}%**，差 **+{last.gap_pp:.3f}** 个百分点；{D["states_old_above_young"]}/{D["state_total"]}州为正。此判定支持州内年龄组差异的描述，不能解释为同一个体老化效应或Beers更新的因果效应。')
add('全国年龄差首次由负转正发生在2017年；全期交互为正不表示每一分段都持续扩大。A4全年龄主分析与年龄可见量敏感性使用不同可回收覆盖率，不能互换。')
add('2024年龄差几乎全部来自glimepiride系（+2.563 pp）；glyburide系仅+0.018 pp。全期年龄差扩大主要对应glyburide系原有负年龄差逐步趋近零，而2019–2023总体长效年龄差的拟合斜率为−0.198 pp/年，不能表述成持续加剧。')
add('## A1　国家级年龄份额、分段斜率与绝对量')
add('B表National行，2013–2024。长效包括glimepiride系、glyburide系、chlorpropamide；glimepiride与glyburide分母也均为全部SU。下表是年龄可见药品行之和；有年龄抑制的年份不声称为精确完整年龄总量。完整抑制上下界在CSV中，2024全国年龄量无抑制。')
table(a,{'year':'年','ge65_share_pct':'≥65长效%','lt65_share_pct':'<65长效%','gap_pp':'差值pp','age_suppressed_rows':'年龄量缺失药品行'})
wide=A.pivot(index='year',columns='family',values=['ge65_share_pct','lt65_share_pct','gap_pp'])
wide.columns=[f'{f}_{v}' for v,f in wide.columns];wide=wide.reset_index();wide.to_csv(T/'A1_family_shares_wide.csv',index=False,float_format='%.12g')
table(wide,{'year':'年','glimepiride_ge65_share_pct':'glime ≥65%','glimepiride_lt65_share_pct':'glime <65%','glimepiride_gap_pp':'glime差pp','glyburide_ge65_share_pct':'gly ≥65%','glyburide_lt65_share_pct':'gly <65%','glyburide_gap_pp':'gly差pp'})
add('### 连续分段线性斜率')
add('对12个年度点共同拟合连续线性样条：1、year−2013、(year−2015)+、(year−2019)+、(year−2023)+。节点没有水平跳跃；相邻段共享节点。2023–2024只有两个年度点，不能据此判断政策效果。')
add('这些是全期共同最小二乘拟合的段斜率，不是各段独立拟合或原始两端点差；局部曲率较强时其方向也可能与原始端点差不同。每年拟合值、残差与RMSE另存，图F1/F2画原始可见份额。')
s=primary(read('A1_segment_slopes')).pivot(index=['family','start','end','segment'],columns='age',values='slope_pp_per_year').reset_index()
table(s,{'family':'药物系','segment':'分段','ge65':'≥65 pp/年','lt65':'<65 pp/年','gap':'两组斜率差 pp/年'})
ov=primary(read('A1_overall_slopes')).pivot(index='family',columns='age',values='ols_pp_per_year').reset_index()
add('全期单一直线斜率（供A2方向判定参照）：')
table(ov,{'family':'药物系','ge65':'≥65 pp/年','lt65':'<65 pp/年','gap':'差 pp/年'})
add('### 绝对30天量与分母变化')
vol=a[['year','ge65_SU','lt65_SU','ge65_target','lt65_target']].copy();vol.to_csv(T/'A1_absolute_volumes.csv',index=False,float_format='%.12g')
table(vol,{'year':'年','ge65_SU':'≥65全部SU','ge65_target':'≥65长效','lt65_SU':'<65全部SU','lt65_target':'<65长效'},1)
changes=[]
for start in [2013,2019,2020]:
    z=a[a.year.eq(start)].iloc[0]
    for age in ['ge65','lt65']:
        changes.append(dict(period=f'{start}→2024',age=age,SU_change_pct=100*(last[f'{age}_SU']/z[f'{age}_SU']-1),long_change_pct=100*(last[f'{age}_target']/z[f'{age}_target']-1)))
ch=pd.DataFrame(changes);ch.to_csv(T/'A1_volume_changes.csv',index=False,float_format='%.12g')
table(ch,{'period':'期间','age':'年龄','SU_change_pct':'全部SU变化%','long_change_pct':'长效变化%'})
add('≥65的SU分母未出现与<65相同程度的收缩；份额变化必须与上述绝对量同时阅读。变化百分比按可见量计算，未把抑制量当零补回。')
sens=read('A1_national_annual');sens=sens[sens.year.eq(2024)&sens.family.eq('long')]
add('2024指标/ER-XL敏感性：排除glipizide ER/XL同时移除其分母量，改变了分母构成。')
table(sens,{'metric':'量指标','scenario':'口径','ge65_share_pct':'≥65%','lt65_share_pct':'<65%','gap_pp':'差pp'})
add('## A2　州内面板与预设判定')
add('50州×12年×2年龄组=1,200个格；权重为每格可见SU30天量。M1=old+t+old×t+州FE；M2=old+old×t+州×年FE（共同t已被州×年FE吸收）。old=1为≥65；t=year−2013。M2比较同一州同一年内的两年龄组。')
add('标准误按州聚类（50簇），CR1全矩阵秩校正，区间采用t49；M2全秩602，CR1因子2.0459。不计嵌套FE的自由度校正另列。置信区间不包含抑制不确定性。')
mm=primary(M);main=mm[mm['sample'].eq('observed_age_rows')&mm.term.eq('old_t')]
table(main,{'model':'模型','coefficient':'交互pp/年','se':'州聚类SE','ci_low':'95%CI下限','ci_high':'95%CI上限','n_cells':'格数','n_states':'州数'})
add(f'**{D["status"]}**：M2交互同向且CI不跨0；全国全期年龄差斜率为+{D["national_age_gap_slope_pp_per_year"]:.3f} pp/年。')
add('### 抑制、指标和自由度敏感性')
ss=M[M.model.eq(2)&M.term.eq('old_t')&M['sample'].eq('observed_age_rows')]
table(ss,{'metric':'量指标','scenario':'ER口径','coefficient':'交互pp/年','ci_low':'95%CI下限','ci_high':'95%CI上限'})
sub=mm[mm.model.eq(2)&mm.term.eq('old_t')&~mm['sample'].str.startswith('post')&~mm['sample'].eq('observed_age_rows')]
table(sub,{'sample':'敏感性样本/处理','coefficient':'交互pp/年','ci_low':'95%CI下限','ci_high':'95%CI上限','n_cells':'格数','n_states':'州数'})
b=primary(read('A2_interaction_suppression_bounds')).iloc[0]
add(f'固定可见SU权重下，把每个被抑制年龄药品量放宽至[0,全年龄量]后，交互的保守界为 **{b.fixed_weight_lower:.3f}–{b.fixed_weight_upper:.3f} pp/年**。这是格间独立放宽得到的界，不是置信区间。上表四种分配敏感性同时重新计算权重，不能视为全体可能分配的穷尽界。全部已发布年龄行都可见的州年只有103/600，删去其余州年后的区间跨0；该结果受明显样本选择限制，不能隐藏。')
post=mm[mm.term.eq('old_post')]
add('### 2023节点的描述性项')
table(post,{'post_start':'post起始年','coefficient':'old×post水平差pp','ci_low':'95%CI下限','ci_high':'95%CI上限'})
add('两者均保留old×t。post2023=2023/2024两年，post2024只有2024一年；这是相对全期直线的水平偏离，不是节点后斜率，也不是2023 Beers更新的效应估计。')
st=read('A2_state_gaps_2024')
add(f'### 2024州间结果：{D["states_old_above_young"]}/50为正，{D["states_robust_old_above_young"]}/50在抑制界下仍为正')
add('California、Colorado为负；Wisconsin点估计略为正但抑制界跨0。排序全表见A2_state_gaps_2024.csv及F3。以下列最低/最高5州。')
table(pd.concat([st.head(5),st.tail(5)]),{'state_name':'州','ge65_share_pct':'≥65%','lt65_share_pct':'<65%','gap_pp':'差pp','gap_lower_pp':'抑制界下限','gap_upper_pp':'抑制界上限'})
pan=read('A2_state_age_panel');supp=[]
for year,g in pan[pan.age.eq('ge65')].groupby('year'):
    supp.append(dict(year=year,n_state_years=len(g),n_state_years_any_suppression=int(g.age_suppressed_rows.gt(0).sum()),n_suppressed_drug_rows=int(g.age_suppressed_rows.sum()),unallocated_all_age_fills=g.suppressed_all_age_volume.sum(),unallocated_pct_of_all_age_SU=100*g.suppressed_all_age_volume.sum()/g.all_age_su.sum()))
su=pd.DataFrame(supp);su.to_csv(T/'A2_suppression_summary.csv',index=False,float_format='%.12g')
add('### 年龄抑制与排除单位')
table(su,{'year':'年','n_state_years_any_suppression':'含年龄抑制州年数/50','n_suppressed_drug_rows':'抑制药品行','unallocated_all_age_fills':'待分配全年龄量','unallocated_pct_of_all_age_SU':'占全年龄SU%'},4)
ex=read('A2_excluded_geographic_units');ex=ex[ex.level.ne('National')]
units=ex.groupby(['geo_code','unit']).agg(first_year=('year','min'),last_year=('year','max'),n_years=('year','nunique')).reset_index()
table(units,{'geo_code':'代码','unit':'排除单位','first_year':'最早年','last_year':'最晚年','n_years':'出现年数'},0)
add('National行另保留于排除记录，原因是已用于全国分析，不是州观察。没有把DC或领地混入50州；未丢弃任何SU量>0的可见年龄格。逐药抑制原始行及全部被排除州级单位按年份保存。保守界不能覆盖因发布阈值而整行未公开的药品。')
add('## A3　2024年≥65规模')
scale=read('A3_scale_with_enrollment_2024');show=scale[scale.family.isin(['glimepiride','glyburide','long'])]
table(show,{'family':'系','published_drug_rows':'全国药品行','beneficiary_row_count_sum':'受益人数药品行合计','fills30_observed':'30天量','beneficiary_row_counts_per_1000_enrollee_person_years':'每千参保人年受益人次'},3)
add('受益人数是CMS各Gnrc_Name×Brnd_Name行的GE65_Tot_Benes合计；同一人跨药、跨品牌或组合制剂可重复，系内也可能重复。合计1,130,596不能写成去重患者数。chlorpropamide在2024无匹配已发布行；这不证明实际使用为零。')
add(f'已找到官方年龄分母：**{E["denominator"]:,.0f}个≥65 Part D参保人年**。来源为[CMS Program Statistics—Medicare Part D Enrollment 2024]({E["source_url"]})，工作表`{E["sheet"]}`，单元格`{E["cell"]}`，行`65 Years and Over`、列`Total Part D Enrollees`。官方按参保月数折算人年，且此表公布值取整；因此上表是年度药品受益人次/千参保人年，不是去重个人用药率、风险或发生率。')
add('Medicare Monthly Enrollment仅提供全Medicare年龄边际和Part D总量边际，未用二者相乘推算。已保存原xlsx、zip、表格逐行CSV、目录证据、实际Monthly字段样例和分母提取坐标。')
add('## A4　处方者分析')
add('主分析以公开A表全年龄SU量>0的NPI为单位；描述性统计包括全部公开地区，州随机效应模型限50州。A表可回收量是已发布处方者×药品行合计，不能把未公开的低量行补零为已观测值。分位数NPI等权；专科份额和集中度按量计算。')
add('### 全国量覆盖率')
rc=RC[RC.scenario.eq('primary')].copy();rc['age_label']=rc.age.map(age_names)
table(rc,{'year':'年','age_label':'口径','n_prescribers':'NPI数','A_SU':'A可回收SU量','SU_recovery_lower_pct':'SU覆盖率下界%','SU_recovery_upper_pct':'SU覆盖率上界%','long_recovery_lower_pct':'长效覆盖率下界%'},3)
add('全年龄≥65可见NPI子集：保留至少一个≥65值可见（含0）的处方者，但份额仍按全年龄量计算；其覆盖率分母为全国全年龄量。≥65可见量份额：只合计≥65量可见且合计>0的处方者，覆盖率分母为全国≥65量。两种敏感性分别识别NPI选择与年龄量抑制的影响。')
add('### 分位数和长效量集中度（表中覆盖率对应本行口径）')
pp=P[P.scenario.eq('primary')].copy();pp['age_label']=pp.age.map(age_names)
table(pp,{'year':'年','age_label':'口径','SU_coverage_pct':'SU覆盖率%','p10':'P10%','p25':'P25%','p50':'中位%','p75':'P75%','p90':'P90%','top10_pct_of_recovered_long':'前10%占长效%','top1_pct_of_recovered_long':'前1%占长效%'})
add('前10%/1%以所有合格NPI人数向上取整，按其长效量排序；分母为同口径A可回收长效量。全部分位数（P0/1/10/25/50/75/90/99/100）及只在长效阳性处方者中取前百分位的补充结果见A4_profiles.csv。')
for age in ['all_age','all_age_GE65_visible_subset','ge65_visible']:
    for year in [2019,2024]:
        cov=rc[rc.age.eq(age)&rc.year.eq(year)].iloc[0].SU_recovery_lower_pct
        add(f'### {year}专科：{age_names[age]}，SU覆盖率≥{cov:.2f}%')
        z=SP[SP.year.eq(year)&SP.age.eq(age)&SP.scenario.eq('primary')&SP.display_top10_or_endocrine].sort_values('rank_by_SU')
        table(z,{'rank_by_SU':'SU量排名','specialty':'Prscrbr_Type','n_prescribers':'NPI数','su_volume':'全部SU量','long_volume':'长效量','share_pct':'长效占比%'},2)
        add('Endocrinology即使已在前10中也明确列出，不重复加总；全部专科见CSV。')
add('### 处方者跨年Spearman')
cc=C[C.scenario.eq('primary')].copy();cc['age_label']=cc.age.map(age_names)
table(cc,{'year_previous':'前一年','year_current':'后一年','age_label':'口径','matched_npi':'两年均合格NPI','spearman_rho':'Spearman ρ'},4)
add('只匹配两年都可观察到相应SU量的NPI，未出现的NPI不补零；并列值用平均秩。ER/XL排除和全部已发布SU年龄行可见子集的相关见完整CSV。')
add('### 专科固定效应＋州随机截距：量加权logit尺度ICC')
add('REML模型：z=log((L+0.5)/(S−L+0.5)) ~ 专科 + (1|州)，w=S/平均S，残差方差sigma²/w。所有实际专科类别均作为固定效应，未仅保留前10。仅50州进入模型；非州NPI计数与量在A4_model_excluded_units.csv。ICC是量参照处方者的logit尺度方差比，不是患者ICC或原始份额解释度。')
ii=I[I.continuity.eq(.5)].copy();ii['age_label']=ii.age.map(age_names)
table(ii,{'year':'年','age_label':'口径','n_prescribers':'模型NPI','n_specialties':'专科数','model_SU_recovery_pct':'模型SU覆盖率%','ICC_mean_volume':'平均量参照ICC','ICC_median_volume':'中位量参照ICC'},4)
ic=I.groupby(['year','age']).agg(ICC_min=('ICC_mean_volume','min'),ICC_max=('ICC_mean_volume','max')).reset_index();ic['age_label']=ic.age.map(age_names)
table(ic,{'year':'年','age_label':'口径','ICC_min':'c=0.1/0.5/1最小ICC','ICC_max':'最大ICC'},4)
add('c为对0%/100%份额的连续性处理量（单位：30天量）。上述区间是c敏感性范围，不是ICC置信区间。固定效应系数、州BLUP、两个方差分量与收敛记录全部输出；专科系数SE为给定估计方差分量的模型SE，不是州聚类SE。')
add('### ≥65可见/不可见处方者的全年龄SU量分布')
vv=read('A4_visibility_distributions')
table(vv,{'year':'年','visibility_group':'年龄可见性','n_prescribers':'NPI数','all_age_SU_mean':'全年龄SU均值','p25_all_age_SU':'P25','p50_all_age_SU':'中位','p75_all_age_SU':'P75','p90_all_age_SU':'P90','visible_but_zero_n':'可见但≥65量为0的NPI'},2)
add('可见=至少一条≥65量非缺失；不可见=全部≥65量缺失。可见NPI整体SU量更大，表明年龄可见子集有规模选择；≥65可见量覆盖率约一半，不能当作全国所有处方者的完整老年用药结构。')
add('### ER/XL与年龄完整行敏感性')
pe=P[~P.scenario.eq('primary')].copy();pe['age_label']=pe.age.map(age_names)
table(pe,{'year':'年','age_label':'口径','scenario':'敏感性','n_prescribers':'NPI数','SU_coverage_pct':'SU覆盖率%','p50':'中位份额%','top10_pct_of_recovered_long':'前10%长效量%','top1_pct_of_recovered_long':'前1%长效量%'},3)
add('## 图、审计与复现')
for stem,title in [('F1_national_long_acting_share','F1 两年龄组长效占比'),('F2_glimepiride_glyburide_share','F2 glimepiride/glyburide两面板'),('F3_state_age_gap_2024','F3 2024各州年龄差排序')]:
    add(f'- {title}：[矢量PDF](figures/{stem}.pdf) · [300 dpi PNG](figures/{stem}.png)')
add('F1/F2虚线仅标记2015/2019/2023 Beers年份。F3横线为抑制界而非置信区间；50州全列。所有图从交付CSV生成。')
fit=read('A1_piecewise_fitted');annual=read('A1_national_annual');diagnostic=[];residuals=[]
for key,g in fit.groupby(['family','metric','scenario','age']):
    fam,metric,scenario,age=key;v=annual[annual.family.eq(fam)&annual.metric.eq(metric)&annual.scenario.eq(scenario)].set_index('year')
    column={'ge65':'ge65_share_pct','lt65':'lt65_share_pct','gap':'gap_pp'}[age]
    obs=v.loc[g.year,column].to_numpy();res=obs-g.fitted_share_or_gap.to_numpy()
    diagnostic.append(dict(family=fam,metric=metric,scenario=scenario,age=age,n=12,parameters=5,RMSE_pp=np.sqrt(np.mean(res**2)),max_abs_residual_pp=np.abs(res).max()))
    for year,o,f,r in zip(g.year,obs,g.fitted_share_or_gap,res):residuals.append(dict(family=fam,metric=metric,scenario=scenario,age=age,year=year,observed=o,fitted=f,residual_pp=r))
pd.DataFrame(diagnostic).to_csv(T/'A1_fit_diagnostics.csv',index=False,float_format='%.12g');pd.DataFrame(residuals).to_csv(T/'A1_fit_residuals.csv',index=False,float_format='%.12g')
qa=json.load(open(O/'evidence/validation.json'))
add(f'数值与来源核验：{sum(x["passed"] for x in qa)}/{len(qa)}项通过，包括既有预检SHA256不变、输入哈希、1200格完整性、份额/抑制界、全年龄减≥65无负值、M1/M2与独立完整虚拟变量WLS及statsmodels聚类协方差一致、加权REML与独立MixedLM校验、生产模型收敛及集中度重算。验证仅证明这些计算与保存记录一致，不替代数据选择偏差评估。详细记录见evidence/validation.json。')
add('主分析代码为code/run_analysis.py与code/models.py；图、报告、独立验证及官方参保表提取各有独立脚本。执行顺序和依赖见README.md。既有预检报告、字段映射、药名清单和代码保持原样；本次所有输出独立保存在S2_LASU_formal_v1。')
add('逐药抑制记录：B_age_suppression_rows.csv及A4_suppressed_provider_drug_rows_2019/2023/2024.csv.gz。所有排除记录：A2_excluded_geographic_units.csv、A2_excluded_age_cells.csv、A4_model_excluded_units.csv。后两类分别是年龄格不可估计和多层模型地区排除，不与数据抑制混为一类。')
(O/'S2_LASU_formal_v1_summary.md').write_text('\n\n'.join(R)+'\n')
print('Wrote numerical report and supplementary summary CSVs.')
