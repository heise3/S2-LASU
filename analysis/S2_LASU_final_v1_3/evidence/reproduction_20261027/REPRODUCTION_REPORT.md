# S2-LASU v1.2 完整统计复现报告

**最终判定：PASS。本次已实际重拟合统计模型，并与冻结 v1.2 最终包核对；实质性差异为 0。** 这是计算复现与交付一致性审计，不是新增分析、临床有效性验证或论文稿件。

- 参照包：`/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/outputs/S2_LASU_final_v1_2`
- 隔离统计工作区：`/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_20261027`
- 新组装表图：`/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_20261027/rebuilt_v1_2`
- 审计目录：`/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_audit_20261027`
- 开始（UTC）：2026-10-27T11:57:26.969531+00:00；比较结束（UTC）：2026-10-27T12:07:58.248098+00:00。
- 预先固定的数值容差：`rtol=1e-7, atol=1e-8`；行列结构、文本、缺失状态一致，整数计数精确一致。图片逐像素比较；PDF另比解码内容流及资源，元数据单列。

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 完整统计重算 | PASS | 冻结入口8步 + 补充基线/修正/文献4步 + 派生表1步 + 主表组装1步 |
| 主表 | 16/16 PASS | MAIN_RESULTS共44行；14张逐字节一致；7个主表差异单元格 |
| 支持统计表 | 100/100 PASS | 排除2份历史table_inventory元数据，其他保存统计表均重新生成或明确静态继承 |
| 图F1–F4 | 8/8 PASS | 4个PNG逐字节且像素一致；4个PDF规范化内容、字体资源及144dpi渲染像素一致 |
| 修正版Beers百分位 | 4/4 PASS | 33条目参照，另加长效SU；四口径均Q4 |
| 独立模型核验 | 78/78 PASS | 68个Beers份额OLS + 10个LASU配对WLS；核对β、SE、CI |
| 旧产出和完整B输入 | 1166/1166 PASS | 旧文件变化0；旧outputs文件集合不变 |
| 原8步入口覆盖 | INCOMPLETE → 已补齐 | 入口本身成功，但未独立重拟合继承Beers基线，且遗漏6张派生表；本次已实际补跑 |

## 主结果核对

`MAIN_RESULTS.csv` 的44行与旧包逐字节一致。以下仅列用于定位的关键数字；全部16表检查见 [table_comparison.csv](table_comparison.csv)。

| result_id | estimate | ci_low | ci_high | unit |
| --- | --- | --- | --- | --- |
| 2024_long_share_ge65 | 38.2229621481 |  |  | percent |
| 2024_long_share_lt65 | 35.6420520321 |  |  | percent |
| 2024_age_gap | 2.580910116 |  |  | percentage_points |
| A2_model2_age_year | 0.574270802756 | 0.443356412296 | 0.705185193217 | percentage_points/year |
| A4_ICC_2019 | 0.111025673672 |  |  | ICC_at_mean_volume |
| A4_ICC_2024 | 0.13005218236 |  |  | ICC_at_mean_volume |

| artifact | rows_reference | columns_reference | byte_equal | status |
| --- | --- | --- | --- | --- |
| tables/main/MAIN_RESULTS.csv | 44 | 9 | True | PASS |
| tables/main/T1_national_age_trends.csv | 24 | 16 | True | PASS |
| tables/main/T2_state_panel_main_and_post2023.csv | 8 | 18 | True | PASS |
| tables/main/T3a_prescriber_profiles.csv | 2 | 24 | True | PASS |
| tables/main/T3b_prescriber_coverage.csv | 2 | 14 | True | PASS |
| tables/main/T3c_prescriber_specialties.csv | 194 | 12 | True | PASS |
| tables/main/T3d_prescriber_correlations.csv | 2 | 6 | True | PASS |
| tables/main/T3e_prescriber_state_ICC.csv | 2 | 23 | True | PASS |
| tables/main/T4a_robustness_interactions.csv | 10 | 20 | True | PASS |
| tables/main/T4b_standardization_direction_checks.csv | 30 | 10 | True | PASS |
| tables/main/T4c_piecewise_slopes.csv | 4 | 9 | True | PASS |
| tables/main/T5_beneficiary_scale_bounds.csv | 3 | 13 | True | PASS |
| tables/main/T6a_BEERS_three_approach_comparison.csv | 34 | 35 | False | PASS |
| tables/main/T6b_BEERS_three_approach_long.csv | 136 | 29 | False | PASS |
| tables/main/T6c_BEERS_percentiles.csv | 4 | 11 | True | PASS |
| tables/main/T7_literature_comparison.csv | 19 | 11 | True | PASS |

## 修正版 Beers 百分位

以下百分位从本次重新拟合的所有条目系数独立计算，定义为低于长效SU系数的参照条目数/33×100。长效SU自身不进入33条目分母；本次四口径均无并列。

| approach | n_below | reference_percentile | recalculated_percentile | recalculated_quartile | status |
| --- | --- | --- | --- | --- | --- |
| a_national_denominator | 26 | 78.7878787879 | 78.7878787879 | 4 | PASS |
| b_share_log | 28 | 84.8484848485 | 84.8484848485 | 4 | PASS |
| b_share_logit | 28 | 84.8484848485 | 84.8484848485 | 4 | PASS |
| c_raw_state_volume | 26 | 78.7878787879 | 78.7878787879 | 4 | PASS |

四口径均为Q4，**纳入S2-LASU描述性对照基准**的决定保持一致。全国年龄分母和州未标准化量均使用修正后的GI条目，不能恢复使用保留错误旧基线的75.76百分位结果。同类内份额的log与logit均为84.85百分位。

