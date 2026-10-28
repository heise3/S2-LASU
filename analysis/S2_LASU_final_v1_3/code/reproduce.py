"""v1.3 frozen entry: read-only verify/preflight; complete replay into NEW directories.

Never reassemble or reseal the frozen release in place.
"""
from pathlib import Path
import sys, json, hashlib, argparse, subprocess, os, importlib.metadata
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    import pandas as pd
    import numpy as np
    manifest=json.loads((O/'MANIFEST.json').read_text())
    listed={r['path'] for r in manifest}
    actual={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}
    assert actual==listed|{'MANIFEST.json','SHA256SUMS'},'Frozen file set changed'
    for r in manifest:
        assert sha(O/r['path'])==r['sha256'],r['path']
        assert (O/r['path']).stat().st_size==r['bytes'],r['path']
    sums={}
    for line in (O/'SHA256SUMS').read_text().splitlines():
        h,p=line.split('  ',1);sums[p]=h;assert sha(O/p)==h,p
    assert set(sums)==listed|{'MANIFEST.json'}
    status=json.loads((O/'STATUS.json').read_text());release=json.loads((O/'release.json').read_text());dec=json.loads((O/'DECISIONS.json').read_text())
    assert status['version']==release['version']==dec['version']=='v1.3'
    assert status['freeze_status']=='FROZEN' and status['statistical_reproduction_status']=='PASS'
    assert status['models_refit_in_source_run'] is True and status['freeze_step_refits_models'] is False
    assert dec['statistical_reproduction_status']=='PASS' and dec['results_source']=='VERIFIED_FULL_STATISTICAL_RECOMPUTE'
    assert 'packaging_only' not in dec and 'models_refit_this_release' not in dec
    tables=list((O/'tables/main').glob('*.csv'));assert len(tables)==16
    assert len(pd.read_csv(O/'tables/main/MAIN_RESULTS.csv'))==44
    assert len(list((O/'tables/details').rglob('*.csv')))+len(list((O/'tables/details').rglob('*.csv.gz')))==100
    rank=pd.read_csv(O/'tables/main/T6c_BEERS_percentiles.csv')
    assert np.allclose(rank.percentile,[78.7878787879,84.8484848485,84.8484848485,78.7878787879]) and rank.quartile.eq(4).all()
    co=pd.read_csv(O/'tables/main/T6b_BEERS_three_approach_long.csv')
    for _,g in co.groupby('approach'):assert len(g[g.role.eq('Table2_entry')])==33 and len(g[g.entry.eq('long_su')])==1
    names=pd.read_csv(O/'definitions/BEERS_numerator_names_effective.csv')
    assert not names[names.entry.eq('antispasmodics')].Gnrc_Name.str.contains('aclidinium|umeclidinium',case=False).any()
    fig=pd.read_csv(O/'FIGURE_INDEX.csv');assert fig.figure_id.tolist()==['F1','F2','F3','F4']
    for c in ['pdf','png']:assert all((O/p).is_file() for p in fig[c])
    lit=pd.read_csv(O/'tables/main/T7_literature_comparison.csv',dtype=str);assert len(lit)==19 and lit.pmid.eq('15555468').sum()==1
    imports=json.loads((O/'evidence/import_manifest.json').read_text())
    for r in imports:
        assert sha(O/r['destination'])==r['destination_sha256'],r['destination']
        if r['role']=='VERIFIED_RECOMPUTED_RESULT':assert r['sha256']==r['destination_sha256']
    return dict(status='PASS',version='v1.3',freeze_status='FROZEN',statistical_reproduction_status='PASS',manifest_payload_files=len(manifest),sha256_entries=len(sums),main_tables=16,supporting_tables=100,main_result_rows=44,figures=4,beers_percentiles=rank.percentile.tolist(),old_file_preservation='SEE_FREEZE_RECEIPT; live source check is preflight')
def preflight(source,workspace=None,audit=None):
    source=Path(source).resolve();req=json.loads((O/'reproduction/source_requirements.json').read_text())
    for r in req:
        p=source/r['path'];assert p.is_file() and sha(p)==r['sha256'],f'Missing or changed frozen input: {p}'
    versions={}
    for line in (O/'code/requirements.txt').read_text().splitlines():
        name,wanted=line.split('==');actual=importlib.metadata.version(name);versions[name]=actual
        assert actual==wanted,f'Runtime version differs: {name} {actual}; expected {wanted}'
    if workspace or audit:
        assert workspace and audit,'Both --workspace and --audit-dir are required'
        s=Path(workspace).resolve();a=Path(audit).resolve()
        assert s!=a and s.parent==source/'work' and a.parent==source/'work','Use two NEW sibling directories under source-project/work'
        assert not s.exists() and not a.exists(),'Refusing to overwrite existing workspace/audit directory'
    return dict(status='PREFLIGHT_PASS_NOT_EXECUTED',source_files_verified=len(req),runtime_versions=versions,reference_package=str(O),complete_pipeline_steps=14,source_project=str(source))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',nargs='?',default='verify',choices=['verify','preflight','recompute']);p.add_argument('--source-project');p.add_argument('--workspace');p.add_argument('--audit-dir');p.add_argument('--dry-run',action='store_true');args=p.parse_args()
    checked=verify()
    if args.mode=='verify':print(json.dumps(checked,ensure_ascii=False,indent=2));return
    assert args.source_project,'--source-project is required for cached input access'
    pf=preflight(args.source_project,args.workspace,args.audit_dir)
    if args.mode=='preflight' or args.dry_run:print(json.dumps(pf,indent=2));return
    assert args.workspace and args.audit_dir,'Complete replay requires two new directories'
    cmd=[sys.executable,str(O/'code/completed_replay/run_reproduction.py'),'--source-project',str(Path(args.source_project).resolve()),'--workspace',str(Path(args.workspace).resolve()),'--audit-dir',str(Path(args.audit_dir).resolve()),'--reference-package',str(O)]
    subprocess.run(cmd,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'},check=True)
    result=json.loads((Path(args.audit_dir)/'REPRODUCTION_STATUS.json').read_text())
    assert result['status']=='PASS',result
    verify()
    print(json.dumps(dict(status='PASS',reference_version='v1.3',report=str(Path(args.audit_dir)/'REPRODUCTION_REPORT.md'),reference_package_unchanged=True),indent=2))
if __name__=='__main__':main()
