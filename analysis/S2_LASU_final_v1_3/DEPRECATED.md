# 明确停用含 clidinium 误匹配的旧结果

旧文件原样保留用于追溯，不删除、不覆盖。下列结果不得从原路径复制进主结果、图或新稿。旧GI项误将aclidinium/umeclidinium呼吸系统产品作为GI解痉药；最新三口径均须使用已纠正版本。

| 旧产物 | 状态 | 理由 | 替代 |
| --- | --- | --- | --- |
| S2_BEERS_precheck/tables/K*.csv; figures/*; SUMMARY.md | DEPRECATED_FOR_ANALYTIC_USE | 含GI clidinium子串误匹配，且独立BEERS论文路线停用 | tables/main/T6a_BEERS_three_approach_comparison.csv |
| S2_BEERS_precheck/tables/drug_filtered/* | DEPRECATED_FOR_ANALYTIC_USE | 低量过滤没有修复aclidinium/umeclidinium误匹配 | tables/details/beers_corrected/ |
| S2_LASU_BEERS_benchmark/tables/three_approach*.csv; tables/share_*.csv | DEPRECATED_INHERITED_RUN | 冻结初算保留错误GI条目 | tables/main/T6a_BEERS_three_approach_comparison.csv |
| S2_LASU_BEERS_benchmark/tables/corrected/three_approach_comparison.csv; three_approach_results_long.csv; benchmark_percentile_and_decision_inputs.csv | AUDIT_ONLY_NOT_MAIN | 份额已修正，但(a)/(c)仍保留错误旧基线，含75.76百分位 | tables/main/T6c_BEERS_percentiles.csv |
| S2_LASU_BEERS_benchmark/figures/frozen_inherited_not_for_use/* | DEPRECATED_FIGURE | 错误GI项森林图 | figures/F4_BEERS_within_class_benchmark.pdf |
| S2_LASU_BEERS_benchmark/evidence/decision.json | SUPERSEDED_DECISION | 初算决定；当前使用全口径更正后的Q4核验 | DECISIONS.json |

原75.76百分位属于保留错误旧基线的审计比较，不是本最终包的主百分位；统一使用78.79/84.85/84.85/78.79。冻结映射原件及历史代码仅为审计，不是有效药名规则；有效清单在definitions/BEERS_numerator_*_effective.csv。LASU自身SU药名定义不含该clidinium规则，原LASU A1–A4结果未因此失效。
