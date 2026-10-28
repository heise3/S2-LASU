"""Targeted K4 update QA; verifies preservation instead of rerunning K0–K3."""
from pathlib import Path
import csv, hashlib, json, re
from urllib.parse import unquote

O=Path(__file__).resolve().parents[1]
H=O/'history/pre_scholar_completion'
def rows(p):
    with p.open() as f:return list(csv.DictReader(f))

preserved=[]
for line in (H/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1)
    keep=(name.startswith('data/') or (name.endswith('.csv') and name.startswith(('K0_','K1_','K2_','K3_','national_','matched_','field_'))) or name in ['matched_drug_names_review.md','annual_fields.md'])
    if keep:
        assert hashlib.sha256((O/name).read_bytes()).hexdigest()==digest,name
        preserved.append(name)
assert len(preserved)>=40
k4=json.loads((O/'K4_final_decision.json').read_text())
assert k4['status']=='PASS' and k4['exact_kill_studies']==0
assert k4['scholar_queries_completed']==3
ledger=rows(O/'K4_Scholar_screening_ledger.csv')
assert len(ledger)==k4['scholar_records']==1440
assert len({r['title_group'] for r in ledger})==1328
counts=rows(O/'K4_Scholar_query_counts.csv')
assert [int(r['actual_result_records']) for r in counts]==[340,260,840]
assert len(rows(O/'K4_key_studies.csv'))==18
assert len(rows(O/'K4_Scholar_candidate_review.csv'))==19
assert len(rows(O/'K4_screening_ledger.csv'))==205
report=(O/'S2_LASU_K0_K4_summary.md').read_text()
assert '**K4 = PASS（本轮检索）' in report
assert '**总判定：K0–K4预检完成' in report
assert '|K4|UNKNOWN_EXTERNAL|' not in report
old=(H/'S2_LASU_K0_K4_summary.md').read_text()
# Everything between the K0 and K4 sections is untouched, including all numeric tables.
section=lambda s:s[s.index('## K0：'):s.index('## K4：')]
assert section(report)==section(old)
links_checked=[]
for file in ['S2_LASU_K0_K4_summary.md','K4_search_log.md']:
    for target in re.findall(r'\]\(([^)]+)\)',(O/file).read_text()):
        if target.startswith(('http://','https://','#')):continue
        p=O/unquote(target.split('#')[0])
        assert p.exists(),(file,target)
        links_checked.append(target)
qa={'status':'PASS','review_date':'2026-10-27','type':'TARGETED_K4_UPDATE_QA','preserved_K0_K3_files':len(preserved),'preserved_paths':preserved,'K0_K3_report_sections_byte_identical':True,'scholar_records':1440,'normalized_title_groups':1328,'key_studies':18,'candidate_reviews':19,'pubmed_unique_records':205,'local_links_checked':len(links_checked),'K4_status':k4['status'],'limitations':'Checks evidence accounting, report consistency and preservation. Does not establish exhaustive literature coverage or remove provider suppression bias.'}
(O/'QA_K4_update.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
oldqa=json.loads((O/'QA_validation.json').read_text())
oldqa.update({'K4_status':k4['status'],'K4_review_date':k4['review_date'],'scholar_records':1440,'K4_update_QA':'QA_K4_update.json','data_QA_reused_unchanged':True})
(O/'QA_validation.json').write_text(json.dumps(oldqa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in qa.items() if k!='preserved_paths'},ensure_ascii=False,indent=2))
