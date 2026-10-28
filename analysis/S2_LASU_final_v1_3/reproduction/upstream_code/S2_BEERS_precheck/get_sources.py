from pathlib import Path
import urllib.request,urllib.parse,json,hashlib,time,concurrent.futures,xml.etree.ElementTree as ET
import pandas as pd
from pypdf import PdfReader
O=Path(__file__).resolve().parents[1];E=O/'evidence';T=O/'tables'
def fetch(url,p):
    if p.exists():return p.read_bytes()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'S2-BEERS public research'}),timeout=75) as r:b=r.read()
            p.write_bytes(b);return b
        except Exception:
            if attempt==2:raise
            time.sleep(2)
sources={
 '2023':'https://geriatrictoolkit.missouri.edu/drug/Beers-Criteria-AGS-2023.pdf',
 '2019':'https://www.hqsc.govt.nz/assets/Our-work/System-safety/Reducing-harm/Medicines/Publications-resources/Beers-Criteria-2019.pdf',
 '2015':'https://www.geriatricsuamsrioa.org/uploads/2/0/6/9/20692546/jgs_13702_rev_ev.pdf'}
def pdf(item):
    year,url=item;p=E/f'Beers_{year}.pdf'
    try:
        fetch(url,p);reader=PdfReader(p)
        (E/f'Beers_{year}.txt').write_text('\n'.join(f'\n--- PDF PAGE {i+1} ---\n'+page.extract_text(extraction_mode='layout') for i,page in enumerate(reader.pages)))
        (E/f'Beers_{year}_plain.txt').write_text('\n'.join(f'\n--- PAGE {i+1} ---\n'+page.extract_text() for i,page in enumerate(reader.pages)))
        print(year,len(reader.pages),flush=True);return dict(version=year,url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='OK')
    except Exception as exc:return dict(version=year,url=url,status='ERROR',error=str(exc))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(pdf,sources.items()))
u='https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC3571677/unicode'
b=fetch(u,E/'Beers_2012_bioc.xml');root=ET.fromstring(b)
(E/'Beers_2012.txt').write_text('\n'.join(''.join(p.itertext()) for p in root.findall('.//passage/text')))
records.append(dict(version='2012',url=u,status='OK',sha256=hashlib.sha256(b).hexdigest()))
(E/'criteria_source_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
queries={
 'main':'Beers AND ("Part D" OR Medicare) AND (trend OR "interrupted time series" OR "difference-in-differences") AND (age OR "under 65")',
 'age_control':'Beers AND ("under 65" OR "younger adults" OR "younger than 65" OR "nonelderly" OR "non-elderly" OR "age control")',
 'design':'Beers AND ("difference-in-differences" OR "interrupted time series" OR "regression discontinuity")',
 'broad':'Beers AND (Medicare OR "Part D") AND (trend OR trends OR impact OR effect)'}
ids=set();logs=[]
for key,q in queries.items():
    url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'+urllib.parse.urlencode(dict(db='pubmed',term=q,retmode='json',retmax=10000))
    j=json.loads(fetch(url,E/f'pubmed_{key}.json'))['esearchresult'];ids.update(j['idlist']);logs.append(dict(id=key,query=q,count=int(j['count']),url=url,pmids=j['idlist']));print(key,j['count'],flush=True);time.sleep(.4)
(E/'pubmed_search_log.json').write_text(json.dumps(logs,indent=2))
allarticles=[]
for start in range(0,len(ids),150):
    ii=sorted(ids)[start:start+150];url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urllib.parse.urlencode(dict(db='pubmed',id=','.join(ii),retmode='xml'))
    b=fetch(url,E/f'pubmed_articles_{start}.xml');allarticles+=ET.fromstring(b).findall('.//PubmedArticle');time.sleep(.4)
rows=[]
for a in allarticles:
    def tx(path):
        x=a.find(path);return ''.join(x.itertext()) if x is not None else ''
    rows.append(dict(pmid=tx('.//PMID'),title=tx('.//ArticleTitle'),year=tx('.//JournalIssue/PubDate/Year') or tx('.//JournalIssue/PubDate/MedlineDate'),journal=tx('.//Journal/Title'),authors='; '.join(' '.join(x.itertext()) for x in a.findall('.//Author')),abstract='\n'.join(''.join(x.itertext()) for x in a.findall('.//AbstractText')),doi=tx('.//ArticleId[@IdType="doi"]'),pmc=tx('.//ArticleId[@IdType="pmc"]')))
pd.DataFrame(rows).to_csv(T/'K4_pubmed_all_records.csv',index=False)
print('PubMed unique',len(rows))
