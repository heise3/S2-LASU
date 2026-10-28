from acquire import *
import xml.etree.ElementTree as ET
queries={
 'Q6':'(Medicare OR "Part D") AND (sulfonylurea* OR sulphonylurea* OR glimepiride OR glyburide OR glipizide OR chlorpropamide)',
 'Q1':'"Part D" AND (glimepiride OR glyburide OR "long-acting sulfonylurea")',
 'Q2':'Beers AND sulfonylurea AND (Medicare OR trend) AND ("2023/01/01"[Date - Publication] : "2026/10/26"[Date - Publication])',
 'Q3':'prescriber AND sulfonylurea AND "older adults"',
 'Q4':'(Medicare OR "Part D") AND (sulfonylurea OR sulfonylureas OR glimepiride OR glyburide OR glipizide) AND (trend OR trends OR prescribing OR prescriber)',
 'Q5':'(Medicare OR "Part D") AND ("long-acting sulfonylurea" OR "long-acting sulfonylureas" OR "short-acting sulfonylurea" OR "short-acting sulfonylureas")'}
ids=set();logs=[]
for key,q in queries.items():
 p={'db':'pubmed','term':q,'retmode':'json','retmax':1000}
 url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'+urllib.parse.urlencode(p)
 j=json.loads(fetch(url,OUT/f'evidence/pubmed_{key}.json'));r=j['esearchresult'];ids.update(r['idlist']);logs.append({'id':key,'query':q,'count':r['count'],'url':url,'pmids':r['idlist']});print(key,r['count'],flush=True);time.sleep(.5)
(OUT/'evidence/pubmed_search_log.json').write_text(json.dumps(logs,indent=2))
url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urllib.parse.urlencode({'db':'pubmed','id':','.join(sorted(ids)),'retmode':'xml'})
b=fetch(url,OUT/'evidence/pubmed_records_expanded.xml');root=ET.fromstring(b);rows=[]
for a in root.findall('.//PubmedArticle'):
 text=lambda path:''.join(a.find(path).itertext()) if a.find(path) is not None else ''
 rows.append({'pmid':text('.//PMID'),'title':text('.//ArticleTitle'),'journal':text('.//Journal/Title'),'year':text('.//JournalIssue/PubDate/Year') or text('.//JournalIssue/PubDate/MedlineDate'),'authors':'; '.join(''.join(x.itertext()) for x in a.findall('.//Author')),'abstract':'\n'.join(''.join(x.itertext()) for x in a.findall('.//AbstractText'))})
with (OUT/'literature_screening_expanded.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('unique',len(rows),flush=True)
