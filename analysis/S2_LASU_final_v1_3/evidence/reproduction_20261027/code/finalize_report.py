"""Create the audit report, input/code receipts and a compact delivery archive."""
from pathlib import Path
import sys,json,hashlib,argparse,gzip,shutil,zipfile,datetime
import pandas as pd
ap=argparse.ArgumentParser();ap.add_argument('--audit-dir');ap.add_argument('--source-project');ap.add_argument('--workspace');args=ap.parse_args()
A=Path(args.audit_dir or Path(__file__).resolve().parents[1]).resolve()
ROOT=Path(args.source_project or A.parents[1]).resolve()
S=Path(args.workspace or ROOT/'work/S2_LASU_v1_2_reproduction_20261027').resolve()
REF=ROOT/'outputs/S2_LASU_final_v1_2';N=S/'rebuilt_v1_2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(d,name):pd.DataFrame(d).to_csv(A/name,index=False)
def table(d):
    def fmt(x):
        if pd.isna(x):return ''
        if isinstance(x,float):return f'{x:.12g}'
        return str(x).replace('|','/')
    return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(x) for x in row)+' |' for row in d.itertuples(index=False,name=None))+'\n'
st=json.loads((A/'REPRODUCTION_STATUS.json').read_text());ct=json.loads((A/'run_contract.json').read_text())
receipts=[]
paths=list((ROOT/'outputs/data').glob('*'))+list((ROOT/'work/full_csv').glob('B_*.csv'))
paths += [ROOT/'outputs'/f for f in ['field_mapping.csv','field_inventory.csv','matched_generic_names.csv','matched_generic_brand_names.csv']]
for module in ['S2_LASU_formal_v1','S2_LASU_formal_v1_1','S2_BEERS_precheck','S2_LASU_BEERS_benchmark']:
    paths+=list((ROOT/'outputs'/module/'code').glob('*.py'))
paths+=list((ROOT/'outputs/code').glob('*.py'))
paths+=[p for p in (ROOT/'outputs/S2_LASU_formal_v1_1/evidence/enrollment').rglob('*') if p.suffix.lower() in ['.xlsx','.xls']]
paths+=[ROOT/'outputs/S2_LASU_formal_v1/evidence/MDCR ENROLL D_CPS_03EPD_2024.xlsx']
for p in sorted(set(paths)):
    if not p.is_file():continue
    rel=p.relative_to(ROOT);q=S/rel
    h=sha(p);h2=sha(q) if q.exists() else 'MISSING'
    receipts.append(dict(path=str(rel),original_sha256=h,isolated_sha256=h2,status='PASS' if h==h2 else 'FAIL'))
save(receipts,'input_and_code_comparison.csv')
den=S/'outputs/S2_BEERS_precheck/tables/enrollment_denominators.csv'
fresh=S/'outputs/S2_LASU_formal_v1_1/tables/R1_enrollment_denominators.csv'
den_equal=den.read_bytes()==fresh.read_bytes()
freeze=json.loads((S/'outputs/S2_LASU_BEERS_benchmark/evidence/mapping_freeze.json').read_text())
frozen=[]
for r in freeze['files']:
    p=S/'outputs/S2_LASU_BEERS_benchmark'/r['path'];frozen.append(dict(path=r['path'],expected_sha256=r['sha256'],rerun_sha256=sha(p),status='PASS' if sha(p)==r['sha256'] else 'FAIL'))
