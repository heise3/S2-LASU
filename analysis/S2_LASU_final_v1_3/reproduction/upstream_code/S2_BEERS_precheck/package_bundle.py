"""Create a hash manifest and portable delivery archive without old LASU outputs."""
from pathlib import Path
import hashlib,json,zipfile
O=Path(__file__).resolve().parents[1]
files=[p for p in sorted(O.rglob('*')) if p.is_file() and not any(x in p.parts for x in ['__pycache__','matplotlib_cache']) and p.name!='delivery_manifest.json']
manifest=[dict(path=str(p.relative_to(O)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
m=O/'evidence/delivery_manifest.json';m.write_text(json.dumps(manifest,indent=2));files.append(m)
z=O.parent/'S2_BEERS_precheck_delivery.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
 for p in files:out.write(p,str(Path(O.name)/p.relative_to(O)))
with zipfile.ZipFile(z) as inp:assert inp.testzip() is None
print(json.dumps(dict(files=len(files),zip=str(z.resolve()),bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest()),indent=2))
