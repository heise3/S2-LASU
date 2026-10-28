"""Assemble only regenerated statistical products and compare to frozen v1.2.

No reference data are used for estimation. Old files are read-only.
"""
from pathlib import Path
import sys, os, json, hashlib, shutil, subprocess, datetime, platform, importlib.metadata, argparse
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
from PIL import Image
from pypdf import PdfReader
import pypdfium2 as pdfium
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster
from scipy.stats import t

ap=argparse.ArgumentParser();ap.add_argument('--audit-dir');ap.add_argument('--source-project');ap.add_argument('--workspace');args=ap.parse_args()
A = Path(args.audit_dir or Path(__file__).resolve().parents[1]).resolve()
ROOT = Path(args.source_project or A.parents[1]).resolve()
S = Path(args.workspace or ROOT/'work/S2_LASU_v1_2_reproduction_20261027').resolve()
REF = ROOT/'outputs/S2_LASU_final_v1_2'
NEW = S/'rebuilt_v1_2'
V = S/'outputs/S2_LASU_formal_v1/tables'
R = S/'outputs/S2_LASU_formal_v1_1/tables'
B = S/'outputs/S2_LASU_BEERS_benchmark/tables/corrected'
contract = json.loads((A/'run_contract.json').read_text())
started = datetime.datetime.fromisoformat(contract['started_utc']).timestamp()
assert json.loads((A/'supplement_status.json').read_text())['status'] == 'COMPLETE'
assert json.loads((S/'RECOMPUTE_STATUS.json').read_text())['status'] == 'COMPLETE_NUMERICALLY_MATCHED'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(d, name): pd.DataFrame(d).to_csv(A/name,index=False)
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

# Re-run independent paired-age checks instead of promoting copied old QA tables.
checks=[]
p=pd.read_csv(B/'share_primary_model_panel.csv.gz')
ac=pd.read_csv(B/'corrected_all_approaches_sensitivity.csv')
for (entry,scale),z in p.groupby(['entry','scale']):
    w=z.pivot(index=['state','year'],columns='old',values='share_pct').reset_index()
    fit=sm.OLS(w[1]-w[0],sm.add_constant(w.year-2013)).fit()
    a=ac[ac.entry.eq(entry)&ac.approach.eq('b_share_'+scale)].iloc[0]
    se=np.sqrt(cov_cluster(fit,w.state,use_correction=False)[1,1]*a.CR1_factor)
    ci=fit.params.iloc[1]+np.array([-1,1])*t.ppf(.975,a.n_states-1)*se
    assert np.isclose(fit.params.iloc[1],a.coefficient,atol=1e-9)
    assert np.isclose(se,a.se,atol=1e-9) and np.allclose(ci,[a.ci_low,a.ci_high],atol=1e-9)
    checks.append(dict(entry=entry,scale=scale,beta_abs_error=abs(fit.params.iloc[1]-a.coefficient),se_abs_error=abs(se-a.se)))
pd.DataFrame(checks).to_csv(B/'independent_model_checks.csv',index=False)
save(checks,'independent_BEERS_68_models.csv')
paired=[]
def pair_check(d,label,row):
    x=d.pivot(index=['state','year'],columns='old',values=['share_pct','su_observed'])
    gap=x['share_pct'][1]-x['share_pct'][0]
    w=x['su_observed'][1]*x['su_observed'][0]/(x['su_observed'][1]+x['su_observed'][0])
    time=x.index.get_level_values('year').to_numpy()-2013
    fit=sm.WLS(gap,sm.add_constant(time),weights=w).fit()
    g=x.index.get_level_values('state');G=len(set(g));n=len(x)
    cv=cov_cluster(fit,g,use_correction=False)*G/(G-1)*(2*n-1)/(n-2)
    se=np.sqrt(cv[1,1]);b=float(fit.params.iloc[1]);lo=b-t.ppf(.975,G-1)*se;hi=b+t.ppf(.975,G-1)*se
    assert np.allclose([b,se,lo,hi],[row.coefficient,row.se,row.ci_low,row.ci_high],atol=1e-8)
    paired.append(dict(scenario=label,independent_coefficient=b,independent_se=se,independent_ci_low=lo,independent_ci_high=hi,beta_abs_error=abs(b-row.coefficient),se_abs_error=abs(se-row.se),n_state_years=n,n_states=G))
