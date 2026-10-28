"""Read actual workbook headers/age labels; preserve year-specific cells and notes."""
from pathlib import Path
import json,hashlib
import pandas as pd,openpyxl
O=Path(__file__).resolve().parents[1];E=O/'evidence';T=O/'tables';records=[];audit=[]
for src in json.load(open(E/'enrollment_sources.json')):
    year=src['year'];found=[]
    for filename in src['files']:
        p=O/filename
        if p.suffix.lower()!='.xlsx':continue
        w=openpyxl.load_workbook(p,data_only=True)
        for s in w:
            rows=list(s.values)
            header=next((i for i,r in enumerate(rows) if 'Total Part D Enrollees' in r),None)
            old=next((i for i,r in enumerate(rows) if r[0]=='65 Years and Over'),None)
            young=next((i for i,r in enumerate(rows) if r[0]=='Under 65 Years'),None)
            if header is None or old is None:continue
            col=rows[header].index('Total Part D Enrollees')
            notes=[str(v) for r in rows for v in r if isinstance(v,str) and ('person-year' in v.lower() or v.startswith('NOTE:'))]
            assert any('person-year' in x for x in notes),(year,s.title)
            assert str(year) in ' '.join(str(v) for r in rows[:4] for v in r if v is not None)
            allrow=next(i for i,r in enumerate(rows) if r[0]=='Total');total=float(rows[allrow][col])
            pd.DataFrame(rows).to_csv(T/f'R1_enrollment_sheet_{year}.csv',index=False,header=False)
            for age,idx in [('ge65',old),('lt65',young)]:
                if idx is None:continue
                value=float(rows[idx][col]);assert value>0
                records.append(dict(year=year,age=age,enrollee_person_years=value,all_age_enrollee_person_years=total,cell=s.cell(idx+1,col+1).coordinate,row_label=rows[idx][0],column_label=rows[header][col],sheet=s.title,workbook=filename,source_url=src['url'],sha256_workbook=hashlib.sha256(p.read_bytes()).hexdigest(),denominator_unit='person-years; published rounded count'))
            found.append((p.name,s.title));audit.append(dict(year=year,files=found.copy(),notes=notes))
    assert len(found)==1,(year,found)
d=pd.DataFrame(records);assert len(d)==24 and not d.duplicated(['year','age']).any()
qa=d.groupby('year').agg(age_sum=('enrollee_person_years','sum'),published_total=('all_age_enrollee_person_years','first')).reset_index();qa['rounding_difference']=qa.age_sum-qa.published_total
assert qa.rounding_difference.abs().le(1).all()
d.to_csv(T/'R1_enrollment_denominators.csv',index=False,float_format='%.12g');qa.to_csv(T/'R1_enrollment_rounding_audit.csv',index=False)
(E/'enrollment_extraction_notes.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(d[['year','age','enrollee_person_years']].to_string(index=False))
