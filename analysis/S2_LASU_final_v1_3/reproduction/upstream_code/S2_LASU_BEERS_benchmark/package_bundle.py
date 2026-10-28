from pathlib import Path
import json,hashlib,zipfile
O=Path(__file__).resolve().parents[1];hist=O/'figures/frozen_inherited_not_for_use';hist.mkdir(exist_ok=True)
for p in (O/'figures').glob('within_class_share_forest_*'):p.replace(hist/p.name)
files=[p for p in sorted(O.rglob('*')) if p.is_file() and not any(x in p.parts for x in ['__pycache__','matplotlib_cache']) and p.name!='delivery_manifest.json']
m=O/'evidence/delivery_manifest.json';m.write_text(json.dumps([dict(path=str(p.relative_to(O)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],indent=2));files.append(m)
z=O.parent/'S2_LASU_BEERS_benchmark_delivery.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
 for p in files:out.write(p,str(Path(O.name)/p.relative_to(O)))
with zipfile.ZipFile(z) as check:assert check.testzip() is None
print(json.dumps(dict(files=len(files),zip=str(z.resolve()),bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest()),indent=2))
