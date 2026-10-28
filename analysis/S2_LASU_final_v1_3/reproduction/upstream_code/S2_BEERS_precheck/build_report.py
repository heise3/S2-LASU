from pathlib import Path
import sys,json,hashlib,shutil,platform
sys.dont_write_bytecode=True
import numpy as np,pandas as pd
O=Path(__file__).resolve().parents[1];BASE=O/'tables';T=BASE/'drug_filtered';E=O/'evidence';PRE=O.parent
# Add provenance fields to filtered manifest without changing analysis membership.
h=pd.read_csv(BASE/'drug_criteria_manifest.csv');c=pd.read_csv(T/'drug_criteria_manifest.csv');cols=['entry','historical_basis','historical_source_url','first_any_Beers_reviewed'];c=c.drop(columns=[x for x in cols if x!='entry'],errors='ignore').merge(h[cols],on='entry',how='left')
c.loc[c.entry.eq('ergoloids'),'status']='LOW_VOLUME_LT100000';c.loc[c.entry.eq('ergoloids'),'qualification']='All matched generic names excluded below100000; pre-filter national observed11429.7, rule upper11586.8'
c.to_csv(T/'drug_criteria_manifest.csv',index=False);c[c.status.ne('INCLUDED')].to_csv(T/'excluded_entries.csv',index=False)
for name in ['field_mapping.csv','field_inventory.csv']:
 shutil.copy2(PRE/name,E/('LASU_'+name))
src=[r for r in json.loads((PRE/'evidence/source_manifest.json').read_text()) if r['source']=='B'];(E/'CMS_B_source_manifest.json').write_text(json.dumps(src,indent=2))
for name in ['CMS_methodology_2026.txt','legacy_prescriber_methodology.txt','CMS_geography_dictionary.txt','enrollment_sources.json','enrollment_extraction_notes.json']:
 shutil.copy2(PRE/'S2_LASU_formal_v1_1/evidence'/name,E/name)
