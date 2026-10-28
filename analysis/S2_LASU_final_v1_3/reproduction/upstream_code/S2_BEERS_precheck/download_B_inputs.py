"""Optional public CMS source acquisition. Never overwrite an existing input.
Use --verify-only to validate cached complete input files without network access.
A changed upstream file is retained as .download and raises a hash mismatch.
"""
from pathlib import Path
import argparse,hashlib,json,urllib.request,shutil
O=Path(__file__).resolve().parents[1];E=O/'evidence';ROOT=O.parents[1]
a=argparse.ArgumentParser();a.add_argument('--verify-only',action='store_true');a.add_argument('--destination',type=Path,default=ROOT/'work/full_csv');args=a.parse_args()
expected={r['year']:r for r in json.loads((E/'input_manifest.json').read_text())}
for r in json.loads((E/'CMS_B_source_manifest.json').read_text()):
 y=r['year'];p=args.destination/f'B_{y}.csv'
 if not p.exists():
  if args.verify_only:raise FileNotFoundError(p)
  p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.download')
  req=urllib.request.Request(r['csv_url'],headers={'User-Agent':'S2-BEERS public data replication'})
  with urllib.request.urlopen(req,timeout=120) as response,tmp.open('wb') as f:shutil.copyfileobj(response,f)
  assert hashlib.sha256(tmp.read_bytes()).hexdigest()==expected[y]['sha256'],f'Upstream hash changed: {y}; inspect {tmp}'
  tmp.replace(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==expected[y]['sha256'],f'Existing input mismatch: {p}'
 print(y,'SHA256 OK',flush=True)
