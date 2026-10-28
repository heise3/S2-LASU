from pathlib import Path
import json
import pandas as pd,numpy as np
O=Path(__file__).resolve().parents[1];T=O/'tables';E=O/'evidence'
def read(x):return pd.read_csv(T/(x+'.csv'))
R=[]
def add(s):R.append(s)
def table(d,cols,dec=3):
    a=d[list(cols)].rename(columns=cols);out=['| '+' | '.join(a.columns)+' |','| '+' | '.join(['---']*len(a.columns))+' |']
    for row in a.itertuples(index=False,name=None):
        ss=[]
        for name,v in zip(a.columns,row):
            if pd.isna(v):s='—'
            elif name in ['年','起年','止年']:s=str(int(v))
            elif isinstance(v,(bool,np.bool_)):s='是' if v else '否'
            elif isinstance(v,(int,np.integer)):s=f'{v:,}'
            elif isinstance(v,(float,np.floating)):s=f'{v:,.{dec}f}'
            else:s=str(v)
            ss.append(s.replace('|','/').replace('\n',' '))
        out.append('| '+' | '.join(ss)+' |')
    add('\n'.join(out))
D=json.load(open(O/'R2_decision.json'));rates=read('R1_rates_wide');change=read('R1_direction_comparison');den=read('R1_enrollment_denominators')
add('# S2-LASU 正式分析 v1.1：R1–R5 稳健性补丁')
add('日期：2026-10-27。复用formal_v1的字段映射、药名分类、固定效应估计与聚类校正；所有新文件位于本目录，v1不改动。不写稿，仅交付数字、表和判定。')
add('## 开头单列：R1标准化后出现方向反转')
add('**2013→2024，≥65全部SU绝对30天量增加13.48%，但每千参保人年量从859.10降至588.52（−31.50%）；因此，v1的绝对量增长不能用于支持“参保人均SU暴露未下降”。** 同期≥65参保人年增长65.66%。≥65 glimepiride、glipizide的全期趋势也从绝对量增加改为人年率下降；<65 glipizide从绝对量−7.73%变为人年率+0.09%，后者仅近乎持平的微小反转。')
table(change[change.direction_reversed],{'age':'年龄','family':'类别','start_year':'起年','end_year':'止年','raw_volume_change_pct':'绝对量变化%','standardized_rate_change_pct':'人年率变化%'})
add('方向反转按预先保留的2013→2024、2019→2024、2020→2024三个比较期逐一审计；并非事后挑选比较年。完整30项比较及抑制界在R1_direction_comparison.csv。人年标准化不会改变同一年龄组内长效/全部SU份额，因为分子分母的参保人年会相消；不能把份额趋势与每千参保人年的暴露量混称。')
add(f'**R2 判定：{D["status"]}。一句话理由：四种按CMS规则构造、保持年龄总量守恒的端点情形，模型2交互均为正且州聚类95%CI均不跨0。** 完全可见子集的区间跨0，另行完整报告；本判定仅针对预设四情形，不声称所有任意混合分配已被全局优化。')
add('## R1　按年龄的Part D参保人年标准化')
add('2013–2024两年龄组均已取得，未触发“仅输出≥65”的回退条件。逐年使用CMS Program Statistics—Medicare Part D Enrollment人口特征表中实际的`Total Part D Enrollees`列，以及`65 Years and Over`、`Under 65 Years`行；各年注释均确认按参保月份折算person-year。2024 ≥65分母与v1 A3完全相同。未使用全Medicare年龄比例推算Part D人数。')
dd=den.pivot(index='year',columns='age',values='enrollee_person_years').reset_index()
table(dd,{'year':'年','ge65':'≥65参保人年','lt65':'<65参保人年'},0)
add('表内官方分母为已取整公布数，年龄分组之和与总计部分年份差1，保留原值，不强行平差；记录见R1_enrollment_rounding_audit.csv。每年原始xlsx/zip、工作表、单元格、表头、年龄行、来源URL与哈希均已保存。官方人年定义可查[CMS Medicare and Medicaid Reports方法](https://data.cms.gov/resources/medicare-and-medicaid-reports-methodology)，各年下载链接见R1_enrollment_denominators.csv。')
for age,label in [('ge65','≥65'),('lt65','<65')]:
    add(f'### {label}：每千Part D参保人年的30天量')
    table(rates[rates.age.eq(age)],{'year':'年','SU':'全部SU','long':'长效','glimepiride':'glimepiride系','glyburide':'glyburide系','glipizide':'glipizide系'},2)
