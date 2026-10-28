"""Complete replay entry: frozen v1.2 plus omitted baseline/view stages and audit.

Requires cached source inputs and two NEW directories under source_project/work.
"""
from pathlib import Path
import argparse,sys,os,json,hashlib,datetime,subprocess,shutil
ap=argparse.ArgumentParser();ap.add_argument('--source-project',required=True);ap.add_argument('--workspace',required=True);ap.add_argument('--audit-dir',required=True);args=ap.parse_args()
root=Path(args.source_project).resolve();stage=Path(args.workspace).resolve();audit=Path(args.audit_dir).resolve()
assert stage!=audit and stage.parent==root/'work' and audit.parent==root/'work'
assert not stage.exists() and not audit.exists(),'Both destinations must be NEW; existing results cannot be overwritten'
ref=root/'outputs/S2_LASU_final_v1_2';assert (ref/'code/reproduce.py').exists()
audit.mkdir(parents=True);(audit/'code').mkdir()
here=Path(__file__).resolve().parent
for name in ['run_reproduction.py','supplement_baselines.py','rebuild_and_compare.py','finalize_report.py']:
    shutil.copy2(here/name,audit/'code'/name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[p for p in sorted((root/'outputs').rglob('*')) if p.is_file()]+sorted((root/'work/full_csv').glob('B_*.csv'))
prior=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)) for p in paths]
(audit/'prior_files_manifest.json').write_text(json.dumps(prior,indent=2))
contract=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_project=str(root),reference_package=str(ref.relative_to(root)),isolated_workspace=str(stage),preserved_files=len(prior),table_comparison='16 canonical main CSVs plus regenerated supporting tables; schema/text/missingness exact; numeric rtol=1e-7 atol=1e-8; integer counts exact',figures='PNG pixel equality; PDF decoded content/resources and 144dpi rendered pixels; metadata separate',models='Frozen entry plus inherited BEERS baseline refits and six LASU derived tables; no statistical source edits',failure_policy='Preserve all logs and first errors; report computational failures separately from numerical differences')
(audit/'run_contract.json').write_text(json.dumps(contract,indent=2))
env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'}
commands=[('unified_entry.log',[sys.executable,str(ref/'code/reproduce.py'),'recompute','--source-project',str(root),'--workspace',str(stage)])]
for script,log in [('supplement_baselines.py','supplement.log'),('rebuild_and_compare.py','comparison.log'),('finalize_report.py','finalization.log')]:
    commands.append((log,[sys.executable,str(audit/'code'/script),'--source-project',str(root),'--workspace',str(stage),'--audit-dir',str(audit)]))
ledger=[]
for logfile,cmd in commands:
    row=dict(command=cmd,log=logfile,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());print('Running',Path(cmd[1]).name,flush=True)
    with (audit/logfile).open('w') as out:r=subprocess.run(cmd,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
    row.update(returncode=r.returncode,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());ledger.append(row)
    (audit/'entry_execution.json').write_text(json.dumps(ledger,indent=2))
    if r.returncode:
        (audit/'ENTRY_FAILURE.json').write_text(json.dumps(row,indent=2));raise SystemExit(f'Execution failed; retained evidence: {audit/logfile}')
print('Complete. Report:',audit/'REPRODUCTION_REPORT.md')
