# v1.3 冻结结果的统计复现报告

**PASS：v1.3采用已完成并通过核验的完整重算结果，实质性差异0。** 源重算完成于2026-10-27 UTC；本次仅冻结交付，没有再次拟合或写稿。

| 核对对象 | 源运行结果 | v1.3采用方式 |
| --- | --- | --- |
| 16张主表，MAIN_RESULTS 44行 | 16/16 PASS；14张与v1.2逐字节一致 | 重算文件逐字节导入 |
| 100张支持统计表 | 100/100 PASS | 重算文件逐字节导入 |
| F1–F4的PDF+PNG | 8/8 PASS；PNG逐字节、PDF内容及像素一致 | 使用重绘后的通过核验版本 |
| 4个Beers百分位 | 78.79/84.85/84.85/78.79；均Q4 | 全口径修正版，仍纳入描述性基准 |
| 独立模型核验 | 68个Beers模型＋10个LASU模型通过 | 保留核验CSV |
| 既有旧文件和完整B输入 | 1,166份哈希不变 | 本次另做冻结前后保留核验 |

源比较中T6a/T6b有7个末位数值差异，最大绝对差约1×10⁻¹³；支持表还有容差内浮点变化、gzip序列化及4个PDF创建时间差异。均已记录，不改变方向、CI、显著性、百分位或判定。v1.3选择通过复现的重算字节为当前权威，未用v1.2旧字节覆盖这些差异。

## 通过证据

- [原始完整复现报告](evidence/reproduction_20261027/REPRODUCTION_REPORT.md)及[原始状态](evidence/reproduction_20261027/REPRODUCTION_STATUS.json)。它们记录v1.2作为当时参照包的审计事实，不是v1.3的当前状态。
- [主表与支持表比较](evidence/reproduction_20261027/table_comparison.csv)、[图形比较](evidence/reproduction_20261027/figure_comparison.csv)、[百分位比较](evidence/reproduction_20261027/BEERS_percentile_comparison.csv)。
- [7处主表差异](evidence/reproduction_20261027/main_table_differences.csv)、[差异分类汇总](evidence/reproduction_20261027/difference_summary.csv)、[完整逐格差异CSV.gz](evidence/reproduction_20261027/difference_list.csv.gz)、[实质性差异空表](evidence/reproduction_20261027/material_differences.csv)。
- [本次冻结核验](evidence/freeze_validation.json)，包括所有导入表图与通过核验的重算源的字节一致性、v1.2及旧源文件保留、补齐入口的集成检查。

## 入口覆盖及状态解释

原8步入口本身运行成功，但未独立重拟合继承的Beers全国分母/州原始量基线，也遗漏6张LASU派生表。本次整合的入口明确保留已实际执行的补齐步骤；全量核对参照已切换为v1.3，默认只读检查冻结包。原模型脚本、映射、抑制规则及判定阈值未变。

根目录STATUS.json是唯一当前版本状态：FROZEN、statistical_reproduction_status=PASS、models_refit_in_source_run=true、freeze_step_refits_models=false。这四项分别表达版本冻结、源统计复现通过、源运行实际重拟合、此次冻结未重复拟合，不再使用含糊的“本版未运行”标签。

含clidinium误匹配的旧结果继续停用，详见[停用清单](DEPRECATED.md)。<65 Part D年龄组不能视为普通年轻人群；交互仅描述年龄组趋势差异，不解释为Beers政策效应。该审计确认数值和交付一致性，不替代原始数据有效性或研究设计评估。