add('主值沿用v1全国可见年龄药品行合计；存在年龄抑制的年份不能写成完整年龄量。R1_rates_long.csv同时给出按R2规则推导的分子下/上界和对应率界；可见量未加回任何推断值，因此可能低于规则识别区间的下界。2013、2024全国这几类量无年龄抑制，全期端点比较不受这些年龄空白影响。界限不覆盖整条未公开药品行。')
table(change[change.start_year.eq(2013)&change.family.isin(['SU','long'])],{'age':'年龄','family':'类别','raw_volume_change_pct':'绝对量变化%','standardized_rate_change_pct':'人年率变化%','denominator_change_pct':'参保人年变化%'})
add('两组长效人年率均下降：≥65 −47.74%、<65 −49.18%。长效每千人年量在2013年已经是≥65高于<65（430.42比321.06），这与SU内部长效份额于2017年才转为≥65更高，是不同指标上的事实。')
add('## R2　按真实抑制规则的面板端点情形')
add('### 规则与四情形定义')
add('`GE65_Sprsn_Flag=*`针对老年组1–10条claims；`#`针对<65小计1–10条claims而反向抑制老年组。30天量随claims抑制，每条claim的标准化量限定在1–12，故不能把所有老年组空白填成0或10个30天量。[CMS历史方法及旗标解释，第6页](https://www.cms.gov/files/document/part-d-prescriber-puf-methodology.pdf)；[当前地理表字典，第2页](https://data.cms.gov/sites/default/files/2025-04/MUP_DPR_RY25_20250401_DD_Geo_508.pdf)；[当前通用方法，第6–7页](https://data.cms.gov/sites/default/files/2026-05/MUP_DPR_RY26_20260421_Methodology_508.pdf)。')
add('设全年龄claims=C、30天量=F。原发小年龄组采用用户指定的宽松下界0；上界 **U=min(10×12, F−max(C−10,0))**，其中第二项保证另一年龄组至少C−10条claim、每条至少1个fill。0是压力分析放宽值，原发小计实际为1–10 claims。*行的≥65界为[0,U]；#行的≥65界为[F−U,F]，<65由F减≥65获得。120是每claim上限推导的保守fills上界，不是CMS直接发布的fills抑制阈值。')
labels={'primary_small_lower':'S1 原发小年龄组全部取0','primary_small_upper':'S2 原发小年龄组全部取U','old_lower_young_upper':'S3 ≥65量下界／<65量上界','old_upper_young_lower':'S4 ≥65量上界／<65量下界','share_old_lower_young_upper':'补充：≥65份额下界／<65份额上界','share_old_upper_young_lower':'补充：≥65份额上界／<65份额下界','complete_published_state_years':'全部已发布年龄fills可见的103州年'}
add('S1/S2的0/U作用于原发小组，#的大组由总量相减恢复，避免误把反向抑制大格当小格。S3/S4对两年龄的量取互补端点。四情形逐药赋值，均保持≥65+<65=全年龄；重新汇总州年年龄SU权重与长效份额。不能将两个年龄的体量都独立填下界或都填上界，那会破坏已知总量。')
cf=read('R2_model2_coefficients');m=cf[cf.term.eq('old_t')].copy();m['label']=m.scenario.map(labels)
table(m[m.role.eq('primary_four')],{'label':'情形','coefficient':'交互pp/年','se':'州聚类SE','ci_low':'95%CI下限','ci_high':'95%CI上限'})
add(f'**{D["status"]}**：四情形同为正向且CI均不跨0。沿用v1的50州、1,200格、600个州×年FE、全秩602的CR1校正，CI使用t49。统计CI未合并抑制不确定性；端点情形分别给出。')
supp=read('R2_suppressed_drug_row_bounds');supp=supp[supp.Prscrbr_Geo_Lvl.eq('State')&supp.Prscrbr_Geo_Cd.isin(['01','02','04','05','06','08','09','10','12','13','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','44','45','46','47','48','49','50','51','53','54','55','56'])]
flag=supp.groupby('GE65_Sprsn_Flag').agg(n_rows=('year','size'),min_upper=('small_fills_upper','min'),max_upper=('small_fills_upper','max')).reset_index()
table(flag,{'GE65_Sprsn_Flag':'旗标','n_rows':'50州跨年药品行数','min_upper':'小格U最小值','max_upper':'小格U最大值'},1)
add('年龄“量”下界不必使长效“份额”最低，因此另做两种更直接的份额对抗分配：老年长效行取低、非长效行取高（年轻组互补），以及反向。它们是补充压力结果，未事后替换四情形的预设判定。')
table(m[m.role.eq('supplementary_share_extreme')],{'label':'补充情形','coefficient':'交互pp/年','ci_low':'95%CI下限','ci_high':'95%CI上限'})
add('### 全可见103州年子集')
table(m[m.role.eq('complete_subset')],{'coefficient':'交互pp/年','ci_low':'95%CI下限','ci_high':'95%CI上限','n_cells':'年龄格数','n_states':'州数'})
inc=read('R2_complete_state_list')
add('纳入41州：'+', '.join(inc.state)+ '。这里是各州部分年份，不是41州完整12年面板；逐州年份如下。')
table(inc,{'state':'州代码','state_name':'州名','n_state_years':'纳入年数','years':'纳入年份'},0)
add('该子集95%CI跨0，应保留为不确定结果。103州年仅占600州年的17.17%，包含41州但时间覆盖不均，不能用它单独否定或证明全50州结果。详细面板、四情形逐药赋值、上下界、守恒核查、完整州年名单和模型所有系数均已输出。')
add('## R3　药物定义敏感性')
add('两项独立改变：①将已有ER/XL标记的glipizide行加入长效分子，全部SU分母保持不变；②剔除全部实际匹配复方，分子分母同时删除，其他分类保持v1。没有把两个改动叠加。')
defs=read('drug_definition_audit');combo=defs[defs.is_combination].Gnrc_Name.drop_duplicates().sort_values().tolist()
add('实际被剔除的全部唯一复方名：'+ '；'.join('`'+s+'`' for s in combo)+'。ER/XL被重新归类的品牌及逐年记录见R3_ER_XL_reclassified_rows.csv；复方逐行排除见R3_excluded_combination_rows.csv。')
ns=read('R3_national_annual')
for definition,label in [('ER_XL_as_long','ER/XL计为长效'),('exclude_all_SU_combinations','剔除全部SU复方')]:
    add('### '+label+'：全国逐年序列')
    table(ns[ns.definition.eq(definition)],{'year':'年','ge65_share_pct':'≥65长效%','lt65_share_pct':'<65长效%','gap_pp':'年龄差pp'})