co=pd.read_csv(R/'R2_model2_coefficients.csv')
for scenario,d in pd.read_csv(R/'R2_endpoint_panels.csv').groupby('scenario'):
    pair_check(d,scenario,co[co.scenario.eq(scenario)&co.term.eq('old_t')].iloc[0])
pair_check(pd.read_csv(R/'R2_complete_state_year_age_panel.csv'),'complete_subset',co[co.scenario.eq('complete_published_state_years')&co.term.eq('old_t')].iloc[0])
c3=pd.read_csv(R/'R3_model2_coefficients.csv')
for definition,d in pd.read_csv(R/'R3_state_age_panels.csv').groupby('definition'):
    pair_check(d,definition,c3[c3.definition.eq(definition)&c3.term.eq('old_t')].iloc[0])
pd.DataFrame(paired).to_csv(R/'independent_paired_model_checks.csv',index=False,float_format='%.12g')
save(paired,'independent_LASU_10_models.csv')

# A fresh view directory; reference main tables are NEVER copied into it.
NEW.mkdir(exist_ok=False)
for sub in ['code','tables/main','tables/details','definitions','provenance/beers','figures']:
    (NEW/sub).mkdir(parents=True,exist_ok=True)
shutil.copy2(REF/'code/assemble.py',NEW/'code/assemble.py')
sources=[]
for group,source in [('lasu_v1',V),('robustness_v1_1',R),('beers_corrected',B)]:
    dest=NEW/'tables/details'/group;dest.mkdir()
    for old in sorted((REF/'tables/details'/group).glob('*')):
        if old.name=='table_inventory.csv': continue # historical packaging metadata
        p=source/old.name
        assert p.is_file(),p
        # Geographic exclusions are a static, deliberately inherited record.
        static=p.name=='R2_inherited_geographic_exclusions.csv'
        fresh=p.stat().st_mtime>=started
        assert fresh or static, f'Unregenerated statistical source: {p}'
        shutil.copy2(p,dest/p.name)
        sources.append(dict(source=str(p.relative_to(S)),destination=str((dest/p.name).relative_to(NEW)),sha256=sha(p),generated_after_run_start=fresh,classification='static_inherited_geography' if static else 'recomputed'))
for name in ['inherited_numerator_manifest_AUDIT_ONLY.csv','numerator_names_frozen_AUDIT_ONLY.csv']:
    shutil.copy2(REF/'provenance/beers'/name,NEW/'provenance/beers'/name)
lit=S/'outputs/S2_LASU_BEERS_benchmark/tables/S2_LASU_literature_comparison_updated.csv'
assert lit.stat().st_mtime>=started
shutil.copy2(lit,NEW/'tables/main/T7_literature_comparison.csv')
fi=pd.read_csv(REF/'FIGURE_INDEX.csv')
for _,f in fi.iterrows():
    for ext in ['pdf','png']:
        src=S/'outputs/S2_LASU_formal_v1/figures'/Path(f[ext]).name if f.figure_id!='F4' else S/f'outputs/S2_LASU_BEERS_benchmark/figures/S2_LASU_BEERS_within_class_forest.{ext}'
        assert src.stat().st_mtime>=started
        shutil.copy2(src,NEW/f[ext])
