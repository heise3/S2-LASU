from pathlib import Path
import csv,json,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parents[1]
rows=[
('Landon et al.','2018','Journal of General Internal Medicine','29427177','全国 Medicare 20% 随机样本；FFS A/B/D','2007–2014','否；患者层面','是；long/short 明确分组','初始用药年度趋势','直接近邻；不满足处方者层面','https://pmc.ncbi.nlm.nih.gov/articles/PMC5880782/'),
('Landon et al.','2021','American Journal of Managed Care','33720673','全国 Medicare enrollment/PDE；TM 20% 样本与 MA','2015–2016','否；患者/计划层面','是；long/short 初始用药比较','TM 与 MA 的用药模式比较','直接近邻；不是处方者长短效时间趋势','https://pmc.ncbi.nlm.nih.gov/articles/PMC7967940/'),
('Alexopoulos et al.','2021','JAMA Network Open','34726745','全国 20% Medicare FFS A/B/D；低血糖急诊/住院者','2007–2017','否；患者/事件层面','是；长效转 glipizide 属降阶定义','严重低血糖后降阶比例及其趋势','直接近邻；不是总体处方者长短效占比趋势','https://pubmed.ncbi.nlm.nih.gov/34726745/'),
('Zullo et al.','2016','Journal of the American Medical Directors Association','27052559','全国 Medicare 20% A/D + MDS/OSCAR；长期养老院住民','2008–2010','否；住民层面','按 glipizide/glimepiride/glyburide 单药拆分','初始用药趋势，图2拆分 SU 单药','分子级近邻；未合并成长/短组，也非处方者层面','https://pmc.ncbi.nlm.nih.gov/articles/PMC4925288/'),
('Zhao et al.','2021（online 2020）','Kidney Medicine','33851113','全国 Medicare 5% / USRDS；CKD + T2D','2007–2016','否；患者层面','按 SU 单药拆分','CKD 人群糖尿病药物趋势','分子级近邻；非处方者长短效趋势','https://pmc.ncbi.nlm.nih.gov/articles/PMC8039422/'),
('Zullo et al.','2023（online 2022）','Journal of the American Geriatrics Society','36495141','全国 Medicare A/B/D + MDS/OSCAR；长期养老院住民','2008–2010','否；患者层面','glimepiride/glipizide/glyburide 分开','不同 SU 药物及剂量的安全性比较','分子级近邻；不是时间趋势','https://pmc.ncbi.nlm.nih.gov/articles/PMC10089954/'),
('Sklepinski et al.','2026','BMJ Open Diabetes Research & Care','41760122','Optum Labs + 全国 Medicare FFS 100%','起始 2014–2021；随访至2022','否；患者层面','glimepiride/glipizide/glyburide 分开','心血管与严重低血糖结局比较','分子级近邻；不是处方者时间趋势','https://pubmed.ncbi.nlm.nih.gov/41760122/'),
('Sklepinski et al.','2026','BMJ Open Diabetes Research & Care','42167878','commercial/MA/traditional Medicare 理赔','2014–2021','否；患者层面','glimepiride/glipizide/glyburide 分开','肾脏结局比较','分子级近邻；不是处方者时间趋势','https://pubmed.ncbi.nlm.nih.gov/42167878/'),
('Borrelli','2024','Journal of the American Geriatrics Society','38709112','Medicare Part D Provider Utilization and Payment PUF','2020','底层是 provider-drug；主要报告全国药物总量','只统计长效 SU；无短效比较','≥65 Beers PIM 横断面统计','数据源最接近；单年且不作长短效趋势，未触发 KILL','https://doi.org/10.1111/jgs.18943'),
('Fralick et al.','2020','Journal of the American Geriatrics Society','32841366','全国 Medicare Part D Prescription Drug Program dataset','2014–2018','否；公开药物聚合统计','Beers PIM 中 SU；未作完整长短效比较','PIM 用量与费用汇总','已有多年份全国 PIM 近邻；非处方者长短效趋势','https://doi.org/10.1111/jgs.16779'),
('Sangha et al.','2021','Circulation: Cardiovascular Quality and Outcomes','34779654','全国 Medicare Part D Prescriber PUF','2014–2018','是','否；SU 作为合并药物类别','SGLT2i 处方者采纳趋势，SU 为比较药类','有处方者趋势，但没有长/短效 SU 拆分','https://pmc.ncbi.nlm.nih.gov/articles/PMC9022137/'),
('Hayes et al.','2023','Journal of the American Geriatrics Society','37078149','全国 100% Medicare Part D + 处方者特征；长期养老院住民','2017–2019','是','否；SU 作为合并药物类别','SGLT2i 相对 SU 的处方者采纳趋势','有处方者趋势，但没有长/短效 SU 拆分','https://pubmed.ncbi.nlm.nih.gov/37078149/'),
('Trombetta & Heller','2019','American Health & Drug Benefits','31057695','宾夕法尼亚 PACE 药房理赔；非全国 Part D','干预2013–2014；每名处方者前后各360天','是；574 对 574','是；长效占全部 SU','学术推广干预的月度分段趋势','指标与处方者设计接近，但不是全国 Medicare/Part D','https://pmc.ncbi.nlm.nih.gov/articles/PMC6485651/'),
]
cols=['authors','publication_year','journal','pmid','data','data_years','prescriber_level','SU_split','design','collision_assessment','source_url']
with (O/'K4_key_studies.csv').open('w') as f:w=csv.writer(f);w.writerow(cols);w.writerows(rows)
# All 205 retrieved titles were screened. Retain a transparent broad triage alongside detailed selected-study assessment.
key={r[3] for r in rows}
allrows=list(csv.DictReader((O/'literature_screening_expanded.csv').open()))
for r in allrows:
 r['screen_stage']='TITLE_SCREEN_WITH_TARGETED_ABSTRACT_REVIEW'
 r['screen_decision']='KEY_STUDY_REVIEW' if r['pmid'] in key else 'NOT_IDENTIFIED_AS_EXACT_COLLISION_AT_TITLE_SCREEN'
 r['full_text_verified']='see_K4_key_studies_and_summary' if r['pmid'] in key else 'NO'
with (O/'K4_screening_ledger.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
# Complete the original 13-study table with the frozen Scholar review.
from finalize_scholar_review import finalize
finalize()
