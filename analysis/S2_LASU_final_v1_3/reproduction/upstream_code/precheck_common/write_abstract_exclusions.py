from pathlib import Path
import csv
O=Path(__file__).resolve().parents[1]
notes={
'25498781':'VA+Medicare 2000–2010；SU对TZD结局/工具变量研究，摘要将SU合并，非长短效趋势。',
'41397233':'Medicare DPP4i对合并SU的工具变量研究；虽用医师偏好，但摘要无长短SU拆分趋势。',
'25573537':'单个大型MAPD支付方2009–2011；HbA1c分层患者用药，非全国处方者长短效趋势。',
'35243741':'MarketScan商业/Medicare 2015–2019临床亚组趋势；摘要SU合并，非处方者长短效。',
'26335938':'Ontario加拿大2002–2013，非美国Medicare。',
'26939711':'Ontario加拿大2004–2013，非美国Medicare。',
'28676291':'全国养老院2008–2010；SU对metformin的患者用药选择，非长短效趋势。',
'32341050':'Medicare 2007–2016死亡风险；摘要SU合并，非处方者长短效趋势。',
'38826070':'Medicare 2013–2019 CMR/PIM停药，提及glimepiride；非长短效SU趋势。',
'39746144':'Medicare 2015–2019生命末期患者趋势；摘要SU合并，长短效拆分对象是胰岛素。',
'34385345':'Clinformatics/Medicare 2013–2019首线用药趋势；摘要SU合并，非处方者长短效。',
'36282929':'全国PBM商业/Medicare2015对2019加药趋势；摘要SU合并，非处方者长短效。'}
source={x['pmid']:x for x in csv.DictReader((O/'K4_screening_ledger.csv').open())}
with (O/'K4_additional_abstract_review.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['pmid','title','review_stage','reason_not_confirmed_exact_collision','source_url'])
 for pmid,n in notes.items():w.writerow([pmid,source[pmid]['title'],'ABSTRACT_REVIEW',n,f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'])
