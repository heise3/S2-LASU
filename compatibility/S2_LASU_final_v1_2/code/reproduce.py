"""Single delivery/reproduction entry. Default verifies, never fits or edits old outputs.
assemble: regenerate delivery views only. seal: validate+hash+zip. recompute:
optional full statistical rerun, only in a new isolated workspace; never executed
as part of the packaging-only v1.2 release.
"""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,os,shutil,zipfile
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(source_project=None,check_manifest=True):
 import pandas as pd,numpy as np
 imported=json.loads((O/'evidence/import_manifest.json').read_text());bad=[r['destination'] for r in imported if sha(O/r['destination'])!=r['sha256']];assert not bad,bad
 ac=pd.read_csv(O/'tables/main/T6b_BEERS_three_approach_long.csv');source=pd.read_csv(O/'tables/details/beers_corrected/corrected_all_approaches_sensitivity.csv');pd.testing.assert_frame_equal(ac,source,check_dtype=False,rtol=1e-10,atol=1e-10)
 ranks=pd.read_csv(O/'tables/main/T6c_BEERS_percentiles.csv');assert len(ranks)==4 and ranks.quartile.eq(4).all();assert np.allclose(ranks.percentile,[78.7878787879,84.8484848485,84.8484848485,78.7878787879])
 names=pd.read_csv(O/'definitions/BEERS_numerator_names_effective.csv');assert not names.loc[names.entry.eq('antispasmodics'),'Gnrc_Name'].str.contains('aclidinium|umeclidinium',case=False,regex=True).any()
 for app,g in ac.groupby('approach'):assert len(g[g.role.eq('Table2_entry')])==33 and len(g[g.entry.eq('long_su')])==1
 t1=pd.read_csv(O/'tables/main/T1_national_age_trends.csv');assert len(t1)==24 and not t1.duplicated(['year','age']).any()
 lit=pd.read_csv(O/'tables/main/T7_literature_comparison.csv',dtype=str);assert len(lit)==19 and lit.pmid.eq('15555468').sum()==1
 fi=pd.read_csv(O/'FIGURE_INDEX.csv');assert fi.figure_id.tolist()==['F1','F2','F3','F4']
 for col in ['pdf','png']:assert all((O/p).exists() for p in fi[col])
 assert len(list((O/'figures').glob('*.pdf')))==4 and len(list((O/'figures').glob('*.png')))==4
 assert not (O/'tables/details/beers_corrected/three_approach_comparison.csv').exists()
 manifest_checked=0
 if check_manifest and (O/'evidence/delivery_manifest.json').exists():
  mm=json.loads((O/'evidence/delivery_manifest.json').read_text());errors=[r['path'] for r in mm if not (O/r['path']).exists() or sha(O/r['path'])!=r['sha256']];assert not errors,errors;manifest_checked=len(mm)
 prior=json.loads((O/'evidence/prior_outputs_manifest.json').read_text());state='NOT_CHECKED_ORIGINAL_PROJECT_UNAVAILABLE';priorchecked=0
 project=Path(source_project or json.loads((O/'release.json').read_text())['source_project'])
 if (project/'outputs/S2_LASU_formal_v1').exists():
  errors=[r['path'] for r in prior if not (project/'outputs'/r['path']).exists() or sha(project/'outputs'/r['path'])!=r['sha256']];assert not errors,errors;state='UNCHANGED';priorchecked=len(prior)
 return dict(imported_files_verified=len(imported),delivery_hashes_verified=manifest_checked,prior_files_checked=priorchecked,prior_output_status=state,main_national_rows=24,beers_reference_entries=33,beers_transformations=4,canonical_figures=4,literature_rows=19,Stuart2003_present=True,effective_GI_names_free_of_clidinium_collision=True,beers_active_baselines_fully_corrected=True,statistical_refitting_this_release='NOT_RUN_PACKAGING_ONLY')
def model_commands(stage):
 out=stage/'outputs';v=out/'S2_LASU_formal_v1/code';r=out/'S2_LASU_formal_v1_1/code';b=out/'S2_LASU_BEERS_benchmark/code'
 return [[sys.executable,str(p)] for p in [v/'run_analysis.py',v/'extract_enrollment.py',v/'plot_figures.py',r/'extract_enrollment.py',r/'run_patch.py',b/'analyze_benchmark.py',b/'correct_name_collision.py',b/'update_literature.py']]
