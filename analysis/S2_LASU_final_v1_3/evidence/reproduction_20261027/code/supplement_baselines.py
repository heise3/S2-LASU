"""Rerun inherited BEERS baselines and their corrected descendants in isolation."""
from pathlib import Path
import sys, os, json, datetime, subprocess, hashlib, shutil, argparse
ap=argparse.ArgumentParser();ap.add_argument('--audit-dir');ap.add_argument('--source-project');ap.add_argument('--workspace');args=ap.parse_args()
AUDIT=Path(args.audit_dir or Path(__file__).resolve().parents[1]).resolve();ROOT=Path(args.source_project or AUDIT.parents[1]).resolve()
STAGE=Path(args.workspace or ROOT/'work/S2_LASU_v1_2_reproduction_20261027').resolve()
assert STAGE.parent==ROOT/'work' and STAGE != ROOT
logdir=STAGE/'logs'; env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1','MPLCONFIGDIR':str(STAGE/'work/matplotlib_cache')}
cache=STAGE/'outputs/S2_BEERS_precheck/tables/matched_published_rows.csv.gz'
# Force matching from 12 complete B files; preserve initial copied cache outside active inputs.
snapshot=AUDIT/'initial_copied_precheck_cache.csv.gz'
if not snapshot.exists():shutil.copy2(cache,snapshot)
cache.unlink(missing_ok=True)
# Verify the inherited BEERS denominator against the freshly extracted official table.
assert (STAGE/'outputs/S2_BEERS_precheck/tables/enrollment_denominators.csv').read_bytes()==(STAGE/'outputs/S2_LASU_formal_v1_1/tables/R1_enrollment_denominators.csv').read_bytes()
shutil.copy2(STAGE/'outputs/S2_LASU_formal_v1_1/tables/R1_enrollment_denominators.csv',STAGE/'outputs/S2_BEERS_precheck/tables/enrollment_denominators.csv')
commands=[
 ['outputs/S2_BEERS_precheck/code/analyze_beers.py','--filter-low-generics'],
 ['outputs/S2_LASU_BEERS_benchmark/code/analyze_benchmark.py'],
 ['outputs/S2_LASU_BEERS_benchmark/code/correct_name_collision.py'],
 ['outputs/S2_LASU_BEERS_benchmark/code/update_literature.py'],
 ['outputs/S2_LASU_formal_v1/code/build_report.py']]
ledger=[]
for i,args in enumerate(commands,9):
 rec={'step':i,'command':[sys.executable,*args],'cwd':str(STAGE),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':hashlib.sha256((STAGE/args[0]).read_bytes()).hexdigest()}
 logfile=logdir/f'{i:02d}_{Path(args[0]).name}.log';rec['log']=str(logfile.relative_to(STAGE));print('START',i,args,flush=True)
 with logfile.open('w') as f:p=subprocess.run([sys.executable,*args],cwd=STAGE,env=env,stdout=f,stderr=subprocess.STDOUT)
 rec.update(returncode=p.returncode,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());ledger.append(rec)
 (AUDIT/'supplement_execution.json').write_text(json.dumps(ledger,indent=2))
 if p.returncode:raise RuntimeError(f'Step {i} failed; see {logfile}')
 print('DONE',i,flush=True)
(AUDIT/'supplement_status.json').write_text(json.dumps({'status':'COMPLETE','steps':len(ledger)},indent=2))