cm=read('R3_model2_coefficients');cm=cm[cm.term.eq('old_t')]
add('### 模型2年龄×年份交互')
table(cm,{'definition':'定义','coefficient':'交互pp/年','ci_low':'95%CI下限','ci_high':'95%CI上限'})
add('两项定义敏感性仍为正向且CI不跨0。ER/XL计为长效时，2013年龄差已为+0.243 pp，改变了最早出现正年龄差的时间；因此“2017才发生倒挂”仅适用于主定义，不能推广到ER/XL定义。')
add('## R4　年龄差形成阶段')
s=read('R4_segment_slopes')
table(s,{'segment':'时间段','ge65':'≥65斜率pp/年','lt65':'<65斜率pp/年','gap':'斜率差pp/年','observed_gap_at_start':'原始起点差pp','observed_gap_at_end':'原始终点差pp','observed_gap_change':'原始端点变化pp'})
add('沿用v1对12年共同拟合的连续线性样条（2015/2019/2023节点）；这些段斜率不是各段独立回归，也不是原始端点差除以年数。最后一段只有2023/2024两个年度点，节点仅作描述。')
add('**一句话：主定义的倒挂主要形成于2015–2019年（年龄差拟合斜率+1.051 pp/年、原始差值由−1.251升至+2.573 pp，并在2017年首次转正），2019–2023年收窄，2023–2024年小幅回升。**')
add('## R5　受益人数行合计与去重边界')
rows=read('R5_long_drug_beneficiary_rows')
table(rows,{'Gnrc_Name':'Gnrc_Name','Brnd_Name':'Brnd_Name','GE65_Tot_Benes':'≥65行内去重人数'},0)
add('每条Gnrc_Name×Brnd_Name全国药品行中的受益人数自身已去重，重复处方不会把同一行人数重复增加。行合计的重叠来自：同一人年内使用不同长效药；使用同分子的不同产品或品牌；单方与含该SU的复方先后/同时使用。复方行在药物分类时只计一次，其受益者仍可能与单方行重叠；这属于跨行人员重叠，不是代码将一条复方行计两遍。')
u=read('R5_beneficiary_union_bounds')
table(u,{'family':'范围','n_published_rows':'公开行数','published_union_lower':'去重并集下界','published_union_upper':'去重并集上界','possible_duplicate_excess_max':'行合计最多可能多计','combination_beneficiary_row_sum':'复方行人数合计'},0)
add('可识别的集合界：**max(单行人数) ≤ 这些公开行覆盖的去重人数 ≤ sum(行人数)**。长效5行并集下界1,061,523、上界1,130,596；下界来自单方Glimepiride行，而不是把所有复方人群假定为独立。复方两行合计15,523（1,047+14,476），无法判断其中多少已在其他行出现。以上为逻辑界，不是置信区间。')
add('**可在正文使用的保守表述：**“2024年，5个已公开长效磺脲类药品行覆盖的≥65岁受益者去重人数介于1,061,523与1,130,596之间；上界为各行人数之和，下界为最大单药行人数，跨药及复方行的人员重叠无法由公开表识别。”')
add('范围限定必须保留：上界只针对这5个已公开且人数可见的药品行；它不是包含所有整行未公开药物的全国严格上界。chlorpropamide无匹配2024公开行，不等于确认实际使用为零。若只需全国层面的下限，可写“公开数据至少可确认1,061,523名≥65岁受益者使用了长效SU”。')
table(u,{'family':'范围','lower_per1000_enrollee_py':'下界/千参保人年','upper_per1000_enrollee_py':'上界/千参保人年'})
add('这里继续使用v1的48,439,021参保人年作分母；不能把人年比率写成去重个人用药率。R5为数字核对及一句可用表述，没有展开稿件。')
add('## 文件、复现与核验')
qa=json.load(open(E/'validation.json'));n=sum(x['passed'] for x in qa)
add(f'{n}/{len(qa)}项核验通过：v1文件集合和内容哈希不变、复用代码逐字一致、24个分母及取整差检查、120个标准化率算术、R2年龄量守恒/阈值界、全部10个模型与独立配对年龄差WLS及州聚类协方差一致、R3主定义复现v1、R4样条独立复算、R5最大行/行合计重算。详见evidence/validation.json及independent_paired_model_checks.csv。')
add('主入口：code/acquire_enrollment.py → extract_enrollment.py → run_patch.py → validate.py → build_report.py → package_outputs.py。执行命令见README.md；CSV索引见TABLE_INDEX.md。国家与州原数据仍复用上级outputs/data，不重复下载。抑制记录、复方排除行、ER重新分类行和源文件坐标均保留。')
(O/'S2_LASU_formal_v1_1_summary.md').write_text('\n\n'.join(R)+'\n')
print('Report complete')
