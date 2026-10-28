# v1.6 glimepiride附加分析冻结规格

**version**

glimepiride_addendum_v1.6

**frozen_utc**

2026-10-28T12:54:04.932211+00:00

**status_at_freeze**

SPECIFICATION_FROZEN_BEFORE_NEW_GLI_STATE_MODELS

**context**

Post hoc addendum motivated by review of known national and long-SU results; not prospective preregistration; new glimepiride state outcomes not inspected before this freeze.

**years**

[2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

**states**

Same 50-state code list as v1; DC/territories/foreign/nonstate aggregates excluded with ledger

**ages**

["ge65", "lt65"]

**outcome**

100 * glimepiride-family 30-day fills / all SU 30-day fills; same case-insensitive generic matching and combinations as frozen LASU; do not silently narrow to pure single-ingredient glimepiride

**primary**

Published age-visible rows only; both ages use same visible drug-row universe; missing age volumes omitted, not set to zero; total-minus-ge65 for lt65.

**model**

Weighted linear y = state-by-year fixed effect + beta*old. No time interaction in primary level estimand; weights age-specific observed SU fills.

**estimand**

Pooled within-state-year older-minus-younger share difference in percentage points. Equivalent paired-gap mean weighted by w_old*w_young/(w_old+w_young); not equal-state mean or patient probability.

**inference**

State-cluster sandwich, full-rank CR1 inherited: G/(G-1)*(N-1)/(N-(number_state_year_FE+number_age_terms)); t(G-1) two-sided95% CI. Independent paired WLS check with same correction.

**periods**

{"2013-2018": [2013, 2018], "2019-2022": [2019, 2022], "2023-2024": [2023, 2024]}

**period_model**

Joint model with state-year FE plus three old*period indicators; estimate three descriptive levels. No post-policy effect claim, no causal contrast or multiplicity-selected period.

**primary_sensitivities**

["primary_small_lower", "primary_small_upper", "old_lower_young_upper", "old_upper_young_lower", "same_original_103_fully_visible_state_years"]

**suppression**

Reuse exact rule_bounds from v1.1: U=min(120,F-max(C-10,0)); star ge65 small, hash lt65 small. All-age total conserved. Recompute weights with scenario SU volumes. Four cases are coupled allocations, not mathematical global bounds.

**additional_suppression_diagnostics**

["target_share_old_low_young_high", "target_share_old_high_young_low"]

**ER_XL**

Reclassify glipizide ER/XL long versus short using inherited flag, recompute glimepiride/all-SU and assert exact invariance. Report NOT_APPLICABLE_AS_DISTINCT_GLI_ESTIMAND. Legacy 42% attenuation and 103-subset CI-crossing describe old long-SU trend only; do not relabel as new glimepiride sensitivity. No unrequested denominator exclusion.

**coverage**

Keep every valid published state-age-year; require paired ages and positive SU volume; all exclusions logged. Verify original complete subset exactly103 state-years/41states before fitting.

**descriptives**

All12 national family shares, age gaps, exact arithmetic endpoint decomposition including chlorpropamide residual; enrollee rates are all-enrollee rates, not patient risks. State annual positive counts; number of states positive in all12 observed annual points; 2019 and2024 observed gaps and suppression intervals.

**decision**

Primary beta<=1e-8: national-only fallback, explicitly report state result. Primary beta>0 but CI crosses0: WEAK. Positive CI and all four allocation CIs>0: SUPPORTED_STATE_LEVEL; otherwise mixed sensitivity explicitly reported. Averages never justify every state/every year. Fully-visible result described regardless direction.

**figures**

F1 two panels: three molecule shares by age; age gaps with glimepiride emphasized, glyburide and longSU reference. Beers2015/2019/2023 vertical references only. F2 all50 states: dumbbell of observed glimepiride share gaps2019 vs2024 sorted by2024, split25+25 for legibility; no CI implied. Suppression interval dataset and width extremes retained, no unsupported claim all narrow.

**manuscript**

New writing_v1_6 and updated cover letter, <=700main words,<=7refs,2figures,no abstract/supplement. Mention noncomparability and possible renal/clinical composition, no measured CKD effect. Do not claim guidelines caused change or imply patient probabilities. Preserve all old outputs; no submission, upload, DOI replacement or release mutation.

**validation**

Validate cached inputs against manifests, reproduce national T1 and original long-SU panel denominators, independent paired-vs-FE coefficient and covariance check, exact ER invariance, row-level volume conservation, source-bound main/cover assertions, protected hashes, rendering and word counts.
