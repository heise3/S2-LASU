# S2-LASU v1.7 geographic decomposition

This isolated addendum explains the difference between national and within-state glimepiride-family shares. It does not refit v1.6 models or change earlier deliverables.

- `DECOMPOSITION_SPEC.json` and `SPEC_SHA256`: algebra specification frozen before the new calculations; explicitly post hoc.
- `DECOMPOSITION_REPORT.md`: results, formulas, reporting-universe caveats and text guidance.
- `tables/annual_geographic_decomposition.csv`: all 12 annual exact decompositions.
- `tables/state_year_weights_and_components.csv`: all 600 state-year weights and components.
- `tables/publication_universe_coverage.csv`: national, 50-state, non50-unit and combined published coverage.
- `tables/national_subnational_drug_volume_audit.csv`: product-specific all-age publication discrepancies.
- `tables/excluded_geographic_units.csv`: all non50-state units by year.
- `audit/QA.json`: independent loop/algebra checks and five input hashes.
- `audit/REPLAY_VERIFICATION.json`: five CSVs reproduced byte for byte in a separate output folder; seven protected source files remain unchanged.

## Reproduction

Use Python with numpy and pandas:

```bash
python code/decompose.py --input-dir ../S2_LASU_glimepiride_addendum_v1_6 --output-dir /new/isolated/output
```

The five required input CSVs are listed in `code/decompose.py`; no network, credentials, beneficiary-level records or raw national data download is needed. The output directory must differ from the input directory. The default input is the sibling v1.6 addendum and the default output is this directory; provide a new output path to preserve packaged outputs. Output figures are unchanged in the writing revision.

The national bridge separates volume-composition effects from observed non50-unit inclusion and the remaining publication/suppression discrepancy. Geographic volume weights cannot establish the geographic distribution of individual beneficiaries. A pooled 2013–2024 estimate is not a single-year estimate.
