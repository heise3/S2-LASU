from pathlib import Path
import json,hashlib,zipfile,shutil
import pandas as pd
O=Path(__file__).resolve().parents[1];T=O/'tables';V=O.parent/'S2_LASU_formal_v1'
shutil.copy2(V/'tables/A2_excluded_geographic_units.csv',T/'R2_inherited_geographic_exclusions.csv')
records=[]
for p in sorted(T.glob('*.csv')):
    if p.name=='table_inventory.csv':continue
    d=pd.read_csv(p,header=None if p.name.startswith('R1_enrollment_sheet_') else 0)
    records.append(dict(file=p.name,rows=len(d),columns=len(d.columns),bytes=p.stat().st_size,column_names=';'.join(map(str,d.columns))))
pd.DataFrame(records).to_csv(T/'table_inventory.csv',index=False)
lines=['# CSV索引','','| CSV | 行数 | 列数 |','| --- | ---: | ---: |']
for r in records:lines.append(f'| [{r["file"]}](tables/{r["file"]}) | {r["rows"]:,} | {r["columns"]} |')
(O/'TABLE_INDEX.md').write_text('\n'.join(lines)+'\n')
files=sorted(p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(O).as_posix()+'\n' for p in files))
archive=O.parent/(O.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files+[O/'SHA256SUMS']:z.write(p,p.relative_to(O.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,files=len(files)+1,sha256=hashlib.sha256(archive.read_bytes()).hexdigest()),indent=2))
