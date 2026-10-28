from pathlib import Path
import sys,json,hashlib,datetime
sys.dont_write_bytecode=True
import pandas as pd,numpy as np,statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster
from scipy.stats import t
O=Path(__file__).resolve().parents[1];T=O/'tables/corrected';E=O/'evidence';base=O.parent
r=pd.read_csv(T/'three_approach_results_long.csv');p=pd.read_csv(T/'share_primary_model_panel.csv.gz');checks=[]
for (entry,scale),z in p.groupby(['entry','scale']):
 w=z.pivot(index=['state','year'],columns='old',values='share_pct').reset_index();fit=sm.OLS(w[1]-w[0],sm.add_constant(w.year-2013)).fit();V=cov_cluster(fit,w.state,use_correction=False);a=r[r.entry.eq(entry)&r.approach.eq('b_share_'+scale)].iloc[0];se=np.sqrt(V[1,1]*a.CR1_factor);ci=fit.params.iloc[1]+np.array([-1,1])*t.ppf(.975,a.n_states-1)*se
 assert np.isclose(fit.params.iloc[1],a.coefficient,atol=1e-9);assert np.isclose(se,a.se,atol=1e-9);assert np.allclose(ci,[a.ci_low,a.ci_high],atol=1e-9)
 checks.append(dict(entry=entry,scale=scale,beta_abs_error=abs(fit.params.iloc[1]-a.coefficient),se_abs_error=abs(se-a.se)))