d=pd.read_csv(BASE/'enrollment_denominators.csv');denfiles=[]
for workbook in d.workbook.unique():
 p=PRE/'S2_LASU_formal_v1_1'/workbook;dest=E/'enrollment_source_files'/Path(workbook).parent.name/Path(workbook).name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);denfiles.append(dict(source=str(p),copy=str(dest.relative_to(O)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
(E/'enrollment_copied_workbooks.json').write_text(json.dumps(denfiles,indent=2))
num=json.loads((E/'drug_filtered/summary_numbers.json').read_text());k4=json.loads((E/'K4_decision.json').read_text());m=num['meta'];k1=pd.read_csv(T/'K1_feasibility.csv');r=pd.read_csv(T/'K2_entry_results.csv');cf=pd.read_csv(T/'K2_all_coefficients.csv');main=r[r.role.eq('Table2_entry')];b=r[r.entry.eq('long_su')].iloc[0];oldb=pd.read_csv(BASE/'K2_entry_results.csv').query("entry=='long_su'").iloc[0]
# Threshold bounds computed from deduplicated original National drug rows.
from analyze_beers import prepare,bounds
z=bounds(prepare());nat=z[z.Prscrbr_Geo_Lvl.eq('National')].drop_duplicates(['year','source_row']);gv=nat.groupby('Gnrc_Name').agg(observed=('GE65_Tot_30day_Fills','sum'),lower=('lo','sum'),upper=('hi','sum'));gv['threshold_ambiguous']=(gv.lower<100000)&(gv.upper>=100000);gv.to_csv(BASE/'generic_threshold_bounds.csv');assert not gv.threshold_ambiguous.any()
# Complete subsets and suppression scenario summary, including each entry's membership.
pan=pd.read_csv(T/'state_age_panel_volumes.csv');comp=pan[pan.row_complete].copy();comp[['entry','state','year']].drop_duplicates().to_csv(T/'complete_published_state_years.csv',index=False)
ss=[]
for ent,g in cf[cf.term.eq('old_t')&cf.model.eq('trend')].groupby('entry'):
 ep=g[g.scenario.isin(['primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower'])];bm=g[g.scenario.eq('observed')].coefficient.iloc[0];ss.append(dict(entry=ent,main_beta=bm,endpoint_beta_min=ep.coefficient.min(),endpoint_beta_max=ep.coefficient.max(),all_four_same_sign=bool((ep.coefficient*bm>0).all()),all_four_CI_excludes0=bool((ep.ci_high<0).all() if bm<0 else (ep.ci_low>0).all()),min_pairs=ep.n_cells.min()/2,max_pairs=ep.n_cells.max()/2))
pd.DataFrame(ss).to_csv(T/'suppression_sensitivity_summary.csv',index=False)
# Preserve all existing output receipts.
before=json.loads((E/'prior_outputs_manifest.json').read_text());changed=[]
for x in before:
 p=PRE/x['path']
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256']:changed.append(x['path'])
qa=dict(prior_files_checked=len(before),prior_files_changed=changed,years=list(range(2013,2025)),official_age_denominator_rows=len(d),eligible_Table2_entries=num['n_eligible'],estimable_primary_entries=num['n_estimable'],ambiguous_generic_thresholds=int(gv.threshold_ambiguous.sum()),n_low_volume_generic_names=int((gv.observed<100000).sum()),main_FE_checked_against_paired_age_OLS=True,meta_bootstrap_seed=20261027,meta_bootstrap_reps=1000,source_scope='cached complete B files; published age-visible amounts with rule bounds; no provider A data required',python=platform.python_version())
assert not changed;(E/'validation.json').write_text(json.dumps(qa,indent=2))
def mdtab(headers,rows):
 return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rows)+'\n'
def f(x,digits=5):return 'NA' if pd.isna(x) else f'{x:.{digits}f}'
text=f'''# S2-BEERS 预检（2026-10-27）

**最终主口径：先排除全国2013–2024 ≥65合计30天量<100,000的 Gnrc_Name，再聚合表2条目。33/36项可分析；19/33（57.6%）老年组相对下降更快且95%CI不跨0。K1 PASS；K4 PASS_WITH_LIMITS（未确认触发指定撞题KILL）。本结果只支持列名药物暴露的描述性比较，不能据此称“Beers政策效应”。**

**共同分母是关键限制：主模型19项显著负向，未标准化州量仅2项显著负向。** 全国≥65参保人年增长与<65分母变化共同进入每个州的年龄交互；对完整600州年样本，分母单独贡献约−0.052675 log单位/年。州×年FE不能吸收年龄不同的这一项。州结果是按处方者所在州分解的全国年龄组标准化量，**不是州居民利用率**，也不能仅凭州聚类置信区间把共同全国时间变化解释为因果。

首轮只按药类条目门槛的结果为20/33；为落实低量“药”的排除要求，最终主口径筛除81个低量通用名后变为19/33（抗精神病药CI跨0）。所有初始结果仍保存在tables根目录作为门槛口径敏感性；最终主结果在`tables/drug_filtered/`和`figures/drug_filtered/`。没有修改既有LASU产出，已逐文件校验{len(before)}个旧文件，变化0。

## K1 可行性：PASS

理由：33个可测药物暴露条目，超过10项门槛。这里“可测”不等于能鉴定所有Beers不适当用药条件。

2023表2逐条登记36项，长效SU为嵌套参照，不计入36项或meta。筛选后的33项主模型均可估计。累计量门槛不按年份或年龄组分别筛选，固定通用名清单贯穿2013–2024；81个低量通用名均有抑制界核查，没有任何一个门槛判定区间跨100,000。通用名可包含盐型或复方，因此不是81种独立活性分子。

排除条目：ergoloid mesylates（过滤前≥65量11,429.7，规则上界11,586.8）；oral mineral oil（无匹配的已发布纯矿物油行）；systemic estrogens（不能可靠拆分系统性与阴道剂型，NOT_ESTIMABLE_ROUTE）。**未发现行不等于证实Part D不覆盖**；未给任何药物作无依据的非覆盖判定。明确非目标剂型、混合剂型以及非50州单位逐行记录。

表中抑制比例以该条目筛选后已发布州级药品行为分母；两年龄组不可回收比例相同，因为<65来自全年龄减≥65。原发*（≥65小格）与反向#（<65小格）另列CSV；它们不能都按老年小格处理。

'''
rows=[]
for _,a in k1[k1.status.eq('INCLUDED')&k1.role.eq('Table2_entry')].iterrows():rows.append([a.label,f'{a.national_ge65_fills:,.1f}',int(a.n_state_published_rows),f(a.ge65_suppressed_rows_pct,2)+'%',f(a.lt65_unrecoverable_rows_pct,2)+'%'])
text+=mdtab(['条目','全国≥65累计30天量','州级已发布行','≥65不可回收','<65不可回收'],rows)
text+='''
量是年龄可见行合计；抑制界和未发布整行的局限另见明细。州年没有发布的药品行不能自动补零，规则界也不覆盖这些完全缺失行。

## K2 单条目州面板：COMPLETE_DESCRIPTIVE

模型：`log(30天可回收量 ×1000 / 全国该年龄组参保人年) ~ old + old×(year−2013) + state×year FE`。不加药量权重。州聚类CR1采用完整FE秩修正，95%CI用t(G−1)。每个州年必须两年龄组均有正数，log(0)不加伪计数；所有删去的配对单列。数据输入、原始字段表、继承的字段映射与数值转换均保留。

β为老年组相对<65的年度log变化差；负值只表示相对下降更快，不要求老年组自身绝对下降。百分比换算为`100×(exp(β)−1)`。原始P值、BH-FDR和完整模型结果见CSV，下面95%CI未作多重校正。

'''
text+=mdtab(['条目','β log/年','95%CI','州年配对','州数'],[[a.label,f(a.coefficient),f'[{f(a.ci_low)}, {f(a.ci_high)}]',int(a.n_cells/2),int(a.n_states)] for _,a in main.sort_values(['organ','entry']).iterrows()])
text+='\n新增/扩展节点的补充模型（保留连续年龄交互，再加入old×post）：\n\n'
posts=cf[cf.term.eq('old_post')].merge(c[['entry','label']],on='entry')
text+=mdtab(['条目','节点模型','old×post','95%CI'],[[a.label,a.model,f(a.coefficient),f'[{f(a.ci_low)}, {f(a.ci_high)}]'] for _,a in posts.iterrows()])
text+='''
2023节点后只有2023、2024两个年度点；post是水平项，不是分段斜率。阿司匹林、rivaroxaban是由其他Beers表进入表2；warfarin是新增表2治疗启动标准。地高辛/抗抑郁药/Z-drugs 2015和SU2023是既有家族的范围扩展，均明确标记，不误称首次出现。长效SU2019补充模型对应加入glimepiride。

抑制处理沿用LASU v1.1：小组claims为1–10，30天量每claim上下截断1–12，宽松小组量[0,U]，U=min(120,F−max(C−10,0))；*给老年小组界，#给年轻小组界，另一组按全年龄量相减。四种端点是small lower、small upper、old lower/young upper、old upper/young lower；各自重新计算log并剔除零值配对。它们是已发布行的四种情形，不是对所有遗漏和所有可能配置的全局最优化界。

'''
trend=cf[cf.term.eq('old_t')&cf.model.eq('trend')&cf.entry.ne('long_su')]
text+=mdtab(['情形','可估计项','显著负向项','显著正向项'],[[sc,int(g.status.eq('OK').sum()),int(g.ci_high.lt(0).sum()),int(g.ci_low.gt(0).sum())] for sc,g in trend.groupby('scenario')])
text+='''
全部已发布行年龄完整可见子集仍不保证没有被整行省略的产品。条目特定的州年名单、端点配对数和排除原因均已输出。局部样本改变导致的差异不归为政策效果。

## K3 跨条目汇总：COMPLETE_DESCRIPTIVE

'''
text+=f'''显著负向19/33（57.6%），显著正向6/33（18.2%），其余8/33的95%CI跨0。REML随机效应合并β={m['pooled_beta']:.6f} log/年，常规95%CI [{m['ci_low_independence']:.6f}, {m['ci_high_independence']:.6f}]，换算约{100*np.expm1(m['pooled_beta']):.2f}%/年。τ²={m['tau2']:.6f}；I²={m['I2_pct']:.2f}%。

这些不是33项独立研究：相同参保人、复方跨条目、NSAID子条目及共同时间冲击都造成相关。常规meta CI只在独立效应假设下成立，不能视为确认性的汇总推断。以同一批州簇联合重采样1000次、固定原条目内方差的描述性bootstrap区间为[{m['state_bootstrap_low']:.6f}, {m['state_bootstrap_high']:.6f}]；它针对这组固定药物的州抽样变化，不代替常规随机药物总体区间，也不校正全国共同时间冲击。

长效SU（同样过滤低量通用名）：β={b.coefficient:.6f}，95%CI [{b.ci_low:.6f}, {b.ci_high:.6f}]，位于33项分布约第{num['long_su_percentile']:.1f}百分位（按比其β小的条目比例），正向但不显著。原LASU完整药名清单未作低量过滤的参照β={oldb.coefficient:.6f}，95%CI [{oldb.ci_low:.6f}, {oldb.ci_high:.6f}]。两者不能与v1的“长效/全部SU占比”交互混用，因为本任务改成了每千参保人年的药物用量。

森林图：[矢量PDF](figures/drug_filtered/K3_forest.pdf)、[PNG](figures/drug_filtered/K3_forest.png)。跨条目重叠行在`tables/drug_filtered/cross_entry_overlap.csv`。

## K4 撞题：PASS_WITH_LIMITS

理由：截至本次检索，确认触发“全国Part D、多药物、<65对照、评估Beers效应”四项同时成立的研究为0；这不是证明不存在。PubMed指定查询12条，另三组扩展查询合并共204篇；Google Scholar指定查询取得999条并到返回末页（接近系统上限），年龄扩展160条、精确under65查询294条到末页，共1453条记录、1375个不同标题。保留查询原文、每页原始回执、终止边界及候选裁决；扩展age查询在160条停止，不宣称全库穷尽，普通结果只作题名/摘要筛查而非全部全文审查。

确认的相关年龄对照先例：

- [Stuart等，2003](https://pubmed.ncbi.nlm.nih.gov/15555468/)：全国MCBS 1995/1999，36项药物/药类，<65残障Medicare为比较组，研究目的明确涉及区分Beers依从与一般新药替代。**概念先例明确，因早于Part D而不触发所设KILL。**
- [Donovan等，2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7669669/)：同一系统两家医院，2016–2019围术期质量改进，以<65同期患者作对照，结局包含Beers药物组合；是地方实施研究，不是全国Part D研究。

相邻研究及逐篇排除依据：

'''
lit=pd.read_csv(BASE/'K4_candidate_adjudication.csv')
text+=mdtab(['作者/年/期刊','数据与年份','<65对照','裁决'],[[f"[{a.authors.split(';')[0]} {a.year}]({a.source_url})；{a.journal}",a.data+'；'+a.data_years,a.under65_control,a.decision] for _,a in lit.iterrows()])
text+='''
Forrester会议摘要的出版社Methods预览已确认只纳入≥65岁、2015年短期新增HRM处方，故排除；没有因全文付费而推断其无对照。Lee研究评估Part D保险引入，不能当成Beers发布时间的政策研究；部分样本年份未在本地全文核定，保持UNVERIFIED。Toth的全国Part D三药类趋势及Jirón的全国多药物趋势均无<65对照模型。上述“未触发KILL”不支持把本项目的年龄对照构思宣称首创。

## 药物版本与可复现性

四份原文、2023表2页码和历史表2文本已存档。[2012原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC3571677/)、[2015原文](https://doi.org/10.1111/jgs.13702)、[2019原文](https://doi.org/10.1111/jgs.15767)、[2023原文](https://doi.org/10.1111/jgs.18372)。2012曾误取同年评论文章，现已纠正为PMC3571677；误指向的文件单独命名并未用于版本判定。

版本清单区分：四版内首次出现的家族、当前范围版本、首次任意Beers表、分子在表2被明确点名的首版。2012表示在审查窗口起点已存在，**不表示历史上首次入Beers**；此前真正首版及无法确定的分子均记UNVERIFIED。药类整体已有标准时，后来点名某分子不自动视为该分子首次被药类标准覆盖。完整药名（含复方、盐型、品牌）、每年匹配、未匹配与低量删除、剂型删除均见CSV。

'''
text+=mdtab(['2023条目','四版内表2家族首版','当前范围/扩展','状态'],[[a.label,int(a.first_Table2_family_reviewed),int(a.current_scope_version),a.status] for _,a in c[c.role.eq('Table2_entry')].iterrows()])
text+='''
主入口：`code/run_all.sh`。离线复跑直接使用已保留的匹配原始行、正式官方分母和原文回执；重新从完整B文件生成匹配可使用`code/download_B_inputs.py`再按README重建。随机种子固定，模型逐条与配对年龄差OLS数值核验。版本溯源审计不是逐条临床用药审核，未声称滑动胰岛素、PPI疗程、阿司匹林用途等条件已识别。

全部输出仅在本新目录；`evidence/validation.json`给出旧文件不变和计算核验结果。未写稿。
'''
(O/'SUMMARY.md').write_text(text)
print('report written; old outputs unchanged',len(before))