def recompute(args):
 source=Path(args.source_project or json.loads((O/'release.json').read_text())['source_project']).resolve();stage=Path(args.workspace).resolve() if args.workspace else None
 assert stage is not None,'--workspace must be a NEW isolated directory'
 assert stage!=source and O!=stage and O not in stage.parents and not (source/'outputs'==stage or source/'outputs' in stage.parents),'Never rerun in old outputs or inside the final package'
 assert not stage.exists(),'Workspace must not exist; no overwriting is permitted'
 validate(source_project=source)
 modules=['S2_LASU_formal_v1','S2_LASU_formal_v1_1','S2_BEERS_precheck','S2_LASU_BEERS_benchmark']
 required=[source/'outputs'/m for m in modules]+[source/'outputs/data',source/'outputs/code/analyze.py',source/'outputs/K4_key_studies.csv']+[source/f'work/full_csv/B_{y}.csv' for y in range(2013,2025)]
 assert all(p.exists() for p in required),[str(p) for p in required if not p.exists()]
 full_B=json.loads((source/'outputs/S2_LASU_BEERS_benchmark/evidence/B_input_hashes.json').read_text())
 for item in full_B:assert sha(source/item['path'])==item['sha256'],item['path']
 commands=model_commands(stage)
 if args.dry_run:
  print(json.dumps(dict(status='PREFLIGHT_OK_NOT_EXECUTED',full_B_inputs_verified=len(full_B),new_workspace=str(stage),commands=commands,old_sources_read_only=True),indent=2));return
 stage.mkdir(parents=True);(stage/'outputs').mkdir();(stage/'work/full_csv').mkdir(parents=True);(stage/'logs').mkdir()
 for mod in modules:shutil.copytree(source/'outputs'/mod,stage/'outputs'/mod,ignore=shutil.ignore_patterns('__pycache__','matplotlib_cache'))
 shutil.copytree(source/'outputs/data',stage/'outputs/data');shutil.copytree(source/'outputs/code',stage/'outputs/code',ignore=shutil.ignore_patterns('__pycache__'))
 for name in ['field_mapping.csv','field_inventory.csv','matched_generic_names.csv','matched_generic_brand_names.csv','K4_key_studies.csv']:shutil.copy2(source/'outputs'/name,stage/'outputs'/name)
 (stage/'outputs/evidence').mkdir();shutil.copy2(source/'outputs/evidence/source_manifest.json',stage/'outputs/evidence/source_manifest.json')
 for y in range(2013,2025):shutil.copy2(source/f'work/full_csv/B_{y}.csv',stage/f'work/full_csv/B_{y}.csv')
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['MPLCONFIGDIR']=str(stage/'work/matplotlib_cache')
 for i,cmd in enumerate(commands):
  with (stage/f'logs/{i+1:02d}_{Path(cmd[1]).name}.log').open('w') as log:subprocess.run(cmd,cwd=stage,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 # Compare only authoritative numerical outputs; never publish inherited bad intermediate tables.
 import pandas as pd
 comparisons=[('S2_LASU_formal_v1/tables/A2_model_coefficients.csv','tables/details/lasu_v1/A2_model_coefficients.csv'),('S2_LASU_formal_v1/tables/A4_profiles.csv','tables/details/lasu_v1/A4_profiles.csv'),('S2_LASU_formal_v1_1/tables/R1_rates_long.csv','tables/details/robustness_v1_1/R1_rates_long.csv'),('S2_LASU_formal_v1_1/tables/R2_model2_coefficients.csv','tables/details/robustness_v1_1/R2_model2_coefficients.csv'),('S2_LASU_formal_v1_1/tables/R3_model2_coefficients.csv','tables/details/robustness_v1_1/R3_model2_coefficients.csv'),('S2_LASU_BEERS_benchmark/tables/corrected/corrected_all_approaches_sensitivity.csv','tables/details/beers_corrected/corrected_all_approaches_sensitivity.csv')]
 for output,ref in comparisons:pd.testing.assert_frame_equal(pd.read_csv(stage/'outputs'/output),pd.read_csv(O/ref),check_dtype=False,rtol=1e-7,atol=1e-8)
 validate(source_project=source);(stage/'RECOMPUTE_STATUS.json').write_text(json.dumps(dict(status='COMPLETE_NUMERICALLY_MATCHED',tables_compared=len(comparisons),active_beers='outputs/S2_LASU_BEERS_benchmark/tables/corrected/corrected_all_approaches_sensitivity.csv',legacy_intermediates='DEPRECATED: inherited tables are audit intermediates only'),indent=2));print('Full statistical replay completed in',stage)
def seal(args):
 qa=validate(args.source_project,check_manifest=False);(O/'evidence/release_validation.json').write_text(json.dumps(qa,indent=2))
 files=[p for p in sorted(O.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery_manifest.json'];mm=[dict(path=str(p.relative_to(O)),size=p.stat().st_size,sha256=sha(p)) for p in files];m=O/'evidence/delivery_manifest.json';m.write_text(json.dumps(mm,indent=2));files.append(m)
 z=O.parent/'S2_LASU_final_v1_2_delivery.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for p in files:out.write(p,str(Path(O.name)/p.relative_to(O)))
 with zipfile.ZipFile(z) as check:assert check.testzip() is None
 print(json.dumps(dict(status='SEALED',files=len(files),bytes=z.stat().st_size,zip=str(z),sha256=sha(z),validation=qa),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',nargs='?',default='verify',choices=['verify','assemble','seal','recompute']);a.add_argument('--source-project');a.add_argument('--workspace');a.add_argument('--dry-run',action='store_true');args=a.parse_args()
 if args.mode=='verify':print(json.dumps(validate(args.source_project),indent=2))
 elif args.mode=='assemble':subprocess.run([sys.executable,str(O/'code/assemble.py')],check=True);print(json.dumps(validate(args.source_project,check_manifest=False),indent=2))
 elif args.mode=='seal':seal(args)
 else:recompute(args)