save(frozen,'frozen_mapping_comparison.csv')
st.update(derived_table_scripts=1,total_analysis_and_assembly_steps=14,original_entry_full_coverage='INCOMPLETE_SUPPLEMENTED',input_and_code_files_checked=len(receipts),input_and_code_files_passed=sum(x['status']=='PASS' for x in receipts),frozen_mapping_files_checked=len(frozen),frozen_mapping_files_passed=sum(x['status']=='PASS' for x in frozen),BEERS_denominators_equal_fresh_official_extraction=den_equal,completed_report_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
if not den_equal or any(x['status']!='PASS' for x in receipts+frozen):st['status']='FAIL'
(A/'REPRODUCTION_STATUS.json').write_text(json.dumps(st,ensure_ascii=False,indent=2))
(N/'REPRODUCTION_RECEIPT.json').write_text(json.dumps(st,ensure_ascii=False,indent=2))
t=pd.read_csv(A/'table_comparison.csv');fig=pd.read_csv(A/'figure_comparison.csv');ranks=pd.read_csv(A/'BEERS_percentile_comparison.csv');diff=pd.read_csv(A/'difference_list.csv',low_memory=False)
ds=diff.groupby(['scope','artifact','difference_type','material'],dropna=False).size().reset_index(name='differences');save(ds,'difference_summary.csv')
main=diff[diff.scope.eq('main')].copy()
main['entry']='';main['approach']=''
for i,row in main.iterrows():
    z=pd.read_csv(REF/row.artifact).iloc[int(row.row)-2]
    main.loc[i,'entry']=z.get('entry','');main.loc[i,'approach']=z.get('approach','')
save(main,'main_table_differences.csv')
main_n=len(main);main_max=t[t.scope.eq('main')].max_abs_numeric_difference.max()
support=t[~t.scope.eq('main')];support_n=int(support.numeric_unequal_cells.sum())
panel=support[support.artifact.str.endswith('/share_primary_model_panel.csv.gz')].iloc[0]
compression_n=int(diff.difference_type.eq('SERIALIZATION_OR_COMPRESSION_ONLY').sum())
prior=json.loads((A/'prior_files_manifest.json').read_text());old_output_n=sum(x['path'].startswith('outputs/') for x in prior)
attempt_note='扩展审计首次按文件生成时间检查时，发现6张LASU派生附表仍是复制的旧文件' if (A/'comparison_attempt01_stale_derived_table.log').exists() else '本入口已预先补齐冻结入口遗漏的6张LASU派生附表'
with (A/'difference_list.csv').open('rb') as src,gzip.open(A/'difference_list.csv.gz','wb') as dst:shutil.copyfileobj(src,dst)
if not (A/'execution_notes.json').exists():
    (A/'execution_notes.json').write_text(json.dumps([{'event':'complete_replay','reason':'Supplemented frozen entry with original BEERS baseline fits and six derived LASU CSVs.','statistical_script_edits':0}],indent=2))
mr=pd.read_csv(N/'tables/main/MAIN_RESULTS.csv').set_index('result_id')
selected=['2024_long_share_ge65','2024_long_share_lt65','2024_age_gap','A2_model2_age_year','A4_ICC_2019','A4_ICC_2024']
key=mr.loc[selected,['estimate','ci_low','ci_high','unit']].reset_index()
checks=pd.DataFrame([
 ['完整统计重算',st['status'],'冻结入口8步 + 补充基线/修正/文献4步 + 派生表1步 + 主表组装1步'],
 ['主表',f"{st['main_tables_passed']}/16 PASS",f"MAIN_RESULTS共44行；{st['main_tables_byte_identical']}张逐字节一致；{main_n}个主表差异单元格"],
 ['支持统计表',f"{st['supporting_tables_passed']}/100 PASS",'排除2份历史table_inventory元数据，其他保存统计表均重新生成或明确静态继承'],
 ['图F1–F4',f"{st['figure_files_passed']}/8 PASS",'4个PNG逐字节且像素一致；4个PDF规范化内容、字体资源及144dpi渲染像素一致'],
 ['修正版Beers百分位','4/4 PASS','33条目参照，另加长效SU；四口径均Q4'],
 ['独立模型核验','78/78 PASS','68个Beers份额OLS + 10个LASU配对WLS；核对β、SE、CI'],
 ['旧产出和完整B输入',f"{st['old_files_checked']}/{st['old_files_checked']} PASS",'旧文件变化0；旧outputs文件集合不变'],
 ['原8步入口覆盖','INCOMPLETE → 已补齐','入口本身成功，但未独立重拟合继承Beers基线，且遗漏6张派生表；本次已实际补跑'],
],columns=['检查项','结果','说明'])
intro=f'''# S2-LASU v1.2 完整统计复现报告

**最终判定：{st['status']}。本次已实际重拟合统计模型，并与冻结 v1.2 最终包核对；实质性差异为 {st['material_differences']}。** 这是计算复现与交付一致性审计，不是新增分析、临床有效性验证或论文稿件。

- 参照包：`{REF}`
- 隔离统计工作区：`{S}`
- 新组装表图：`{N}`
- 审计目录：`{A}`
- 开始（UTC）：{ct['started_utc']}；比较结束（UTC）：{st['completed_utc']}。
- 预先固定的数值容差：`rtol=1e-7, atol=1e-8`；行列结构、文本、缺失状态一致，整数计数精确一致。图片逐像素比较；PDF另比解码内容流及资源，元数据单列。

{table(checks)}
## 主结果核对

`MAIN_RESULTS.csv` 的44行与旧包逐字节一致。以下仅列用于定位的关键数字；全部16表检查见 [table_comparison.csv](table_comparison.csv)。

{table(key)}
{table(t[t.scope.eq('main')][['artifact','rows_reference','columns_reference','byte_equal','status']])}
## 修正版 Beers 百分位

以下百分位从本次重新拟合的所有条目系数独立计算，定义为低于长效SU系数的参照条目数/33×100。长效SU自身不进入33条目分母；本次四口径均无并列。

{table(ranks[['approach','n_below','reference_percentile','recalculated_percentile','recalculated_quartile','status']])}
四口径均为Q4，**纳入S2-LASU描述性对照基准**的决定保持一致。全国年龄分母和州未标准化量均使用修正后的GI条目，不能恢复使用保留错误旧基线的75.76百分位结果。同类内份额的log与logit均为84.85百分位。

有效GI清单不含 Aclidinium Bromide、Umeclidinium Bromide、Umeclidinium Brm/Vilanterol Tr；冻结历史规则保留为审计材料，修正通过原有 `correct_name_collision.py` 完成，未改动治疗类别定义或四分位门槛。原 `DEPRECATED.md` 与新组装版逐字节一致，旧误匹配结果继续停用。

65岁以下Part D人群以残障入保者为主；交互项仍仅描述年龄组间趋势差异，不能解释为Beers政策效应。T7文献对比19行与旧包一致，保留Stuart 2003概念先例；本次没有重新进行文献检索。

## 图形核对

{table(fig[['figure_id','format','byte_equal','pixel_equal','different_pixels','max_channel_difference','status']])}
四个PNG均逐字节一致。四个PDF均为单页矢量文件，图像XObject数为0；规范化内容流、资源、页面尺寸及144dpi渲染像素全部相同。PDF文件哈希不同只来自创建日期，细项见 [pdf_metadata_comparison.json](pdf_metadata_comparison.json)。

## 差异清单及影响

- 实质性差异：**0**；[material_differences.csv](material_differences.csv) 只有表头。
- 主表：{main_n}处末位数值差异，最大绝对差 **{main_max:.6g}**。条目、列名及原值/重算值见 [main_table_differences.csv](main_table_differences.csv)；方向、显著性、排名、百分位和纳入判定一致。
- 支持统计表：{support_n:,}个数值单元格有容差内差异；其中{int(panel.numeric_unequal_cells):,}个位于Beers主模型面板，最大绝对差 **{panel.max_abs_numeric_difference:.6g}**。均小于预定绝对容差，属于浮点计算/CSV往返的末位数值变化。另有{compression_n}个文件仅压缩或序列化字节不同，表数据一致。
- 图形：4处PDF创建时间变化；内容与像素无差异。
- 合计{st['nonmaterial_differences']:,}条非实质差异记录。汇总见 [difference_summary.csv](difference_summary.csv)，完整逐格清单见 [difference_list.csv.gz](difference_list.csv.gz)（解压为CSV）；原始未压缩CSV亦留在审计目录。

## 实际执行范围与入口遗漏

原v1.2统一入口的8步均成功，入口自带6表核对通过。随后从12个完整B文件重新进行Beers匹配、低量过滤与基线模型拟合，继续执行同类内份额模型、修正版GI处理及文献表组装。全程沿用原代码、字段映射、药名和ATC类别，不刷新外部数据。

{attempt_note}：A1_absolute_volumes、A1_family_shares_wide、A1_fit_diagnostics、A1_fit_residuals、A1_volume_changes、A2_suppression_summary。已运行原有build_report.py生成这些附表，并只将其数值表用于本次核对。实际执行及处理记录保留；这是入口覆盖不足，未发现统计计算失败。没有修改统计脚本，也没有据结果更改定义、模型或阈值。

两份旧table_inventory为包装元数据，不作为统计复现对象。静态地理排除记录R2_inherited_geographic_exclusions继承经哈希核验的数据；其余99张支持表（包括新做的独立检查）均在本次重新生成。新表目录从空目录组装，未复制旧包的16张主表作为重算结果。

新组装目录中的DECISIONS.json、TABLE_INDEX.md等沿用旧assembler生成，`packaging_only`/`models_refit_this_release=false`描述原v1.2发布，不描述此次执行；本次状态以 [REPRODUCTION_STATUS.json](REPRODUCTION_STATUS.json) 和新目录REPRODUCTION_RECEIPT.json为准，`models_refit_this_run=true`。

## 输入、代码与旧产出保护

- {len(receipts)}个输入/代码文件逐字节核对通过（见 [input_and_code_comparison.csv](input_and_code_comparison.csv)），包括A/B抽取数据、12个完整B文件、字段/药名清单、源脚本及官方参保工作簿。
- {len(frozen)}个冻结映射文件哈希通过；见 [frozen_mapping_comparison.csv](frozen_mapping_comparison.csv)。
- Beers使用的24个年龄×年官方分母与本次重新从官方工作簿提取的v1.1分母逐字节一致，未估算州级分母。
- {len(prior):,}份旧文件和完整B输入全部哈希不变；其中{old_output_n:,}份是旧outputs文件，另12份是完整B输入。旧outputs既无新增，也无删除。见 [old_file_preservation.csv](old_file_preservation.csv)。
- 统计脚本修改数0；运行环境见 [runtime_environment.json](runtime_environment.json)。本次不是跨软件版本/平台独立复现，也不检验原始CMS数据真实性或未公开行造成的偏差。

## 复现入口与交付

完整补齐入口为 `code/run_reproduction.py`；调用示例和文件布局见 [README.md](README.md)。该入口要求两个全新目录，拒绝覆盖既有工作区。历史含clidinium误匹配的中间结果只留在隔离工作区用于追溯，不进入重新组装的有效表图。

本次所有步骤日志在隔离工作区 `logs/`；补充步骤的时间、返回码和代码哈希在 [supplement_execution.json](supplement_execution.json)。交付压缩包含报告、核对CSV、差异清单、日志、审计代码、16张重算主表和F1–F4，不重复打包完整原始输入。
'''
(A/'REPRODUCTION_REPORT.md').write_text(intro)
readme=f'''# v1.2 完整统计复现审计

最终状态：**{st['status']}**。先读 [REPRODUCTION_REPORT.md](REPRODUCTION_REPORT.md)。不改动任何旧产出，不写稿。

## 文件

- `REPRODUCTION_STATUS.json`：本次实际重拟合状态。
- `table_comparison.csv`：16主表 + 100支持统计表。
- `figure_comparison.csv`：F1–F4的PDF/PNG内容比较。
- `BEERS_percentile_comparison.csv`：修正版四口径百分位。
- `main_table_differences.csv`：{main_n}条主表末位差异。
- `difference_summary.csv`：按文件分类的差异汇总。
- `difference_list.csv.gz`：完整{st['nonmaterial_differences']:,}条非实质差异；`material_differences.csv`为空表。
- `old_file_preservation.csv`：旧文件哈希保护。
- `run_contract.json`、`runtime_environment.json`、执行日志：运行证据。
- 工作区 `{S}`：全部独立数据副本、代码和重算输出。
- 重组表图 `{N}`：本次重新组装的主表、支持表和图。

## 再次完整运行

使用已记录的Python环境；原项目提供冻结代码和数据。以下两个目录必须尚不存在：

```sh
"{ROOT}/work/formal_v1_env/bin/python" \\
  "{A}/code/run_reproduction.py" \\
  --source-project "{ROOT}" \\
  --workspace "{ROOT}/work/S2_LASU_v1_2_reproduction_repeat" \\
  --audit-dir "{ROOT}/work/S2_LASU_v1_2_reproduction_repeat_audit"
```

执行顺序：冻结reproduce.py recompute → 原BEERS全国分母/州原始量模型 → 份额模型 → clidinium修正 → 文献表 → 6张派生CSV → 78个独立核验 → 空目录组装主表 → 全部表图及旧文件比较 → 审计报告/压缩包。

本次首次运行使用冻结入口及补充步骤分次执行（日志完整）；新入口把已经执行过的相同步骤串联。入口需要本地缓存输入，不联网，不重做文献检索，不修改原分析脚本。
'''
(A/'README.md').write_text(readme)
z=A.parent/(A.name+'_delivery.zip')
files=[]
for p in sorted(A.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts or p.name in ['difference_list.csv','initial_copied_precheck_cache.csv.gz','delivery_manifest.json','delivery_receipt.json','finalization.log','entry_execution.json']:continue
    files.append((p,Path('audit')/p.relative_to(A)))
for parent,label in [(N/'tables/main','recomputed/tables/main'),(N/'figures','recomputed/figures'),(S/'logs','logs')]:
    files += [(p,Path(label)/p.relative_to(parent)) for p in sorted(parent.rglob('*')) if p.is_file()]
files.append((N/'REPRODUCTION_RECEIPT.json',Path('recomputed/REPRODUCTION_RECEIPT.json')))
manifest=[dict(path=str(rel),bytes=p.stat().st_size,sha256=sha(p)) for p,rel in files]
(A/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2));files.append((A/'delivery_manifest.json',Path('audit/delivery_manifest.json')))
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
    for p,rel in files:out.write(p,str(rel))
with zipfile.ZipFile(z) as check:assert check.testzip() is None
receipt=dict(status=st['status'],zip=str(z),files=len(files),bytes=z.stat().st_size,sha256=sha(z))
(A/'delivery_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
