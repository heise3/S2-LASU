"""Download official yearly Part D enrollment workbooks; preserve archive contents."""
from pathlib import Path
import json,urllib.request,zipfile,hashlib,concurrent.futures,shutil
O=Path(__file__).resolve().parents[1];V=O.parent/'S2_LASU_formal_v1';E=O/'evidence';E.mkdir(exist_ok=True)
def fetch(url,path):
    if path.exists():return path.read_bytes()
    req=urllib.request.Request(url,headers={'User-Agent':'S2-LASU public-data research'})
    with urllib.request.urlopen(req,timeout=90) as r:b=r.read()
    path.write_bytes(b);return b
catalog=json.load(open(V/'evidence/enrollment_catalog_selected.json'))
selected=[d for d in catalog if d['title'].startswith('CMS Program Statistics - Medicare Part D Enrollment :')]
def one(d):
    year=int(d['title'].split(':')[-1].strip()[:4]);folder=E/'enrollment'/str(year);folder.mkdir(parents=True,exist_ok=True)
    url=next(x['downloadURL'] for x in d['distribution'] if x.get('downloadURL'));p=folder/'official.zip'
    if year==2024 and not p.exists():shutil.copy2(V/'evidence/PartD_enrollment_2024.zip',p)
    fetch(url,p)
    files=[]
    with zipfile.ZipFile(p) as z:
        for name in z.namelist():
            if name.endswith('/') or name.startswith('__MACOSX/'):continue
            dest=folder/Path(name).name;dest.write_bytes(z.read(name));files.append(str(dest.relative_to(O)))
    print(year,files,flush=True)
    return dict(year=year,title=d['title'],url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),files=files)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    records=list(pool.map(one,selected))
(E/'enrollment_sources.json').write_text(json.dumps(sorted(records,key=lambda r:r['year']),ensure_ascii=False,indent=2)+'\n')
docs={
'legacy_prescriber_methodology.pdf':'https://www.cms.gov/files/document/part-d-prescriber-puf-methodology.pdf',
'enrollment_methodology.html':'https://data.cms.gov/resources/medicare-and-medicaid-reports-methodology',
}
for name,url in docs.items():fetch(url,E/name)
for name in ['CMS_methodology_2026.pdf','CMS_methodology_2026.txt','CMS_geography_dictionary.pdf','CMS_geography_dictionary.txt']:
    shutil.copy2(O.parent/'evidence'/name,E/name)
from pypdf import PdfReader
p=E/'legacy_prescriber_methodology.pdf'
(E/'legacy_prescriber_methodology.txt').write_text('\n'.join(page.extract_text() for page in PdfReader(p).pages))
