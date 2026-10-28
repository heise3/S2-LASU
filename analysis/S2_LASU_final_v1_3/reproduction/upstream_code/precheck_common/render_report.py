"""Render the completed K0–K4 audit; refuses partial A downloads."""
from pathlib import Path
import pandas as pd
import json
O=Path(__file__).resolve().parents[1]
for y in range(2013,2025):
 for s in 'AB':assert (O/f'data/{s}_{y}_su.csv.gz').exists(),(s,y)
def read(n):return pd.read_csv(O/n)
def fmt(v,n=2):return 'NA' if pd.isna(v) else f'{v:,.{n}f}'
def table(headers,rows):return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+['|'+'|'.join(str(x).replace('|','/') for x in r)+'|' for r in rows])
def link(name,label=None):return f'[{label or name}]({name})'
def span(lo,hi,n=2):
 if abs(lo-hi)<1e-8:return fmt(lo,n)
 while fmt(lo,n)==fmt(hi,n) and n<8:n+=1
 return '['+fmt(lo,n)+', '+fmt(hi,n)+']'
n=read('national_annual_primary.csv');q=read('K0_row_QA.csv');r=read('K0_recovery.csv');p=read('K3_provider_profiles.csv');sp=read('K3_specialties.csv');st=read('K3_states.csv');co=read('K3_adjacent_year_spearman.csv');co=co[co.metric=='fills30'];sl=read('K2_slopes.csv');alln=read('national_annual.csv');lit=read('K4_key_studies.csv')
a=q[q.source.eq('A')].set_index('year');b=q[(q.source=='B')&(q.level=='National')].set_index('year');ba=q[(q.source=='B')&(q.level=='all_geographies')].set_index('year');rr=r[r['class'].eq('all')].set_index('year')
x=n[n.year.eq(2024)].iloc[0];pr=p[(p.metric=='fills30')&(p.scenario=='observed')].set_index('year')
names=read('matched_generic_names.csv');brands=read('matched_generic_brand_names.csv')
name_lines=['# 逐年磺脲类药名人工核对清单','', '保留CMS实际大小写、空格和标点；A与B分别去重。CSV包含各药名对应行数。','']
for y in range(2013,2025):
 name_lines += [f'## {y}','',table(['组别','A实际Gnrc_Name','B实际Gnrc_Name'],[[cl,'；'.join(sorted(names[(names.year==y)&(names.source=='A')&(names['class']==cl)].Gnrc_Name)) or '未匹配','；'.join(sorted(names[(names.year==y)&(names.source=='B')&(names['class']==cl)].Gnrc_Name)) or '未匹配'] for cl in ['long','short','other']]),'']
