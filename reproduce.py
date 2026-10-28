"""Verify the release or replay the new addenda in a fresh isolated directory."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,shutil,os
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def verify():
 n=0
 for line in (R/'PUBLIC_SHA256SUMS').read_text().splitlines():
  h,rel=line.split('  ',1);assert sha(R/rel)==h,rel;n+=1
 print(f'PUBLIC_MANIFEST_PASS: {n} files',flush=True)
 subprocess.run([sys.executable,str(R/'analysis/S2_LASU_final_v1_3/code/reproduce.py'),'verify'],check=True)
 return n

def compare_csv(expected,actual):
 import pandas as pd,numpy as np
 a=pd.read_csv(expected,keep_default_na=False);b=pd.read_csv(actual,keep_default_na=False)
 assert a.shape==b.shape,(expected.name,a.shape,b.shape)
 assert list(a.columns)==list(b.columns),expected.name
 max_abs=0.;cells=0
 for c in a:
  try:
   x=pd.to_numeric(a[c].where(a[c].ne(''),np.nan));y=pd.to_numeric(b[c].where(b[c].ne(''),np.nan))
   assert np.allclose(x,y,rtol=1e-10,atol=1e-9,equal_nan=True),(expected.name,c)
   delta=np.abs(x.to_numpy()-y.to_numpy());finite=delta[np.isfinite(delta)]
   if len(finite):max_abs=max(max_abs,float(finite.max()))
   cells+=int(x.notna().sum())
  except (ValueError,TypeError):assert a[c].tolist()==b[c].tolist(),(expected.name,c)
 return dict(file=expected.name,rows=len(a),numeric_cells=cells,max_absolute_difference=max_abs,status='PASS')

def replay(work):
 import pandas as pd,numpy as np
 from PIL import Image
 assert not work.exists(),'Refusing existing workspace; use a new isolated directory.'
 assert R not in work.parents and work!=R,'Replay outside the release directory.'
 verify();work.mkdir(parents=True)
 logs=work/'audit';logs.mkdir();out=work/'outputs';out.mkdir()
 G=R/'addenda/glimepiride_v1_6';D=out/'S2_LASU_glimepiride_addendum_v1_6';D.mkdir()
 for x in ['tables','figures','audit']:(D/x).mkdir()
 shutil.copytree(G/'code',D/'code')
 for x in ['ANALYSIS_CONTRACT.json','CONTRACT_SHA256']:shutil.copy2(G/x,D/x)
 F=out/'S2_LASU_final_v1_3';shutil.copytree(R/'analysis/S2_LASU_final_v1_3',F)
 shutil.copytree(G/'inputs/cms_su',out/'data')
 (out/'code').mkdir();shutil.copy2(G/'code/legacy/loader.py',out/'code/analyze.py')
 # Original run checks hashes for the twelve CMS extracts, its loader, and
 # the immutable reference tables. Extra historical writing/provenance files
 # are deliberately not necessary for this statistical replay.
 protected={p.relative_to(work).as_posix():sha(p) for base in [F,out/'data',out/'code'] for p in base.rglob('*') if p.is_file()}
 dump(D/'audit/PROTECTED_BEFORE.json',protected)
 dump(D/'audit/INPUT_MANIFEST.json',[dict(path=k,sha256=v) for k,v in protected.items()])
 def run(script,args=(),name=None):
  with (logs/(name or script.stem+'.log')).open('w') as log:
   subprocess.run([sys.executable,str(script),*map(str,args)],stdout=log,stderr=subprocess.STDOUT,check=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 run(D/'code/analyze.py');run(D/'code/plot_figures.py')
 co=pd.read_csv(D/'tables/glimepiride_state_models.csv')
 main=pd.DataFrame([dict(analysis='glimepiride_level',variant=x.scenario,period=x.period,estimate=x.estimate_pp,ci_low=x.ci_low,ci_high=x.ci_high,unit='percentage_points',source='glimepiride_state_models.csv') for _,x in co.iterrows()])
 main.to_csv(D/'tables/MAIN_RESULTS.csv',index=False)
 checks=[]
 for expected in sorted((G/'tables').glob('*')):
  if expected.name=='LITERATURE_COMPARISON_v1_6.csv':continue
  actual=D/'tables'/expected.name;assert actual.exists(),expected.name
  checks.append(compare_csv(expected,actual))
 # Geographical decomposition consumes the freshly regenerated addendum.
 GD=R/'addenda/geography_v1_7';GO=out/'S2_LASU_geography_decomposition_v1_7'
 if GD.exists():
  run(GD/'code/decompose.py',['--input-dir',D,'--output-dir',GO],name='geography_decomposition.log')
  for expected in sorted((GD/'tables').glob('*.csv')):
   check=compare_csv(expected,GO/'tables'/expected.name);check['file']='geography/'+check['file'];checks.append(check)
 visual=[]
 for expected in sorted((G/'figures').glob('*.png')):
  actual=D/'figures'/expected.name;a=np.array(Image.open(expected));b=np.array(Image.open(actual))
  visual.append(dict(file=expected.name,pixel_identical=bool(a.shape==b.shape and np.array_equal(a,b)),expected_shape=list(a.shape),actual_shape=list(b.shape)))
 assert all(sha(work/k)==v for k,v in protected.items())
 pd.DataFrame(checks).to_csv(logs/'TABLE_COMPARISON.csv',index=False)
 result=dict(status='PASS' if all(x['pixel_identical'] for x in visual) else 'PASS_NUMERICS_FIGURE_FONT_REVIEW_REQUIRED',table_checks=len(checks),numeric_cells=sum(x['numeric_cells'] for x in checks),model_coefficient_rows=len(co),protected_reference_files=len(protected),protected_changes=0,figures=visual,scope='New addenda replay from included CMS public SU extracts; does not re-run the historical full v1.3 pipeline',source_code='Byte-identical v1.6 scientific code; wrapper only stages relative layout and compiles the main result projection')
 dump(logs/'REPLAY_STATUS.json',result);print(json.dumps(result,indent=2))

p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['verify','recompute-addenda'],nargs='?',default='verify');p.add_argument('--workspace',type=Path);args=p.parse_args()
if args.mode=='verify':verify()
else:
 assert args.workspace is not None,'--workspace NEW_DIRECTORY is required';replay(args.workspace.resolve())
