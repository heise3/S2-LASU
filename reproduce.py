"""Public-release integrity check; scientific replay remains in the frozen entry."""
from pathlib import Path
import argparse,hashlib,subprocess,sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('mode',choices=['verify'],nargs='?',default='verify')
p.parse_args()
count=0
for line in (root/'PUBLIC_SHA256SUMS').read_text().splitlines():
    expected,rel=line.split('  ',1);path=root/rel
    assert path.is_file(),rel
    assert hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==expected,rel
    count+=1
print(f'PUBLIC_MANIFEST_PASS: {count} files',flush=True)
subprocess.run([sys.executable,str(root/'analysis/S2_LASU_final_v1_3/code/reproduce.py'),'verify'],check=True)