有效GI清单不含 Aclidinium Bromide、Umeclidinium Bromide、Umeclidinium Brm/Vilanterol Tr；冻结历史规则保留为审计材料，修正通过原有 `correct_name_collision.py` 完成，未改动治疗类别定义或四分位门槛。原 `DEPRECATED.md` 与新组装版逐字节一致，旧误匹配结果继续停用。

65岁以下Part D人群以残障入保者为主；交互项仍仅描述年龄组间趋势差异，不能解释为Beers政策效应。T7文献对比19行与旧包一致，保留Stuart 2003概念先例；本次没有重新进行文献检索。

## 图形核对

| figure_id | format | byte_equal | pixel_equal | different_pixels | max_channel_difference | status |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | png | True | True | 0 | 0 | PASS |
| F1 | pdf | False | True | 0 | 0 | PASS |
| F2 | png | True | True | 0 | 0 | PASS |
| F2 | pdf | False | True | 0 | 0 | PASS |
| F3 | png | True | True | 0 | 0 | PASS |
| F3 | pdf | False | True | 0 | 0 | PASS |
| F4 | png | True | True | 0 | 0 | PASS |
| F4 | pdf | False | True | 0 | 0 | PASS |

四个PNG均逐字节一致。四个PDF均为单页矢量文件，图像XObject数为0；规范化内容流、资源、页面尺寸及144dpi渲染像素全部相同。PDF文件哈希不同只来自创建日期，细项见 [pdf_metadata_comparison.json](pdf_metadata_comparison.json)。

## 差异清单及影响

- 实质性差异：**0**；[material_differences.csv](material_differences.csv) 只有表头。
- 主表：7处末位数值差异，最大绝对差 **1.00003e-13**。条目、列名及原值/重算值见 [main_table_differences.csv](main_table_differences.csv)；方向、显著性、排名、百分位和纳入判定一致。
- 支持统计表：320,687个数值单元格有容差内差异；其中320,533个位于Beers主模型面板，最大绝对差 **5.58794e-09**。均小于预定绝对容差，属于浮点计算/CSV往返的末位数值变化。另有20个文件仅压缩或序列化字节不同，表数据一致。
- 图形：4处PDF创建时间变化；内容与像素无差异。
- 合计320,718条非实质差异记录。汇总见 [difference_summary.csv](difference_summary.csv)，完整逐格清单见 [difference_list.csv.gz](difference_list.csv.gz)（解压为CSV）；原始未压缩CSV亦留在审计目录。

## 实际执行范围与入口遗漏

原v1.2统一入口的8步均成功，入口自带6表核对通过。随后从12个完整B文件重新进行Beers匹配、低量过滤与基线模型拟合，继续执行同类内份额模型、修正版GI处理及文献表组装。全程沿用原代码、字段映射、药名和ATC类别，不刷新外部数据。

扩展审计首次按文件生成时间检查时，发现6张LASU派生附表仍是复制的旧文件：A1_absolute_volumes、A1_family_shares_wide、A1_fit_diagnostics、A1_fit_residuals、A1_volume_changes、A2_suppression_summary。已运行原有build_report.py生成这些附表，并只将其数值表用于本次核对。实际执行及处理记录保留；这是入口覆盖不足，未发现统计计算失败。没有修改统计脚本，也没有据结果更改定义、模型或阈值。

两份旧table_inventory为包装元数据，不作为统计复现对象。静态地理排除记录R2_inherited_geographic_exclusions继承经哈希核验的数据；其余99张支持表（包括新做的独立检查）均在本次重新生成。新表目录从空目录组装，未复制旧包的16张主表作为重算结果。

新组装目录中的DECISIONS.json、TABLE_INDEX.md等沿用旧assembler生成，`packaging_only`/`models_refit_this_release=false`描述原v1.2发布，不描述此次执行；本次状态以 [REPRODUCTION_STATUS.json](REPRODUCTION_STATUS.json) 和新目录REPRODUCTION_RECEIPT.json为准，`models_refit_this_run=true`。

## 输入、代码与旧产出保护

- 125个输入/代码文件逐字节核对通过（见 [input_and_code_comparison.csv](input_and_code_comparison.csv)），包括A/B抽取数据、12个完整B文件、字段/药名清单、源脚本及官方参保工作簿。
- 29个冻结映射文件哈希通过；见 [frozen_mapping_comparison.csv](frozen_mapping_comparison.csv)。
- Beers使用的24个年龄×年官方分母与本次重新从官方工作簿提取的v1.1分母逐字节一致，未估算州级分母。
- 1,166份旧文件和完整B输入全部哈希不变；其中1,154份是旧outputs文件，另12份是完整B输入。旧outputs既无新增，也无删除。见 [old_file_preservation.csv](old_file_preservation.csv)。
- 统计脚本修改数0；运行环境见 [runtime_environment.json](runtime_environment.json)。本次不是跨软件版本/平台独立复现，也不检验原始CMS数据真实性或未公开行造成的偏差。

## 复现入口与交付

完整补齐入口为 `code/run_reproduction.py`；调用示例和文件布局见 [README.md](README.md)。该入口要求两个全新目录，拒绝覆盖既有工作区。历史含clidinium误匹配的中间结果只留在隔离工作区用于追溯，不进入重新组装的有效表图。

本次所有步骤日志在隔离工作区 `logs/`；补充步骤的时间、返回码和代码哈希在 [supplement_execution.json](supplement_execution.json)。交付压缩包含报告、核对CSV、差异清单、日志、审计代码、16张重算主表和F1–F4，不重复打包完整原始输入。
