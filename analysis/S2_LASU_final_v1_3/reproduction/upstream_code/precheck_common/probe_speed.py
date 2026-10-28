from acquire import *
import gzip
r=next(x for x in catalog() if x['source']=='A' and x['year']==2024)
names=sorted({x['Gnrc_Name'] for x in csv.DictReader(gzip.open(OUT/'data/B_2024_su.csv.gz','rt'))})
def run(sort):
 p=[('filter[su][condition][path]','Gnrc_Name'),('filter[su][condition][operator]','IN')]+[('filter[su][condition][value][]',n) for n in names]+[('size','5000'),('column','Prscrbr_NPI,Brnd_Name,Gnrc_Name,Tot_Clms,Tot_30day_Fills,GE65_Tot_30day_Fills')]
 if sort:p.append(('sort','Prscrbr_NPI,Brnd_Name,Gnrc_Name'))
 start=time.monotonic();u=r['api_url']+'?'+urllib.parse.urlencode(p);b=fetch(u,WORK/f'probe_in_{sort}.json');print(sort,time.monotonic()-start,len(b),len(json.loads(b)),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(run,[False,True]))
