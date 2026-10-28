from pathlib import Path
import json,urllib.request,urllib.parse,hashlib,concurrent.futures,datetime
import pandas as pd
O=Path(__file__).resolve().parents[1];E=O/'evidence';m=pd.read_csv(O/'tables/therapeutic_class_map_frozen.csv');codes=sorted(set(';'.join(m.ATC_classes).split(';')))
jobs=[('ATC_version.json','https://rxnav.nlm.nih.gov/REST/rxclass/version/ATC.json')]+[(f'ATC_{c}_members.json','https://rxnav.nlm.nih.gov/REST/rxclass/classMembers.json?'+urllib.parse.urlencode(dict(classId=c,relaSource='ATC',trans=0))) for c in codes]+[(f'ATC_{c}_label.json','https://rxnav.nlm.nih.gov/REST/rxclass/class/byId.json?classId='+c) for c in codes]
def one(job):
 name,url=job;p=E/name
 try:
  if not p.exists():
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'S2-LASU public research'}),timeout=45) as r:b=r.read()
   p.write_bytes(b)
  json.loads(p.read_text());return dict(file=name,url=url,status='OK',sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 except Exception as ex:return dict(file=name,url=url,status='ERROR',error=str(ex))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:receipts=list(pool.map(one,jobs))
(E/'ATC_fetch_log.json').write_text(json.dumps(receipts,indent=2));print('OK',sum(x['status']=='OK' for x in receipts),'of',len(receipts));print([x for x in receipts if x['status']!='OK'][:3])
