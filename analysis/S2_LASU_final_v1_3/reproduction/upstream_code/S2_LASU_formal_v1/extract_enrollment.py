"""Extract exact published 2024 age-specific Part D enrollment, with cell provenance."""
from pathlib import Path
import json,hashlib
import openpyxl,pandas as pd
O=Path(__file__).resolve().parents[1];E=O/'evidence';T=O/'tables'
p=E/'MDCR ENROLL D_CPS_03EPD_2024.xlsx'
w=openpyxl.load_workbook(p,data_only=True)
s=w['MDCR ENROLL D 2_CPS_03EPD']
rows=list(s.values)
header=next(i for i,r in enumerate(rows) if r[0]=='Type of Plan and Demographic Characteristics')
col=rows[header].index('Total Part D Enrollees')
row=next(i for i,r in enumerate(rows) if r[0]=='65 Years and Over')
denom=float(rows[row][col]);assert denom==48439021
notes=[r[0] for r in rows if isinstance(r[0],str) and r[0].startswith('NOTE:')]
assert any('person-year' in x for x in notes)
source=next(x for x in json.load(open(E/'enrollment_catalog_selected.json')) if x['title']=='CMS Program Statistics - Medicare Part D Enrollment : 2024-01-01')
meta=dict(year=2024,age='ge65',denominator=denom,denominator_unit='enrollee person-years, accounting for months enrolled; published rounded count',sheet=s.title,cell=s.cell(row+1,col+1).coordinate,row_label=rows[row][0],column_label=rows[header][col],source_url=source['distribution'][0]['downloadURL'],source_title=source['title'],source_notes=notes,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='AVAILABLE_PERSON_YEAR_DENOMINATOR',interpretation='Annual beneficiary drug-row counts per 1000 enrollee person-years; not unique-person prevalence or incidence')
(E/'enrollment_denominator.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
pd.DataFrame(rows).to_csv(T/'A3_enrollment_demographic_sheet_raw.csv',index=False,header=False)
a=pd.read_csv(T/'A3_national_scale_2024.csv')
a['PartD_ge65_enrollee_person_years']=denom
a['beneficiary_row_counts_per_1000_enrollee_person_years']=1000*a.beneficiary_row_count_sum/denom
a.loc[a.published_drug_rows.eq(0),'beneficiary_row_counts_per_1000_enrollee_person_years']=float('nan')
a['rate_note']=meta['interpretation']
a.to_csv(T/'A3_scale_with_enrollment_2024.csv',index=False,float_format='%.12g')
print(json.dumps(meta,ensure_ascii=False,indent=2))
