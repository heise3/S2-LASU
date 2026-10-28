from acquire import *
import gzip
url=None
for x in (OUT/'evidence/request_log.jsonl').read_text().splitlines():
 j=json.loads(x)
 if j['source']=='A' and j['year']==2024 and j['offset']==0:url=j['url']
start=time.monotonic()
with urllib.request.urlopen(urllib.request.Request(url,headers={'Accept-Encoding':'gzip'}),timeout=120) as r:
 b=r.read();print('seconds',time.monotonic()-start,'bytes',len(b),'encoding',r.headers.get('Content-Encoding'),flush=True)
 if r.headers.get('Content-Encoding')=='gzip':b=gzip.decompress(b)
 print('uncompressed',len(b),flush=True)