pd.DataFrame(checks).to_csv(T/'independent_model_checks.csv',index=False)
fr=json.loads((E/'mapping_freeze.json').read_text())
for x in fr['files']:assert hashlib.sha256((O/x['path']).read_bytes()).hexdigest()==x['sha256']
prior=json.loads((E/'prior_outputs_manifest.json').read_text());changed=[x['path'] for x in prior if not (base/x['path']).exists() or hashlib.sha256((base/x['path']).read_bytes()).hexdigest()!=x['sha256']];assert not changed
old=pd.read_csv(base/'K4_key_studies.csv',dtype=str,keep_default_na=False);new=pd.read_csv(O/'tables/S2_LASU_literature_comparison_updated.csv',dtype=str,keep_default_na=False);assert new.iloc[:len(old)].equals(old)
dec=json.loads((E/'corrected_decision.json').read_text());ranks=pd.read_csv(T/'benchmark_percentile_and_decision_inputs.csv');sens=pd.read_csv(T/'corrected_all_approaches_percentiles.csv');ac=pd.read_csv(T/'corrected_all_approaches_sensitivity.csv');frozen=pd.read_csv(O/'tables/three_approach_results_long.csv')
keys=['entry','approach'];cols=['coefficient','se','ci_low','ci_high'];a=frozen[frozen.entry.ne('antispasmodics')].set_index(keys)[cols].sort_index();b=ac[ac.entry.ne('antispasmodics')].set_index(keys)[cols].sort_index();assert np.allclose(a,b,atol=1e-10)
qa=dict(prior_files_checked=len(prior),prior_files_changed=changed,frozen_mapping_files_verified=len(fr['files']),share_models_independently_verified=len(checks),Table2_entries_each_approach=33,nested_LASU_benchmark_not_counted_in_reference=True,unchanged_effects_outside_corrected_entry=True,literature_old_rows_preserved=len(old),literature_added_rows=1,all_transforms_and_integrity_sensitivity_same_quartile=bool(ranks.quartile.nunique()==1 and sens.quartile.nunique()==1),decision=dec['decision'])
(E/'validation.json').write_text(json.dumps(qa,indent=2))
def tab(head,rows):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n'
labels={'a_national_denominator':'(a) 全国年龄分母：原结果','b_share_log':'(b) 同类内份额：log','b_share_logit':'(b) 同类内份额：logit','c_raw_state_volume':'(c) 州未标准化量：原结果'}
md=f'''# S2-LASU：Beers 对照基准分析（2026-10-27）

**决定：纳入 S2-LASU，作为描述性的背景参照；S2-BEERS 不作为独立论文。未写稿。**

用户已确认的判定规则：长效SU在(a)全国年龄分母、(b)同类内份额、(c)州未标准化量的33项分布中处于同一个四分位，且(b)的log、logit均须满足。正式计算前已冻结规则、治疗类别映射及匹配名单。本次四种表示均为Q4；明确药名匹配错误修正后，结论仍成立。没有用全体排序完全相同或精确名次相同替代这条门槛。

## 三口径与决定

下表严格保留用户指定的(a)/(c)原结果，(b)使用药名错误修正后的份额。β是年龄组≥65相对<65的年度变化差；不同变换的β大小不可直接横比，纳入门槛比较的是相对名次所在四分位。

'''
md+=tab(['口径','长效SU β','州聚类95%CI','百分位','四分位','显著负向项/33'],[[labels[x.approach],f'{x.benchmark_beta:.6f}',f'[{x.benchmark_ci_low:.6f}, {x.benchmark_ci_high:.6f}]',f'{x.percentile:.2f}',f'Q{int(x.quartile)}',f'{int(x.negative_significant_n)}/33 ({100*x.negative_significant_fraction:.1f}%)'] for _,x in ranks.iterrows()])
md+='''
**理由：三口径均处于Q4，log与logit均通过预设门槛，因此纳入。** Q4表示其交互项位于较正向的上四分位；这不是对指南有效性或绝对用药增长的判定。33项参考分布中包括全部SU条目；长效SU是额外高亮的第34条，不进入百分位分母。

为避免旧药名错误影响对照，另将(a)/(c)中的同一错误一并纠正。长效SU自身的系数/CI均不变，但原先一个参考条目的位置改变：

'''
md+=tab(['全口径修正敏感性','百分位','四分位','显著负向项/33'],[[labels[x.approach],f'{x.percentile:.2f}',f'Q{int(x.quartile)}',f'{int(x.negative_significant_n)}/33'] for _,x in sens.iterrows()])
md+='''
原口径和全口径修正均通过同四分位规则。后续S2-LASU只能使用本目录的修正版份额森林图；旧GI项原值不作为正确结果引用。全33项的正式三口径对照见`tables/corrected/three_approach_comparison.csv`（(a)/(c)按原结果保留，GI行有完整性提示）；全部三口径均修正的可用版本见`fully_corrected_three_approach_comparison.csv`。

## 实施与来源冻结

主量均为30天处方量，非原始处方笔数。同类内份额=目标条目量/同治疗类别总量，以州×年×年龄组计算。分母无需参保人数，不把缺失州年龄参保人年作比例估算。50州，排除DC及其他非州单位；年份2013–2024。

分母以NLM RxClass中的WHO ATC二级治疗类别为统一起点，多用途条目使用预先列明的并集；长效SU遵循LASU既有分母——全部SU（A10BB）。类别层级和范围不同，因此跨条目百分位仅提供描述性背景，不是统一临床可替代性评分。ATC类中同一产品只计一次；含目标成分的复方按整行30天量计，不拆成多个成分份额。分母保留低量产品，分子沿用既有低量过滤清单。无法从名称确定适应证、剂量、疗程时不作推断。

[NLM RxClass官方分类说明](https://lhncbc.nlm.nih.gov/RxNav/applications/RxClassIntro.html)与[成员API说明](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxClass.getClassMembers.html)为成员来源；本次ATC版本为2026_01_28，所有原始JSON及SHA256已保留。分类是回顾性固定词表，不表示每种药在2013年已上市。

'''
m=pd.read_csv(O/'tables/therapeutic_class_map_frozen.csv');cat=pd.read_csv(O/'tables/inherited_numerator_manifest.csv');mm=m.merge(cat[['entry','label']],on='entry')
md+=tab(['条目','冻结ATC分母','类别'],[[x.label,x.ATC_classes,x.denominator_label] for _,x in mm.iterrows()])
md+=f'''
冻结时刻为 `{fr['frozen_utc']}`，先读取2917个通用名进行名称匹配，未读取新份额结果。初始映射覆盖913个通用名；ATC未直接覆盖但属于冻结目标条目的产品，按预设规则并入分母以保持分子嵌套，例外逐项保留。记录的是“含ATC成分的产品集合”，不能声称是已按实际适应证分层的全部替代治疗。

模型分别为`log(share)`和`logit(share) ~ old + old×(year−2013) + 州×年FE`，不加药量权重；州聚类CR1，完整FE秩修正，t(G−1)置信区间。log要求0<份额≤1，logit要求0<份额<1；不加伪计数，同一州年两年龄组须同时可用。主分析使用年龄可见行量，四种既有抑制端点均另存CSV；完全未发布药品行未填零。条件性Beers条目仍是药物暴露代理，非已判定PIM。

百分位=100×(33项中β小于长效SU者数+0.5×并列者数)/33，边界25/50/75归入上一个四分位区间，即Q2/Q3/Q4。本次无并列。所有33项和长效SU在两种变换中均可估计，没有删条目以改善排名。

## 明确的继承错误与修正

继承正则`clidinium`缺少成分边界，误匹配`Aclidinium Bromide`、`Umeclidinium Bromide`和`Umeclidinium Brm/Vilanterol Tr`。它们不是GI解痉药；[aclidinium原始标签](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6f92cceb-a63f-4470-99b6-56179d98f10f)和[umeclidinium原始标签](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=dbb64747-1505-49d7-9a33-99dd402e96d3)确认其呼吸系统用途。

该问题在名称例外审计中、首次查看新效应估计前发现；当时程序已生成部分数值文件。因此修正被单列为实现错误修复，不称为重新完成的结果盲预注册。共删除{dec['removed_state_rows']}条误匹配州级药品行；同时从该条目分子以及因“目标药嵌套”而并入的分母中扣除。ATC治疗类别映射、纳入条目数、低量门槛、四分位规则都未改变。只有GI项系数改变，其余33条（含长效SU参照）均通过不变核验。原冻结运行完整保留在tables根目录，修正版在tables/corrected。

'''
x=frozen[frozen.entry.eq('antispasmodics')].set_index('approach');y=ac[ac.entry.eq('antispasmodics')].set_index('approach')
md+=tab(['GI项口径','错误原β','修正β','修正95%CI'],[[labels[k],f'{x.loc[k,"coefficient"]:.6f}',f'{y.loc[k,"coefficient"]:.6f}',f'[{y.loc[k,"ci_low"]:.6f}, {y.loc[k,"ci_high"]:.6f}]'] for k in labels])
md+='''
## 解释及概念先例

**65岁以下Part D人群以残障资格入保者为主，亦有ESRD等资格途径；不是一般年轻人群或病种匹配对照。交互项仅描述“年龄组间趋势差异”，不解释为Beers政策效应。** [CMS资格说明](https://www.cms.gov/medicare/enrollment-renewal/original-part-a-b)列出老年、残障及ESRD资格。研究未测量个体适应证、疾病严重度、指南采纳或其他同期冲击。

[Stuart等2003年](https://pubmed.ncbi.nlm.nih.gov/15555468/)已使用全国MCBS 1995/1999、36项药物/药类/组合和<65残障Medicare比较组，探讨老年用药变化与Beers依从及一般药物替代的关系。本项目的年龄对照构思不是首创。该文已加入新版S2-LASU文献对比表：原18行完整保留，新增1行，共19行；原始摘要XML和新增回执已保存。此前Part D处方者长短效SU趋势撞题门槛与本处概念先例是不同问题。

## 交付与核验

- 一张双面板森林图：[矢量PDF](figures/S2_LASU_BEERS_within_class_forest.pdf)、[PNG](figures/S2_LASU_BEERS_within_class_forest.png)。33项加长效SU高亮，分别标注log/logit百分位。
- 三口径原结果对照：`tables/corrected/three_approach_comparison.csv`；全口径修正版：`tables/corrected/fully_corrected_three_approach_comparison.csv`。
- 冻结治疗类别表：`tables/therapeutic_class_map_frozen.csv`；原始ATC成员和通用名匹配均单列。
- 新版S2-LASU文献对比表：`tables/S2_LASU_literature_comparison_updated.csv`。
- 可复现代码及状态回执：`code/`、`analysis_contract.json`、`evidence/mapping_freeze.json`、`evidence/corrected_decision.json`。

'''
md+=f'独立配对年龄差OLS验证了{len(checks)}个份额模型的β、SE及CI；核验{len(prior)}份既有文件，变化0。没有修改既有LASU或BEERS产出，没有撰写论文段落。\n'
(O/'SUMMARY.md').write_text(md);print(json.dumps(qa,indent=2))
