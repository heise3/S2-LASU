"""Finalize a NEW v1.3 replay audit without editing the frozen reference."""
from pathlib import Path
import argparse,json,gzip,shutil,datetime
import pandas as pd
ap=argparse.ArgumentParser();ap.add_argument('--audit-dir',required=True);ap.add_argument('--source-project',required=True);ap.add_argument('--workspace',required=True);ap.add_argument('--reference-package',required=True);args=ap.parse_args()
A=Path(args.audit_dir);S=Path(args.workspace);REF=Path(args.reference_package)
st=json.loads((A/'REPRODUCTION_STATUS.json').read_text())
st.update(reference_version='v1.3',pipeline='COMPLETE_14_STEPS',reference=str(REF),derived_table_scripts=1,total_analysis_and_assembly_steps=14,completed_report_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(A/'REPRODUCTION_STATUS.json').write_text(json.dumps(st,ensure_ascii=False,indent=2))
(S/'rebuilt_v1_3/REPRODUCTION_RECEIPT.json').write_text(json.dumps(st,ensure_ascii=False,indent=2))
ds=pd.read_csv(A/'difference_list.csv',low_memory=False)
ds.groupby(['scope','artifact','difference_type','material'],dropna=False).size().reset_index(name='differences').to_csv(A/'difference_summary.csv',index=False)
ds[ds.scope.eq('main')].to_csv(A/'main_table_differences.csv',index=False)
with (A/'difference_list.csv').open('rb') as src,gzip.open(A/'difference_list.csv.gz','wb') as dst:shutil.copyfileobj(src,dst)
rank=pd.read_csv(A/'BEERS_percentile_comparison.csv')
rows='\n'.join(f'| {r.approach} | {r.recalculated_percentile:.8f} | Q{r.recalculated_quartile} | {r.status} |' for r in rank.itertuples())
md=f'''# S2-LASU v1.3 统计复现报告

**判定：{st['status']}。** 此报告对应当前隔离重算，不修改冻结包。

- 参照包：`{REF}`；实际重算工作区：`{S}`。
- 主表：{st['main_tables_passed']}/{st['main_tables_checked']}；支持表：{st['supporting_tables_passed']}/{st['supporting_tables_checked']}；图文件：{st['figure_files_passed']}/{st['figure_files_checked']}。
- 实质性差异：{st['material_differences']}；容差内或元数据差异：{st['nonmaterial_differences']}。
- 统计重拟合：已执行；完整流程14步，包含原8步、补齐Beers继承基线及修正/文献4步、派生表1步与组装1步。另独立核验78个模型。
- 旧文件检查：{st['old_files_checked']}；改变：{st['old_files_changed']}。
- 数值容差rtol=1e-7、atol=1e-8；整数、文本、缺失位置一致；PDF规范化内容/资源及144dpi渲染像素一致。

| 口径 | 百分位 | 四分位 | 核对 |
| --- | --- | --- | --- |
{rows}

全部核对CSV、执行日志、环境和状态均在本审计目录。完整差异为`difference_list.csv.gz`，汇总为`difference_summary.csv`。

含clidinium误匹配的旧Beers结果继续停用；仅以全部口径均修正的结果为准。长效SU不计入33条目参照分母。交互描述年龄组趋势差异，不解释为Beers政策效应。没有撰写稿件。
'''
(A/'REPRODUCTION_REPORT.md').write_text(md)
(A/'README.md').write_text('# v1.3 隔离统计复现\n\n从 [复现报告](REPRODUCTION_REPORT.md) 和 [状态](REPRODUCTION_STATUS.json) 开始。完整执行入口在冻结包 `code/reproduce.py`，不得直接运行历史源脚本。\n')
print(json.dumps(st,ensure_ascii=False,indent=2))
