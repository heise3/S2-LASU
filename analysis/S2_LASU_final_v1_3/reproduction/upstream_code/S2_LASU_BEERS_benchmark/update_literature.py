from pathlib import Path
import pandas as pd,json,xml.etree.ElementTree as ET,hashlib
O=Path(__file__).resolve().parents[1];base=O.parent;T=O/'tables';E=O/'evidence'
old=pd.read_csv(base/'K4_key_studies.csv',dtype=str,keep_default_na=False);out=old.copy();r=dict.fromkeys(old.columns,'')
r.update(authors='Stuart et al.',publication_year='2003',journal='American Journal of Geriatric Pharmacotherapy',pmid='15555468',data='全国 Medicare Current Beneficiary Survey (MCBS)',data_years='1995、1999',prescriber_level='否；受益人层面',SU_split='多药物/药类，共36项；非长短效SU专门研究',design='以<65残障Medicare受益人为比较组的多药物趋势研究，区分Beers依从与一般药物替代',collision_assessment='概念先例：年龄对照、多药物趋势已存在；早于Part D，不是本项目构思首创；未触发原LASU处方者长短效趋势KILL',source_url='https://pubmed.ncbi.nlm.nih.gov/15555468/')
assert '15555468' not in old.pmid.values
out=pd.concat([out,pd.DataFrame([r])],ignore_index=True);assert out.iloc[:len(old)].equals(old);out.to_csv(T/'S2_LASU_literature_comparison_updated.csv',index=False)
for f in (base/'S2_BEERS_precheck/evidence').glob('pubmed_articles_*.xml'):
 for a in ET.fromstring(f.read_bytes()).findall('.//PubmedArticle'):
  if a.findtext('.//PMID')=='15555468':
   (E/'Stuart2003_original_pubmed.xml').write_bytes(ET.tostring(a,encoding='utf-8'));(E/'Stuart2003_original_abstract.txt').write_text('\n'.join(''.join(x.itertext()) for x in a.findall('.//AbstractText')))
assert (E/'Stuart2003_original_pubmed.xml').exists()
(E/'literature_update_receipt.json').write_text(json.dumps(dict(original_file=str(base/'K4_key_studies.csv'),original_sha256=hashlib.sha256((base/'K4_key_studies.csv').read_bytes()).hexdigest(),original_rows=len(old),rows_preserved=len(old),added_rows=1,output_rows=len(out),added_pmid='15555468',note='New version; old literature table not modified'),indent=2))
print('Literature:',len(old),'unchanged rows + Stuart2003 =',len(out))