name_lines += ['## ER/XL标记','',table(['年','实际Brnd_Name'],[[y,'；'.join(sorted(set(brands[(brands.year==y)&brands.glipizide_er_xl].Brnd_Name)))] for y in range(2013,2025)])]
(O/'matched_drug_names_review.md').write_text('\n'.join(name_lines)+'\n')
text=['# S2-LASU：Medicare Part D 老年人长效磺脲类 K0–K4 预检','', '数据预检日：2026-10-26；K4补核完成日：2026-10-27（America/Los_Angeles）。仅公开数据预检；未写稿。','',
'**总判定：K0–K4预检完成，未触发预设KILL。** K1全国≥65长效占比仍高于25%；K4补齐PubMed与Scholar三组查询后，在本轮检索范围内判PASS。处方者公开年龄量缺失显著，K0/K3的PASS仍仅限可见量描述，不构成完整处方者行为或选题创新性的验证。','',
table(['门','判定','关键数字／一句话理由'],[
['K0','PASS（限全国趋势；处方者覆盖受限）',f'2013–2024 共12年；2024 A 的≥65全部SU量回收 {rr.loc[2024,"recovery_lower_pct"]:.2f}%，不能当作完整全国处方者数据。'],
['K1','PASS',f'2024 ≥65长效占比 {x.ge65_share_observed_pct:.2f}%，未低于预设25%。'],
['K2','PASS（描述性可计算）',f'年龄差从2013年的{n.iloc[0].age_gap_observed_pp:.2f}升至2024年的{x.age_gap_observed_pp:.2f}个百分点。'],
['K3','PASS（仅公开可见量描述）',f'2024合格NPI {int(pr.loc[2024,"n_prescribers"]):,}；分布和相关受抑制及未发布低量行影响。'],
['K4','PASS（限本轮检索）', 'PubMed去重205篇；Scholar三式实际1,440条结果，关键表18项；核实精确KILL研究0篇。']]),'',
'K0/K2/K3 没有用户预设的数值淘汰阈值；上述 PASS 只表示所列描述可计算且一致性检查通过，不是创新性或完整处方者行为的科学验证。','',
'## 数据版本、字段与药物定义','',
'**2024 已发布，是本次目录中 A/B 共同最新年份。** 目录版本记录为2026-05-21。数据来自 [CMS Provider and Drug](https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider-and-drug) 与 [CMS Geography and Drug](https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-geography-and-drug)。固定版本URL与API见 '+link('evidence/source_manifest.json')+'。','',
'已逐年打印24张实际CSV表头，并与该版本API字段核对：当前可下载的2013–2018重发文件也采用现代字段名，不能把最初旧版字段名机械套用。[CMS方法说明](https://data.cms.gov/sites/default/files/2026-05/MUP_DPR_RY26_20260421_Methodology_508.pdf)记载2013–2019在2021年更新抑制规则、2013–2021在2024年再次更新。'+link('annual_fields.md','24张逐年字段表')+'；'+link('field_mapping.csv','逐年语义映射')+'。','',
table(['语义','实际字段（A/B共同）'],[['总处方数／30天量／受益人数','Tot_Clms / Tot_30day_Fills / Tot_Benes'],['≥65抑制标记','GE65_Sprsn_Flag；受益人数另用 GE65_Bene_Sprsn_Flag'],['≥65处方数／30天量／受益人数','GE65_Tot_Clms / GE65_Tot_30day_Fills / GE65_Tot_Benes'],['药名','Gnrc_Name / Brnd_Name'],['A处方者／专科／州','Prscrbr_NPI / Prscrbr_Type / Prscrbr_State_Abrvtn'],['B地区','Prscrbr_Geo_Lvl / Prscrbr_Geo_Desc；无处方者类型']]),'',
'药物按 Gnrc_Name 大小写不敏感正则分组：长效 glimepiride、glyburide、chlorpropamide（含组合及micronized）；短效 glipizide（含组合）；其他实际匹配 tolazamide、tolbutamide，单列但保留在全部SU分母。完整逐年清单见 '+link('matched_generic_names.csv')+'（'+link('matched_drug_names_review.md','便于人工核对的逐年表')+'），品牌与ER/XL标记见 '+link('matched_generic_brand_names.csv')+'。','',
'主指标为CMS标准化30天fills，claims敏感性包含原始处方和续配。ER/XL敏感性从SU分母排除带标记的glipizide制剂，长效分子不变；实际品牌为 Glipizide Er、Glipizide Xl、Glucotrol Xl。所有精确定义见 '+link('analysis_contract.md')+'。','',
'## K0：数据可行性','',
'以下A行数为处方者×品牌×通用名；B同时列全部地理行和National行，计算全国量只用National。抑制比例以 GE65_Sprsn_Flag 非空为分子；标记类别和缺失值明细保留在CSV。', '',
table(['年','A SU行','A≥65抑制行%','B全部／全国SU行','B全国≥65抑制行','A≥65 SU量回收%'],[[y,fmt(a.loc[y,'su_rows'],0),fmt(a.loc[y,'age65_flagged_pct']),f'{int(ba.loc[y,"su_rows"])} / {int(b.loc[y,"su_rows"])}',int(b.loc[y,'age65_flagged_rows']),span(rr.loc[y,'recovery_lower_pct'],rr.loc[y,'recovery_upper_pct'],3)] for y in range(2013,2025)]),'',
'回收率分母是B全国量；B有年龄抑制时给出保守区间。2024全部SU回收49.70%，长效回收51.43%，短效回收48.63%。B按全部PDE聚合，不是A公开行简单汇总；A的低量删行和年龄反抑制因此会造成实质性缺口。','',
'逐行计算 `<65=总量−≥65`；缺失保持缺失，不填0。下面按A全年行与B全国行分别报告缺失数（顺序为30天量／claims／受益人数）；负值是可计算差值中的检查结果。','',
table(['年','A <65缺失：量／处方／人数','B全国 <65缺失：量／处方／人数','A+B全国负值数（三指标）'],[[y,' / '.join(fmt(a.loc[y,'lt65_missing_'+k],0) for k in ['30day_Fills','Clms','Benes']),' / '.join(fmt(b.loc[y,'lt65_missing_'+k],0) for k in ['30day_Fills','Clms','Benes']),int(sum(a.loc[y,'lt65_negative_'+k]+b.loc[y,'lt65_negative_'+k] for k in ['30day_Fills','Clms','Benes']))] for y in range(2013,2025)]),'',
'受益人数只检查逐行差值，不跨药或处方者相加当作独立患者人数。每年API下载行数、服务端筛选计数与唯一键数一致；B另下载全部12年完整CSV逐字段比对，差异均为0。证据在 evidence/，原始请求日志及筛选后公开数据一并保留。'+link('K0_row_QA.csv')+'；'+link('K0_recovery.csv')+'。','',
'## K1：全国趋势','',
'量单位为百万个标准化30天fills；占比单位为%。带†年份的量为年龄已公开行之和、不是全量点估计；占比范围为容许被抑制年龄量在0至该行总量之间变化得到的界。精确数值、量上下界和空置的exact列均在CSV中。', '',
table(['年／节点','≥65 SU量','≥65长效量','≥65长效%','<65 SU量','<65长效量','<65长效%'],[[str(int(v.year))+(' ★' if v.year in [2015,2019,2023] else '')+('†' if v.age_suppressed_rows else ''),fmt(v.ge65_su_observed/1e6,4),fmt(v.ge65_long_observed/1e6,4),span(v.ge65_share_lower_pct,v.ge65_share_upper_pct,3),fmt(v.lt65_su_observed/1e6,4),fmt(v.lt65_long_observed/1e6,4),span(v.lt65_share_lower_pct,v.lt65_share_upper_pct,3)] for v in n.itertuples()]),'',
'★仅标2015/2019/2023节点，不拟合政策干预效应。2015–2021有少量全国年龄抑制行；完整名单见 '+link('national_suppressed_rows.csv')+'。区间覆盖已发布全国药品行，不能恢复完全未发布的≤10-claim药品行。','',
f'2024 ≥65全部SU量 **{x.ge65_su_observed:,.1f}**，长效量 **{x.ge65_long_observed:,.1f}**，占比 **{x.ge65_share_observed_pct:.4f}%**；预设KILL为<25%，因此K1 PASS。','',
table(['2024口径','≥65长效%','<65长效%'],[[f'{v.metric} / {v.sensitivity}',fmt(v.ge65_share_observed_pct,4),fmt(v.lt65_share_observed_pct,4)] for v in alln[alln.year.eq(2024)].itertuples()]),'',
'主分析CSV：'+link('national_annual_primary.csv')+'；含claims/ER敏感性：'+link('national_annual.csv')+'；其他SU单列：'+link('national_by_class.csv')+'。','',
'## K2：年龄梯度','',
table(['年','≥65减<65（百分点）','抑制界（百分点）'],[[int(v.year),fmt(v.age_gap_observed_pp,4),span(v.age_gap_lower_pp,v.age_gap_upper_pp,4)] for v in n.itertuples()]),'',
'年均变化主定义是2013–2024十二个年度占比对年份的未加权OLS斜率；另列首末差/11，避免把两者混称。区间是抑制范围传播，不是统计置信区间。','',
table(['指标','年龄组','OLS百分点/年','抑制界','首末差/11'],[[v.metric,v.age,fmt(v.ols_slope_pp_per_year,6),span(v.slope_lower_pp_per_year,v.slope_upper_pp_per_year,6),fmt(v.endpoint_change_divided_by_11_pp_per_year,6)] for v in sl[sl.scenario.eq('primary')].itertuples()]),'',
'两组长效份额均下降，<65下降更快，年龄差在2016–2017之间由负转正。这是份额的描述性变化，不能解释成同一患者的年龄效应。'+link('K2_slopes.csv')+'。','',
'## K3：处方者层面（≥65可见量）','',
'合格处方者至少有一条已公开≥65 SU量且合计>0。已公开年龄数据但合计为0的NPI另列在K0_row_QA.csv，不计算0/0份额。个人份额=可见长效量/可见全部SU量；受抑制的长效行不是“未开长效”。以下分位数、集中度、专科、州和跨年相关均受到该限制。','',
table(['年','≥65非缺失NPI（含零）','≥65量>0合格NPI','可见长效>0 NPI','P10','P25','中位','P75','P90','P99'],[[y,fmt(a.loc[y,'npi_any_ge65_fills_data'],0),fmt(v.n_prescribers,0),fmt(v.n_with_positive_long,0)]+[fmt(v[k]) for k in ['p10','p25','p50','p75','p90','p99']] for y,v in pr.iterrows()]),'',
'按可见长效30天量排序，人数基数为全部合格SU处方者，向上取整；量份额的主分母为A可回收长效量。附列相同前列处方者可见量占B全国长效量，便于区分两个分母。','',
table(['年','前10%人数','占A可见长效%','同一可见量占B全国长效%','前1%人数','占A可见长效%','同一可见量占B全国长效%'],[[y,fmt(v.top10_n,0),fmt(v.top10_pct_of_recovered_long),span(v.long_volume*v.top10_pct_of_recovered_long/n.loc[n.year.eq(y),'ge65_long_upper'].iloc[0],v.long_volume*v.top10_pct_of_recovered_long/n.loc[n.year.eq(y),'ge65_long_lower'].iloc[0]),fmt(v.top1_n,0),fmt(v.top1_pct_of_recovered_long),span(v.long_volume*v.top1_pct_of_recovered_long/n.loc[n.year.eq(y),'ge65_long_upper'].iloc[0],v.long_volume*v.top1_pct_of_recovered_long/n.loc[n.year.eq(y),'ge65_long_lower'].iloc[0])] for y,v in pr.iterrows()]),'',
'专科按全部可见SU30天量排序，每年列前10；占比为组内量的比值。','']
for y in [2015,2024]:
 z=sp[(sp.year==y)&(sp.metric=='fills30')&(sp.scenario=='observed')].head(10)
 text += [f'### {y}：量前10专科','',table(['专科','NPI','SU30天量','长效30天量','长效%'],[[v.specialty,fmt(v.n_prescribers,0),fmt(v.su_volume,1),fmt(v.long_volume,1),fmt(v.share_pct)] for v in z.itertuples()]),'']
