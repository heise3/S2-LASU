from pathlib import Path
import hashlib,zipfile,json
import pandas as pd
O=Path(__file__).resolve().parents[1]
inventory=[]
for p in sorted((O/'tables').iterdir()):
    if p.name=='table_inventory.csv' or not (p.name.endswith('.csv') or p.name.endswith('.csv.gz')):continue
    # The enrollment sheet is an intentionally headerless preservation of Excel rows.
    d=pd.read_csv(p,header=None if p.name=='A3_enrollment_demographic_sheet_raw.csv' else 0)
    inventory.append(dict(file=p.name,rows=len(d),columns=len(d.columns),bytes=p.stat().st_size,column_names=';'.join(map(str,d.columns))))
pd.DataFrame(inventory).to_csv(O/'tables/table_inventory.csv',index=False)
index=['# CSV索引','', '压缩文件可直接用 pandas.read_csv 读取；空表保留表头表示没有该类排除记录。', '', '| CSV | 行数 | 列数 |','| --- | ---: | ---: |']
for r in inventory:index.append(f'| [{r["file"]}](tables/{r["file"]}) | {r["rows"]:,} | {r["columns"]} |')
(O/'TABLE_INDEX.md').write_text('\n'.join(index)+'\n')
def eligible(p):return p.is_file() and '__pycache__' not in p.parts and 'matplotlib_cache' not in p.parts and p.name!='SHA256SUMS'
paths=sorted(p for p in O.rglob('*') if eligible(p))
(O/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(O).as_posix()+'\n' for p in paths))
dest=O.parent/'S2_LASU_formal_v1.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in paths+[O/'SHA256SUMS']:z.write(p,p.relative_to(O.parent))
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(json.dumps(dict(archive=str(dest),bytes=dest.stat().st_size,files=len(paths)+1,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),indent=2))
