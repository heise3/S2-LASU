# Glimepiride addendum v1.6

This post hoc descriptive addendum was specified after review of known national and combined-long-acting results; its additional state-model specification was frozen before fitting. It is not a prospective preregistration.

Primary result: pooled, volume-weighted within-state-year glimepiride-family share difference, +4.04 percentage points (95% CI 2.59–5.49). This is not a 2024 estimate, a trend coefficient, patient risk, or causal Beers effect. Families include combination products.

The code is byte-identical to the completed v1.6 scientific code. The root `reproduce.py recompute-addenda --workspace NEW_DIRECTORY` stages its required relative layout from included official public sulfonylurea extracts and the retained frozen reference tables, then regenerates tables and figures. No source-project cache is needed for this addendum replay. Entire omitted CMS rows are not recovered.

`tables/MAIN_RESULTS.csv` is a deterministic projection of all 36 model coefficient rows. `LITERATURE_COMPARISON_v1_6.csv` is curated documentation, not a statistical output. Original publisher PDFs, manuscript text, private author sheets, and workstation-specific internal logs are excluded. Historical v1.3 original source requirements remain distinct.

The four suppression allocations conserve total age volume and recompute weights. Two additional target-share allocations are diagnostic corners, not mathematical global missing-data bounds. The original 103 fully visible state-years are used exactly. Reclassifying glipizide ER/XL cannot alter glimepiride/all-SU, so this check is invariant, not an additional sensitivity estimate.