text += ['### 相邻年份同一处方者的Spearman相关','', '此表为30天量；claims敏感性相关亦在CSV中。使用并列值平均秩；不把缺年补0。“完整已发布行”仅要求该NPI已经发布的SU行没有年龄缺失，仍不包含被CMS整行移除的低量药。','',table(['年对','两年合格NPI','ρ（可见量）','完整已发布行NPI','ρ（完整已发布行）'],[[f'{int(v.year_previous)}→{int(v.year_current)}',fmt(v.matched_npi,0),fmt(v.spearman_rho,4),fmt(co[(co.year_current==v.year_current)&(co.scenario=='complete_published_SU_rows')].iloc[0].matched_npi,0),fmt(co[(co.year_current==v.year_current)&(co.scenario=='complete_published_SU_rows')].iloc[0].spearman_rho,4)] for v in co[co.scenario=='observed'].itertuples()]),'', '### 州级最高／最低5州','', '基于A可见≥65量，仅比较50州；DC、领地和海外不参与排名。这不是B完整州级量的排名。','']
for y in [2015,2024]:
 z=st[(st.year==y)&(st.metric=='fills30')&(st.scenario=='observed')]
 text += [f'**{y}**','',table(['位置','州','NPI','SU30天量','长效%'],[[pos,v.state,fmt(v.n_prescribers,0),fmt(v.su_volume,1),fmt(v.share_pct)] for pos,g in [('最高5',z.head(5)),('最低5',z.tail(5).sort_values('share_pct'))] for v in g.itertuples()]),'']
