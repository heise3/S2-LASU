# S2-LASU: age differences in sulfonylurea dispensing in Medicare Part D

Release **v1.1.0** adds the post hoc glimepiride analysis and an annual geographical-composition decomposition. It preserves the original frozen v1.3 analysis from public release v1.0.0. This repository contains scientific code and aggregate results, not the unpublished manuscript or an indication of journal submission or acceptance.

Authors: Peng Liang, Jie Wu, BaoLong Li, XiangYan Wu, and Xiaona Zhu. Peng Liang and Jie Wu share first authorship.

## Contents

- `analysis/S2_LASU_final_v1_3/`: unchanged original frozen analysis, 16 main tables, 100 supporting tables, F1–F4, corrected Beers definitions, and prior reproduction evidence.
- `addenda/glimepiride_v1_6/`: specification, byte-identical scientific code, 12 official CMS sulfonylurea extracts, all generated tables, two current presentation figures, and scientific QA.
- `addenda/geography_v1_7/`: exact annual arithmetic decomposition separating within-state differences, geographic volume composition, observed nonstate addition, and publication/suppression-universe residuals.
- `presentation/`: historical v1.0.0 presentation figures, retained for provenance. The current manuscript figure data and graphics are in `addenda/glimepiride_v1_6/figures/`.
- `compatibility/`: unchanged historical adapter code; not an alternative current entry.
- `reproduce.py`: unified verification and isolated new-addenda recomputation.
- `RIGHTS.md`: existing rights retained, with no additional reuse license.

## Verify the public package

Use Python 3.12 and the pinned versions in `requirements.txt`. Create the environment outside the frozen analysis directory.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py verify
```

Verification checks every release manifest entry and invokes the authoritative frozen v1.3 verification. It does not refit models.

## Self-contained recomputation of the new addenda

```sh
python reproduce.py recompute-addenda --workspace /absolute/path/to/new_replay_directory
```

The destination must not exist and must be outside this release directory. The entry reconstructs the original v1.6 relative execution layout using the included public CMS SU extracts and immutable original reference tables. It executes the unchanged scientific code, regenerates tables and figures, and then runs the geographical decomposition on the newly regenerated results. It also regenerates `MAIN_RESULTS.csv` as a deterministic projection of all model rows.

The replay compares every generated numeric/statistical CSV with the released reference and checks the two PNG figures pixel by pixel. `audit/REPLAY_STATUS.json`, `audit/TABLE_COMPARISON.csv`, and execution logs appear in the new workspace. Figure pixel identity depends on available fonts; if numeric checks pass but a font changes rendering, the report records `PASS_NUMERICS_FIGURE_FONT_REVIEW_REQUIRED`. Original figures remain available for visual comparison. PDF creation metadata can differ without changing content. No source-project cache or beneficiary-level data is needed for **these new addenda**.

This is not a fresh download and nationwide extraction of all original CMS files. Included extracts are published aggregate rows selected by the frozen SU definitions; source versions and hashes remain documented in the original frozen provenance. It is also not a replay of the full original prescriber/Beers pipeline. That older pipeline still requires the historical source-project inputs and layout specified in `analysis/S2_LASU_final_v1_3/README.md` and `reproduction/source_requirements.json`.

## Interpretation

The new primary estimand is the pooled volume-weighted within-state-year glimepiride-family share difference, +4.04 percentage points (95% CI 2.59–5.49), across 2013–2024. It is a level difference, not a per-year trend, a 2024 national difference, or a patient probability. It is a post hoc analysis: the added-state-model specification was frozen before fitting, after review of known national and combined-long-acting results. Neither this repository nor the timestamp represents prospective preregistration.

Glimepiride shares use 30-day fills divided by all sulfonylurea fills and include combination products. State weights reflect dispensing volumes classified by **prescriber location**, not the geographic distribution of unique beneficiaries. The under-65 Part D group is predominantly disability-eligible and is not clinically exchangeable with older beneficiaries. Comparisons cannot identify an age effect or Beers policy effect. Suppression is retained; missing values are not zero, and allocations cannot recover entirely omitted drug rows.

The geographical decomposition is an exact arithmetic reconciliation. National published aggregates and sums of state rows can differ because of geography coverage and publication/suppression universes. A remaining discrepancy must not be attributed solely to nonstate units without evidence. The 12-year pooled estimate must not be confused with a single-year comparison.

## Deprecated clidinium matching

Historical substring rules captured aclidinium and umeclidinium as clidinium products. **Affected old Beers tables, rankings, figures, and standalone historical scripts remain deprecated and must not be used.** The retained v1.3 effective definitions and corrected T6 outputs are authoritative. Corrected Beers percentiles are 78.79, 84.85, 84.85, and 78.79, all Q4; the old 75.76 value is invalid.

## Archiving and rights

Original release v1.0.0: https://doi.org/10.5281/zenodo.23727072 . This v1.1.0 release retains it and adds the new analyses without overwriting that historical record. Version-specific v1.1.0 DOI: https://doi.org/10.5281/zenodo.23732736 (reserved when this package was prepared; it resolves after archive publication).

No beneficiary-level records, unpublished manuscript, private author contact sheets, or publisher full-text PDFs are included in the new addenda. Some unchanged original provider-summary tables contain publicly released NPIs, which are prescriber rather than patient identifiers. Historical v1.3 provenance records retain some original local paths as audit evidence; these are not portable commands. New addenda have no workstation-specific private paths.

No new reuse license is granted. Existing rights and third-party terms remain unchanged. See `RIGHTS.md`. Authors report no specific funding for this secondary analysis and no conflicts of interest.
