# v1.3 主结果表

以下16张主表来自通过完整统计复现的重算结果。统一结果定位表MAIN_RESULTS共44行；100张支持统计表在tables/details/。状态以[STATUS.json](STATUS.json)为准。

| 表 | 行数 | 列数 |
| --- | --- | --- |
| [MAIN_RESULTS.csv](tables/main/MAIN_RESULTS.csv) | 44 | 9 |
| [T1_national_age_trends.csv](tables/main/T1_national_age_trends.csv) | 24 | 16 |
| [T2_state_panel_main_and_post2023.csv](tables/main/T2_state_panel_main_and_post2023.csv) | 8 | 18 |
| [T3a_prescriber_profiles.csv](tables/main/T3a_prescriber_profiles.csv) | 2 | 24 |
| [T3b_prescriber_coverage.csv](tables/main/T3b_prescriber_coverage.csv) | 2 | 14 |
| [T3c_prescriber_specialties.csv](tables/main/T3c_prescriber_specialties.csv) | 194 | 12 |
| [T3d_prescriber_correlations.csv](tables/main/T3d_prescriber_correlations.csv) | 2 | 6 |
| [T3e_prescriber_state_ICC.csv](tables/main/T3e_prescriber_state_ICC.csv) | 2 | 23 |
| [T4a_robustness_interactions.csv](tables/main/T4a_robustness_interactions.csv) | 10 | 20 |
| [T4b_standardization_direction_checks.csv](tables/main/T4b_standardization_direction_checks.csv) | 30 | 10 |
| [T4c_piecewise_slopes.csv](tables/main/T4c_piecewise_slopes.csv) | 4 | 9 |
| [T5_beneficiary_scale_bounds.csv](tables/main/T5_beneficiary_scale_bounds.csv) | 3 | 13 |
| [T6a_BEERS_three_approach_comparison.csv](tables/main/T6a_BEERS_three_approach_comparison.csv) | 34 | 35 |
| [T6b_BEERS_three_approach_long.csv](tables/main/T6b_BEERS_three_approach_long.csv) | 136 | 29 |
| [T6c_BEERS_percentiles.csv](tables/main/T6c_BEERS_percentiles.csv) | 4 | 11 |
| [T7_literature_comparison.csv](tables/main/T7_literature_comparison.csv) | 19 | 11 |

不混用不同量纲或年龄口径。受益人数行合计不是去重患者数，规模以T5公开行并集界为准。