text += ['### K3敏感性','',table(['年','指标／口径','NPI','中位长效%','前10%占可见长效%','前1%占可见长效%'],[[int(v.year),f'{v.metric} / {v.scenario}',fmt(v.n_prescribers,0),fmt(v.p50),fmt(v.top10_pct_of_recovered_long),fmt(v.top1_pct_of_recovered_long)] for v in p.itertuples()]),'',
'完整已发布行筛选改变了入组人群，不能视为无偏修正；可见长效>0处方者作为人数分母的集中度也保留在 '+link('K3_provider_profiles.csv')+'。其余完整表：'+link('K3_specialties.csv')+'、'+link('K3_states.csv')+'、'+link('K3_adjacent_year_spearman.csv')+'。','',
'## K4：撞题检索','',
'PubMed六式合计281次命中，去重205篇；Scholar三式分别保存340、260、840条结果记录，共1,440条、按标题机械归一后1,328个标题组（不是独立研究数）。三式均沿网页分页到达当前无下一页的空结果终点。进行了题名筛查与定向原始摘要／全文核查，没有声称所有记录全部全文评审。检索式、实际数量、估算数变动及访问历史见 '+link('K4_search_log.md')+'；题录及筛查决定见 '+link('K4_screening_ledger.csv')+'；另12篇定向摘要复核及理由见 '+link('K4_additional_abstract_review.csv')+'。','',
'下表列出本轮核实的18项关键研究，区分明确长／短分组、SU分子级拆分、同数据源但未拆分和非全国近邻。新增5项已纳入；完整Scholar结果与19条新增/复核候选分别见 [Scholar筛查台账](K4_Scholar_screening_ledger.csv) 与 [候选复核表](K4_Scholar_candidate_review.csv)。这是有检索范围边界的核实清单，不声称穷尽一切已发表研究。','',
table(['作者／年／期刊','数据／年份','长短拆分与处方者层面','是否触发KILL'],[[f'[{v.authors} ({v.publication_year})]({v.source_url})<br>{v.journal}',f'{v.data}<br>{v.data_years}',f'{v.SU_split}<br>{v.prescriber_level}',v.collision_assessment] for v in lit.itertuples()]),'',
'尤其是Landon 2018已有全国Medicare患者层面长／短效初始用药趋势；Borrelli 2024使用2020年provider-drug公开文件报告老年人长效SU总量；Sangha 2021和Hayes 2023有处方者分析但把SU合并为一类。这些限制了泛泛“首次全国趋势”的主张，但目前核实范围内没有同时满足“全国Part D＋处方者层面＋长／短效SU时间趋势”的研究。','',
'另有 [Pilla et al., JAGS 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6488408/) 使用NAMCS 2006–2015比较年龄组长效SU处方趋势，及 [NHANES 1999–2020研究](https://doi.org/10.1007/s11606-023-08067-w) 分析SU使用；均非Part D。Pilla的长效分类主要为glyburide及少量chlorpropamide，与本次含glimepiride的定义不完全相同；年龄比较本身已有先例。','',
'**K4 = PASS（本轮检索）；精确KILL研究0篇。** 新核实的Jayaweera 2020确有全国2013–2015处方者PIM率趋势，但未作长／短效SU比较；Hume 2022报告全国2016年SU单药构成，是单年住民分析；Riester只单列长效PIM；McCoy为2022单年其他降糖药采用；Herzik为区域系统。均不满足全部四项KILL条件。Scholar深分页估算数不稳定，末页估算数低于已保存记录数；结论基于实际取得结果和原始文献，不以网页估算总数推断穷尽性。此前UNKNOWN_EXTERNAL与两次人工验证中断均保留在history/和检索日志。','',
'## 可复现交付与QA','',
'分析入口：'+link('code/README.md')+'。源数据筛选文件位于 data/；源码、24个版本表头及API样本、完整性核对、12年B全文CSV校验、PubMed原始查询、题录、Scholar逐页快照和复核决定位于 code/ 与 evidence/。运行前后保留请求记录，两个中途改进传输方案的尝试记录没有删除。','',
'独立检查见 '+link('QA_validation.json')+'；本轮K4更新核验见 '+link('QA_K4_update.json')+'（41个K0–K3数据/表格/药名文件及报告数字段落与旧版逐字节一致）。交付文件SHA-256见 '+link('SHA256SUMS')+'。主表、分组表和代码的一致性通过不代表处方者抑制偏差已消除，也不构成创新性验证。']
(O/'S2_LASU_K0_K4_summary.md').write_text('\n'.join(text)+'\n')
print('Rendered S2_LASU_K0_K4_summary.md')
