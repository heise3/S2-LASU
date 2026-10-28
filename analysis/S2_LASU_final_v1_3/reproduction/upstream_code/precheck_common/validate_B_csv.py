from acquire import *
from download_su import PAT
import io,gzip

def check(r):
 if r['source']!='B':return
 y=r['year'];b=fetch(r['csv_url'],WORK/f'full_csv/B_{y}.csv');d=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))));su=[x for x in d if PAT.search(x['Gnrc_Name'])]
 api=list(csv.DictReader(gzip.open(OUT/f'data/B_{y}_su.csv.gz','rt')))
 keys=lambda rows:{tuple(x.get(k,'').strip() for k in ['Prscrbr_Geo_Lvl','Prscrbr_Geo_Desc','Brnd_Name','Gnrc_Name']):x for x in rows}
 a,c=keys(api),keys(su);assert set(a)==set(c),(y,len(a),len(c))
 diffs=[]
 for k in a:
  for col in a[k]:
   av=a[k][col].strip();cv=c[k][col].strip()
   if av==cv:continue
   try:
    if abs(float(av)-float(cv))<1e-6:continue
   except ValueError:pass
   diffs.append([k,col,av,cv])
 assert not diffs,(y,diffs[:3])
 result={'year':y,'full_csv_rows':len(d),'regex_matched_rows':len(su),'api_rows':len(api),'matched_keys':len(a),'value_mismatches':len(diffs),'full_csv_sha256':hashlib.sha256(b).hexdigest()}
 (OUT/f'evidence/B_{y}_CSV_API_validation.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(check,catalog()))
