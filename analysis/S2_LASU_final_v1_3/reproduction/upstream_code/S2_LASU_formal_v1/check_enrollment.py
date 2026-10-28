"""Read-only CMS catalog/dictionary audit; no inferred enrollment denominator."""
from pathlib import Path
import json,urllib.request,csv
O=Path(__file__).resolve().parents[1]
E=O/'evidence';E.mkdir(exist_ok=True)
def fetch(url,p):
 if p.exists():return p.read_bytes()
 with urllib.request.urlopen(url,timeout=60) as r:b=r.read()
 p.write_bytes(b);return b
cat=json.loads(fetch('https://data.cms.gov/data.json',O.parents[1]/'work/cms_catalog_formal_v1.json'))
ds=cat.get('dataset',cat) if isinstance(cat,dict) else cat
selected=[d for d in ds if ('enrollment' in d.get('title','').lower() and ('part d' in d['title'].lower() or 'monthly' in d['title'].lower())) or 'medicare program statistics' in d.get('title','').lower()]
(E/'enrollment_catalog_selected.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2))
for d in selected:
 print(d['title'],d.get('temporal'),d.get('identifier'))
 for r in d.get('distribution',[]):
  if r.get('format')=='API':
   print('API',r.get('accessURL'))
   if 'monthly enrollment' in d['title'].lower():
    u=r['accessURL']+'?size=1';b=fetch(u,E/'monthly_enrollment_actual_sample.json');print('ACTUAL FIELDS',list(json.loads(b)[0]))
url='https://data.cms.gov/sites/default/files/2025-12/Medicare%20Monthly%20Enrollment%20Data%20Dictionary.pdf'
fetch(url,E/'monthly_enrollment_dictionary.pdf')
import zipfile
for d in selected:
 if d['title']=='CMS Program Statistics - Medicare Part D Enrollment : 2024-01-01':
  url=d['distribution'][0]['downloadURL'];p=E/'PartD_enrollment_2024.zip';fetch(url,p)
  with zipfile.ZipFile(p) as z:
   print('2024 PART D FILES',z.namelist())
   for name in z.namelist():
    if not name.endswith('/') and not name.startswith('__MACOSX/'):
     (E/Path(name).name).write_bytes(z.read(name))
