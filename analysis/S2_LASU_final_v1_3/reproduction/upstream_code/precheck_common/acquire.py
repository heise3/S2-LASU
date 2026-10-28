"""CMS public acquisition. Python standard library; bounded parallel read-only requests."""
import csv,json,pathlib,urllib.request,urllib.parse,concurrent.futures,time,hashlib,gzip
ROOT=pathlib.Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'; WORK=ROOT/'work'
def fetch(url,path,headers=None):
 path=pathlib.Path(path)
 if path.exists(): return path.read_bytes()
 for attempt in range(4):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {'Accept-Encoding':'gzip'}),timeout=120) as r:
    b=r.read()
    if r.headers.get('Content-Encoding')=='gzip':b=gzip.decompress(b)
   path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b);return b
  except Exception:
   if attempt==3: raise
   time.sleep(2**attempt)
def catalog():
 ds=json.loads((OUT/'evidence/cms_catalog_selected.json').read_text()); rows=[]
 for d in ds:
  row={'source':'A' if 'Provider and Drug' in d['title'] else 'B','year':int(d['temporal'][0]['startDate'][:4]),'modified':d['modified'],'title':d['title']}
  for dist in d['distribution']:
   if dist['format']=='CSV':row['csv_url']=dist['downloadURL'];row['dictionary_url']=dist['describedBy']['downloadURL']
   if dist['format']=='API':row['api_url']=dist['accessURL']
  rows.append(row)
 return rows
def inspect(row):
 s,y=row['source'],row['year'];pre=f'{s}_{y}'
 b=fetch(row['csv_url'],OUT/f'evidence/{pre}_header_sample.txt',{'Range':'bytes=0-8191'})
 fields=next(csv.reader(b.decode('utf-8-sig').splitlines()))
 dd=fetch(row['dictionary_url'],OUT/f'evidence/{pre}_dictionary.json')
 sample=json.loads(fetch(row['api_url']+'?size=1',OUT/f'evidence/{pre}_api_sample.json'))
 row['fields']=fields;row['api_fields']=list(sample[0]) if isinstance(sample,list) and sample else []
 print(pre,','.join(fields),flush=True)
 return row
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: rows=list(ex.map(inspect,catalog()))
 (OUT/'evidence/source_manifest.json').write_text(json.dumps(rows,indent=2))
 with (OUT/'field_inventory.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['source','year','position','actual_field'])
  for r in rows:
   for i,k in enumerate(r['fields'],1):w.writerow([r['source'],r['year'],i,k])