with (S/'logs/14_assemble_views.log').open('w') as log:
    subprocess.run([sys.executable,str(NEW/'code/assemble.py')],cwd=S,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'},stdout=log,stderr=subprocess.STDOUT,check=True)
save(sources,'regenerated_source_ledger.csv')

diffs=[];table_checks=[]
def diff(scope,artifact,kind,row='',column='',reference='',rerun='',material=True):
    diffs.append(dict(scope=scope,artifact=artifact,difference_type=kind,row=row,column=column,reference=reference,rerun=rerun,material=material))
def compare_csv(old,new,scope):
    x=pd.read_csv(old);y=pd.read_csv(new);name=str(old.relative_to(REF)) if old.is_relative_to(REF) else old.name
    r=dict(scope=scope,artifact=name,rows_reference=len(x),rows_rerun=len(y),columns_reference=len(x.columns),columns_rerun=len(y.columns),byte_equal=sha(old)==sha(new),numeric_unequal_cells=0,numeric_outside_tolerance=0,text_or_missingness_differences=0,max_abs_numeric_difference=0.,status='PASS')
    if x.columns.tolist()!=y.columns.tolist() or x.shape!=y.shape:
        r['status']='FAIL';diff(scope,name,'SCHEMA_OR_SHAPE',reference=f'{x.shape}:{list(x.columns)}',rerun=f'{y.shape}:{list(y.columns)}')
    else:
        for c in x:
            a=x[c];b=y[c];missing=a.isna()!=b.isna()
            for idx in np.flatnonzero(missing):diff(scope,name,'MISSINGNESS',int(idx)+2,c,a.iloc[idx],b.iloc[idx])
            r['text_or_missingness_differences']+=int(missing.sum())
            valid=a.notna()&b.notna()
            if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(a):
                av=a[valid].to_numpy(dtype=float);bv=b[valid].to_numpy(dtype=float)
                exact=av==bv
                close=np.isclose(av,bv,rtol=1e-7,atol=1e-8,equal_nan=True)
                if pd.api.types.is_integer_dtype(a) and pd.api.types.is_integer_dtype(b):close=exact
                r['numeric_unequal_cells']+=int((~exact).sum());r['numeric_outside_tolerance']+=int((~close).sum())
                finite=np.isfinite(av)&np.isfinite(bv)
                if finite.any():r['max_abs_numeric_difference']=max(r['max_abs_numeric_difference'],float(np.max(np.abs(av[finite]-bv[finite]))))
                for j in np.flatnonzero(~exact):
                    idx=a[valid].index[j];diff(scope,name,'NUMERIC_OUTSIDE_TOLERANCE' if not close[j] else 'NUMERIC_WITHIN_TOLERANCE',int(idx)+2,c,av[j],bv[j],not bool(close[j]))
            else:
                bad=valid&(a.astype(str)!=b.astype(str));r['text_or_missingness_differences']+=int(bad.sum())
                for idx in np.flatnonzero(bad):diff(scope,name,'TEXT_OR_BOOLEAN',int(idx)+2,c,a.iloc[idx],b.iloc[idx])
        if r['numeric_outside_tolerance'] or r['text_or_missingness_differences']:r['status']='FAIL'
    if not r['byte_equal'] and r['status']=='PASS' and r['numeric_unequal_cells']==0:
        diff(scope,name,'SERIALIZATION_OR_COMPRESSION_ONLY',reference=sha(old),rerun=sha(new),material=False)
    table_checks.append(r)
for p in sorted((REF/'tables/main').glob('*.csv')):compare_csv(p,NEW/'tables/main'/p.name,'main')
assert len([r for r in table_checks if r['scope']=='main'])==16
for p in sorted((NEW/'tables/details').rglob('*')):
    if p.is_file():compare_csv(REF/p.relative_to(NEW),p,'supporting_statistical_tables')
save(table_checks,'table_comparison.csv')

# Independently calculate ranks from newly fitted all-approach coefficients.
rank_checks=[]
oldr=pd.read_csv(REF/'tables/main/T6c_BEERS_percentiles.csv')
for approach,g in ac.groupby('approach'):
    pool=g[g.role.eq('Table2_entry')];su=g[g.entry.eq('long_su')].iloc[0]
    assert len(pool)==33 and len(g)==34
    below=int((pool.coefficient<su.coefficient).sum());ties=int((pool.coefficient==su.coefficient).sum())
    percentile=100*below/33;quartile=min(4,int(percentile//25)+1)
    old=oldr[oldr.approach.eq(approach)].iloc[0]
    ok=np.isclose(percentile,old.percentile,atol=1e-8) and quartile==old.quartile
    rank_checks.append(dict(approach=approach,n_reference=33,n_below=below,n_tied=ties,reference_percentile=old.percentile,recalculated_percentile=percentile,reference_quartile=int(old.quartile),recalculated_quartile=quartile,beta=su.coefficient,ci_low=su.ci_low,ci_high=su.ci_high,status='PASS' if ok else 'FAIL'))
save(rank_checks,'BEERS_percentile_comparison.csv')
names=pd.read_csv(NEW/'definitions/BEERS_numerator_names_effective.csv')
gi=names[names.entry.eq('antispasmodics')]
assert not gi.Gnrc_Name.str.contains('aclidinium|umeclidinium',case=False,regex=True).any()
assert (NEW/'DEPRECATED.md').read_bytes()==(REF/'DEPRECATED.md').read_bytes()

# Image pixels and PDF content streams/resources; creation dates are metadata only.
fig_checks=[];pdf_metadata={}
def pixels(a,b):
    aa=np.asarray(a.convert('RGBA'));bb=np.asarray(b.convert('RGBA'))
    if aa.shape!=bb.shape:return False,-1,-1,list(aa.shape),list(bb.shape)
    delta=np.abs(aa.astype(np.int16)-bb.astype(np.int16));return bool(np.array_equal(aa,bb)),int(np.any(delta!=0,axis=2).sum()),int(delta.max()),list(aa.shape),list(bb.shape)
def normalized_pdf(p):
    r=PdfReader(p);seen=set()
    def norm(x):
        from pypdf.generic import IndirectObject,StreamObject,DictionaryObject,ArrayObject
        if isinstance(x,IndirectObject):
            key=(x.idnum,x.generation)
            if key in seen:return 'RECURSIVE_REFERENCE'
            seen.add(key);v=norm(x.get_object());seen.remove(key);return v
        if isinstance(x,StreamObject):
            return {'stream_sha256':hashlib.sha256(x.get_data()).hexdigest(),'dict':{str(k):norm(v) for k,v in sorted(x.items()) if str(k) not in ['/Length','/Filter','/DecodeParms']}}
        if isinstance(x,DictionaryObject):return {str(k):norm(v) for k,v in sorted(x.items())}
        if isinstance(x,ArrayObject):return [norm(v) for v in x]
        if isinstance(x,bytes):return {'bytes':x.hex()}
        if isinstance(x,(int,float,str,bool)) or x is None:return x
        return str(x)
    pages=[]
    for pg in r.pages:
        pages.append(dict(mediabox=list(map(float,pg.mediabox)),content_sha256=hashlib.sha256(pg.get_contents().get_data()).hexdigest(),resources=norm(pg.get('/Resources')),image_count=len(list(pg.images))))
    md={str(k):str(v) for k,v in (r.metadata or {}).items()}
    return pages,md
for _,f in fi.iterrows():
    for ext in ['png','pdf']:
        old=REF/f[ext];new=NEW/f[ext];r=dict(figure_id=f.figure_id,format=ext,byte_equal=sha(old)==sha(new),reference_sha256=sha(old),rerun_sha256=sha(new))
        if ext=='png':
            with Image.open(old) as im1,Image.open(new) as im2:
                same,n,maxdelta,sh1,sh2=pixels(im1,im2)
            r.update(pixel_equal=same,different_pixels=n,max_channel_difference=maxdelta,reference_shape=str(sh1),rerun_shape=str(sh2),status='PASS' if same else 'FAIL')
        else:
            n1,md1=normalized_pdf(old);n2,md2=normalized_pdf(new)
            pdf_metadata[f.figure_id]=dict(reference=md1,rerun=md2)
            normsame=n1==n2;doc1=pdfium.PdfDocument(old);doc2=pdfium.PdfDocument(new)
            same=len(doc1)==len(doc2);totaldiff=0;maxdelta=0
            if same:
                for j in range(len(doc1)):
                    page1=doc1[j];page2=doc2[j];bm1=page1.render(scale=2);bm2=page2.render(scale=2)
                    ok,n,delta,sh1,sh2=pixels(bm1.to_pil(),bm2.to_pil());same &= ok;totaldiff+=n;maxdelta=max(maxdelta,delta)
                    bm1.close();bm2.close();page1.close();page2.close()
            doc1.close();doc2.close()
            r.update(pixel_equal=same,different_pixels=totaldiff,max_channel_difference=maxdelta,normalized_content_and_resources_equal=normsame,metadata_equal=md1==md2,pages_reference=len(n1),pages_rerun=len(n2),vector_no_image_XObjects=all(x['image_count']==0 for x in n2),status='PASS' if same and normsame else 'FAIL')
            if md1!=md2:diff('figures',f[ext],'PDF_METADATA_ONLY' if same and normsame else 'PDF_METADATA_CHANGED_WITH_CONTENT_DIFFERENCE',reference=json.dumps(md1),rerun=json.dumps(md2),material=not(same and normsame))
        if r['status']=='FAIL':diff('figures',f[ext],'FIGURE_CONTENT_MISMATCH',reference=str(r),rerun='',material=True)
        fig_checks.append(r)
save(fig_checks,'figure_comparison.csv')
(A/'pdf_metadata_comparison.json').write_text(json.dumps(pdf_metadata,indent=2))

# All old output bytes and all full B input files must remain unchanged.
prior=json.loads((A/'prior_files_manifest.json').read_text());preservation=[]
for x in prior:
    p=ROOT/x['path'];observed=sha(p) if p.exists() else 'MISSING';ok=observed==x['sha256']
    preservation.append(dict(path=x['path'],before_sha256=x['sha256'],after_sha256=observed,status='PASS' if ok else 'FAIL'))
    if not ok:diff('preservation',x['path'],'OLD_FILE_CHANGED',reference=x['sha256'],rerun=observed)
prior_outputs={x['path'] for x in prior if x['path'].startswith('outputs/')}
now_outputs={str(p.relative_to(ROOT)) for p in (ROOT/'outputs').rglob('*') if p.is_file()}
for p in sorted(now_outputs-prior_outputs):diff('preservation',p,'UNEXPECTED_NEW_FILE_IN_OLD_OUTPUTS')
save(preservation,'old_file_preservation.csv')
columns=['scope','artifact','difference_type','row','column','reference','rerun','material']
df=pd.DataFrame(diffs,columns=columns);df.to_csv(A/'difference_list.csv',index=False)
df[df.material.eq(True)].to_csv(A/'material_differences.csv',index=False)
env={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['pandas','numpy','scipy','statsmodels','matplotlib','pypdf','pypdfium2','Pillow','openpyxl']}}
(A/'runtime_environment.json').write_text(json.dumps(env,indent=2))
main=[x for x in table_checks if x['scope']=='main'];detail=[x for x in table_checks if x['scope']!='main']
status=dict(status='PASS' if not df.material.eq(True).any() and all(x['status']=='PASS' for x in rank_checks) else 'FAIL',completed_utc=utc(),models_refit_this_run=True,reference_release_packaging_only=True,reference=str(REF),workspace=str(S),rebuilt_views=str(NEW),frozen_entry_status='PASS',frozen_entry_scripts=8,supplemental_statistical_scripts=4,assembly_scripts=1,main_tables_checked=len(main),main_tables_passed=sum(x['status']=='PASS' for x in main),main_tables_byte_identical=sum(x['byte_equal'] for x in main),main_result_ledger_rows=len(pd.read_csv(NEW/'tables/main/MAIN_RESULTS.csv')),supporting_tables_checked=len(detail),supporting_tables_passed=sum(x['status']=='PASS' for x in detail),figure_files_checked=len(fig_checks),figure_files_passed=sum(x['status']=='PASS' for x in fig_checks),percentiles_checked=len(rank_checks),independent_BEERS_models=len(checks),independent_LASU_models=len(paired),old_files_checked=len(preservation),old_files_changed=sum(x['status']!='PASS' for x in preservation),old_output_file_set_unchanged=prior_outputs==now_outputs,material_differences=int(df.material.eq(True).sum()),nonmaterial_differences=int(df.material.eq(False).sum()),Beers_decision='INCLUDE_CONTEXT_ONLY' if all(x['recalculated_quartile']==4 for x in rank_checks) else 'DIFFERS',engineering_edits_to_statistical_scripts=0,table_tolerance={'rtol':1e-7,'atol':1e-8},pdf_raster_scale=2)
(A/'REPRODUCTION_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
(NEW/'REPRODUCTION_RECEIPT.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
print(json.dumps(status,ensure_ascii=False,indent=2))
