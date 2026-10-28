from pathlib import Path
import hashlib
O=Path(__file__).resolve().parents[1]
with (O/'SHA256SUMS').open('w') as f:
 for p in sorted(O.rglob('*')):
  if p.is_file() and p.name!='SHA256SUMS' and '__pycache__' not in p.parts and not p.name.endswith('.part'):
   f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(O))+'\n')
