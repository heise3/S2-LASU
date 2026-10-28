from acquire import *
import gzip,re,threading
DRUGS=['glimepiride','glyburide','chlorpropamide','glipizide','tolbutamide','tolazamide','gliclazide','gliquidone','glibenclamide','acetohexamide','glibornuride','glisoxepide','glyclopyramide']
PAT=re.compile('|'.join(DRUGS),re.I)
LOCK=threading.Lock()
def params():
 p={'filter[su][group][conjunction]':'OR'}
 for i,drug in enumerate(DRUGS):
  p.update({f'filter[d{i}][condition][path]':'Gnrc_Name',f'filter[d{i}][condition][operator]':'CONTAINS',f'filter[d{i}][condition][value]':drug,f'filter[d{i}][condition][memberOf]':'su'})
 return p
def log(x):
 with LOCK:
  with (OUT/'evidence/request_log.jsonl').open('a') as f:f.write(json.dumps(x)+'\n')
def request(row,offset=None):
 s,y=row['source'],row['year']; p=params();endpoint='data/stats' if offset is None else 'data'
 if s=='A':
  names=sorted({x['Gnrc_Name'] for x in csv.DictReader(gzip.open(OUT/f'data/B_{y}_su.csv.gz','rt'))})
  p={'filter[su][condition][path]':'Gnrc_Name','filter[su][condition][operator]':'IN'}
  p.update({f'filter[su][condition][value][{i}]':n for i,n in enumerate(names)})
 if offset is not None:
  p.update({'size':5000,'offset':offset})
  if s=='A':p['column']=','.join(['Prscrbr_NPI','Prscrbr_State_Abrvtn','Prscrbr_Type','Brnd_Name','Gnrc_Name','Tot_Clms','Tot_30day_Fills','Tot_Benes','GE65_Sprsn_Flag','GE65_Tot_Clms','GE65_Tot_30day_Fills','GE65_Bene_Sprsn_Flag','GE65_Tot_Benes'])
 url=row['api_url'].removesuffix('data')+endpoint+'?'+urllib.parse.urlencode(p)
 path=WORK/f'raw_in/{s}_{y}_{"stats" if offset is None else offset}.json'
 b=fetch(url,path);j=json.loads(b)
 if offset is not None:
  assert isinstance(j,list);assert all(PAT.search(x['Gnrc_Name']) for x in j)
 log({'source':s,'year':y,'offset':offset,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'rows':len(j) if isinstance(j,list) else j})
 return j
def download_year(r):
 s,y=r['source'],r['year'];out=OUT/f'data/{s}_{y}_su.csv.gz'
 if out.exists(): print('CACHED',s,y,flush=True);return
 stats=request(r);n=int(stats['found_rows']);out.parent.mkdir(exist_ok=True)
 if s=='A':
  original=WORK/f'raw/{s}_{y}_stats.json'
  if not original.exists():
   fetch(r['api_url']+'/stats?'+urllib.parse.urlencode(params()),original)
  assert n==int(json.loads(original.read_text())['found_rows']),('IN_vs_regex_candidate_count',s,y,n)
 print('START',s,y,n,flush=True)
 # Four years concurrently, sequential pages within each year keeps total request concurrency bounded at four.
 got=0;seen=set();tmp=out.with_suffix('.part')
 with gzip.open(tmp,'wt') as f:
  w=None
  for off in range(0,n,5000):
   rows=request(r,off);assert len(rows)==min(5000,n-off),(s,y,off,len(rows),n)
   if w is None:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
   for x in rows:
    key=tuple(x.get(k,'') for k in (['Prscrbr_NPI','Brnd_Name','Gnrc_Name'] if s=='A' else ['Prscrbr_Geo_Lvl','Prscrbr_Geo_Desc','Brnd_Name','Gnrc_Name']))
    assert key not in seen,(s,y,'duplicate',key);seen.add(key)
   w.writerows(rows);got+=len(rows)
   if off%50000==0:print('PAGE',s,y,got,'/',n,flush=True)
 assert got==n
 tmp.rename(out)
 (OUT/f'evidence/{s}_{y}_completeness.json').write_text(json.dumps({'api_filtered_rows':n,'downloaded_rows':got,'unique_keys':len(seen),'data_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2))
 print('DONE',s,y,n,flush=True)
if __name__=='__main__':
 rows=json.loads((OUT/'evidence/source_manifest.json').read_text())
 # Complete geography first, then provider data; prioritized required K3 pairs.
 priority=[2024,2023,2015,2014]+[x for x in range(2013,2025) if x not in [2024,2023,2015,2014]]
 rows.sort(key=lambda r:(0 if r['source']=='B' else 1,priority.index(r['year'])))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(download_year,rows))
