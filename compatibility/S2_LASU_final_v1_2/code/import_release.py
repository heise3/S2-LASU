"""One-time delivery import. No models are executed; old files are read only."""
from pathlib import Path
import json,hashlib,shutil,datetime
O=Path(__file__).resolve().parents[1];P=O.parent
assert not (O/'evidence/prior_outputs_manifest.json').exists(),'Already imported'
for s in ['evidence','tables/main','tables/details/lasu_v1','tables/details/robustness_v1_1','tables/details/beers_corrected','figures','definitions','provenance','reproduction/upstream_code']:(O/s).mkdir(parents=True,exist_ok=True)
before=[dict(path=str(p.relative_to(P)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(P.rglob('*')) if p.is_file() and O not in p.parents]
(O/'evidence/prior_outputs_manifest.json').write_text(json.dumps(before,indent=2))
receipt=[]
def cp(source,dest,role='ACTIVE'):
 source=P/source;dest=O/dest;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);receipt.append(dict(source=str(source.relative_to(P)),destination=str(dest.relative_to(O)),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),role=role))
for src,dest in [('S2_LASU_formal_v1','lasu_v1'),('S2_LASU_formal_v1_1','robustness_v1_1')]:
 for p in (P/src/'tables').iterdir():
  if p.is_file():cp(str(p.relative_to(P)),f'tables/details/{dest}/{p.name}')
 for p in (P/src/'code').glob('*'):
  if p.is_file():cp(str(p.relative_to(P)),f'reproduction/upstream_code/{src}/{p.name}','SOURCE_CODE_SNAPSHOT_NOT_DIRECT_ENTRY')
 for p in (P/src/'evidence').rglob('*'):
  if p.is_file() and not any(x in p.parts for x in ['matplotlib_cache','__pycache__']):cp(str(p.relative_to(P)),f'provenance/{dest}/evidence/{p.relative_to(P/src/"evidence")}','PROVENANCE_ONLY')
 for p in (P/src).glob('*decision.json'):cp(str(p.relative_to(P)),f'provenance/{dest}/{p.name}','PROVENANCE_ONLY')
 for p in (P/src).glob('*contract*'):cp(str(p.relative_to(P)),f'provenance/{dest}/{p.name}','FROZEN_CONTRACT')
allow=['fully_corrected_three_approach_comparison.csv','corrected_all_approaches_sensitivity.csv','corrected_all_approaches_percentiles.csv','share_all_coefficients.csv','share_primary_model_panel.csv.gz','state_age_year_share_panel.csv','independent_model_checks.csv','antispasmodic_model_exclusions.csv','excluded_false_positive_names.csv','excluded_false_positive_respiratory_rows.csv.gz']
for name in allow:cp('S2_LASU_BEERS_benchmark/tables/corrected/'+name,'tables/details/beers_corrected/'+name)
for p in (P/'S2_LASU_BEERS_benchmark/code').iterdir():
 if p.is_file():cp(str(p.relative_to(P)),f'reproduction/upstream_code/S2_LASU_BEERS_benchmark/{p.name}','SOURCE_CODE_SNAPSHOT_NOT_DIRECT_ENTRY')
for name in ['therapeutic_class_map_frozen.csv','ATC_members_frozen.csv','generic_atc_matches_frozen.csv','inherited_numerator_manifest.csv']:
 cp('S2_LASU_BEERS_benchmark/tables/'+name,('definitions/'+name if name!='inherited_numerator_manifest.csv' else 'provenance/beers/inherited_numerator_manifest_AUDIT_ONLY.csv'),'FROZEN_DEFINITION' if name!='inherited_numerator_manifest.csv' else 'AUDIT_ONLY_SUPERSEDED_REGEX')
cp('S2_LASU_BEERS_benchmark/tables/numerator_names_frozen.csv','provenance/beers/numerator_names_frozen_AUDIT_ONLY.csv','AUDIT_ONLY_CONTAINS_INHERITED_FALSE_POSITIVES')
for name in ['field_mapping.csv','field_inventory.csv','matched_generic_names.csv','matched_generic_brand_names.csv']:cp(name,'definitions/LASU_'+name,'FROZEN_LASU_DEFINITION')
for p in (P/'S2_LASU_BEERS_benchmark/evidence').glob('*'):
 if p.is_file() and (p.name.startswith('ATC_') or p.name.startswith('Stuart') or p.name in ['mapping_freeze.json','initial_freeze.json','analysis_started.json','ingredient_aliases_frozen.json','corrected_decision.json','validation.json','literature_update_receipt.json']):cp(str(p.relative_to(P)),f'provenance/beers/{p.name}','AUDIT_ONLY' if p.name=='corrected_decision.json' else 'PROVENANCE_ONLY')
cp('S2_LASU_BEERS_benchmark/analysis_contract.json','provenance/beers/analysis_contract.json','FROZEN_CONTRACT')
cp('S2_LASU_BEERS_benchmark/tables/S2_LASU_literature_comparison_updated.csv','tables/main/T7_literature_comparison.csv')
figs=[('F1','national_long_acting_share','S2_LASU_formal_v1','F1_national_long_acting_share'),('F2','glimepiride_glyburide_share','S2_LASU_formal_v1','F2_glimepiride_glyburide_share'),('F3','state_age_gap_2024','S2_LASU_formal_v1','F3_state_age_gap_2024'),('F4','BEERS_within_class_benchmark','S2_LASU_BEERS_benchmark','S2_LASU_BEERS_within_class_forest')]
for num,label,src,old in figs:
 for ext in ['pdf','png']:cp(f'{src}/figures/{old}.{ext}',f'figures/{num}_{label}.{ext}')
cp('evidence/source_manifest.json','provenance/CMS_source_manifest.json','PROVENANCE_ONLY')
cp('S2_LASU_BEERS_benchmark/evidence/B_input_hashes.json','provenance/full_B_input_hashes.json','PROVENANCE_ONLY')
(O/'evidence/import_manifest.json').write_text(json.dumps(receipt,indent=2))
(O/'release.json').write_text(json.dumps(dict(version='S2_LASU_final_v1_2',date='2026-10-27',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Delivery consolidation only; no refitting, no manuscript',sources=['S2_LASU_formal_v1','S2_LASU_formal_v1_1','S2_LASU_BEERS_benchmark/tables/corrected'],beers_authority='fully corrected all-approach data only; old original-baseline comparison deprecated',source_project=str(P.parent.resolve())),indent=2))
print('Copied',len(receipt),'files; protected',len(before),'prior files')
