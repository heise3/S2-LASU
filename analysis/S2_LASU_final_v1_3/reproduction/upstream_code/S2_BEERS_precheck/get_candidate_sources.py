from pathlib import Path
import urllib.request,urllib.parse,json,concurrent.futures,xml.etree.ElementTree as ET
E=Path(__file__).resolve().parents[1]/'evidence'
jobs={
'Lee2024.html':'https://onlinelibrary.wiley.com/doi/10.1002/hec.4766',
'Forrester_crossref.json':'https://api.crossref.org/works/10.1016/j.sapharm.2016.05.009',
'Donovan2020.xml':'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC7669669/unicode',
'Toth2022.xml':'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC8993456/unicode',
'Jiron2016.xml':'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC4843827/unicode',
'Forrester_doi.html':'https://doi.org/10.1016/j.sapharm.2016.05.009',
'Milliman2023.pdf':'https://media.milliman.com/v1/media/edge/images/millimaninc5660-milliman6442-prod27d5-0001/media/Milliman/PDFs/2023-Articles/3-28-23_Treatment-Patterns-Generalized-Anxiety-Disorder-Insomnia-Medicare-FFS.pdf'}
def get(j):
 name,url=j
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as r:b=r.read();final=r.url
  (E/name).write_bytes(b)
  if name.endswith('.xml'):(E/(name+'.txt')).write_text('\n'.join(''.join(p.itertext()) for p in ET.fromstring(b).findall('.//passage/text')))
  if name.endswith('.pdf'):
   from pypdf import PdfReader
   (E/(name+'.txt')).write_text('\n'.join(p.extract_text() for p in PdfReader(E/name).pages))
  return dict(file=name,url=url,status='OK',final_url=final)
 except Exception as ex:return dict(file=name,url=url,status='ACCESS_ERROR',error=str(ex))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:r=list(p.map(get,jobs.items()))
(E/'candidate_fetch_log.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
