# S2-LASU: age differences in sulfonylurea dispensing in Medicare Part D

Code, frozen aggregate results, definitions, and reproducibility evidence for **Age Differences in Long-Acting Sulfonylurea Dispensing in Medicare Part D, 2013–2024**.

Authors: Peng Liang, Jie Wu, BaoLong Li, XiangYan Wu, and Xiaona Zhu. Peng Liang and Jie Wu share first authorship. This repository is a research resource; it is not a clinical decision tool or a statement that the manuscript has been published or accepted.

## What is available

- `analysis/S2_LASU_final_v1_3/`: the byte-for-byte frozen analysis package, including 16 main tables, 100 supporting tables, F1–F4, drug definitions, analysis code, environment pins, and prior complete-replay evidence.
- `analysis/S2_LASU_final_v1_3/code/reproduce.py`: the authoritative frozen analysis entry.
- `analysis/S2_LASU_final_v1_3/reproduction/upstream_code/`: source scripts used by the analysis modules, including acquisition and schema harmonization.
- `compatibility/S2_LASU_final_v1_2/code/`: historical compatibility code required by the complete replay. It is not an alternative current analysis entry.
- `presentation/`: the two figures used in the concise manuscript and their numerical plotting data. Manuscript Figure 1 combines national trends and drug-family differences; manuscript Figure 2 corresponds to the frozen analysis state comparison (F3).
- `CITATION.cff`: author and release metadata; no DOI is claimed.

## Verify this public release

Use Python 3.12 and the versions recorded in `requirements.txt` for the original analysis environment. Create a virtual environment outside the frozen analysis folder.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py verify
```

The command checks the public file manifest and the original frozen manifest, then verifies the canonical tables, corrected Beers definitions, and figures. It does **not** fit statistical models. The frozen analysis directory must remain unchanged, including its file set; do not create virtual environments or logs inside it.

## Complete statistical replay: additional inputs are required

This repository is **not a self-contained download of every original CMS cache and historical project output**. The small `verify` command works from this repository; full statistical recomputation requires the original source-project layout and cached inputs described in `analysis/S2_LASU_final_v1_3/README.md` and `reproduction/source_requirements.json`. The latter records 457 hashed source requirements. The historical adapter additionally expects the source project's prior-output provenance and layout; copying only those 457 files is not guaranteed to reconstruct that full project.

Once that original source-project layout is available, use the authoritative entry:

```sh
python analysis/S2_LASU_final_v1_3/code/reproduce.py preflight \
  --source-project /absolute/path/to/source_project
python analysis/S2_LASU_final_v1_3/code/reproduce.py recompute \
  --source-project /absolute/path/to/source_project \
  --workspace /absolute/path/to/source_project/work/new_replay \
  --audit-dir /absolute/path/to/source_project/work/new_audit \
  --dry-run
```

The two output directories must not exist. Remove `--dry-run` only to execute the full pipeline. Prior full-replay evidence is preserved in the frozen package; the GitHub publication step checks packaging and integrity and does not constitute a new statistical rerun. Some provenance records retain original local paths as historical evidence, not portable commands.

## Data and interpretation

CMS public sources are Medicare Part D Prescribers by Geography and Drug, by Provider and Drug, and official Part D enrollment tables. Dataset URLs and versions are in `analysis/S2_LASU_final_v1_3/provenance/CMS_source_manifest.json` and the associated evidence files. These are published aggregates, not beneficiary-level records. Some supporting provider summaries contain publicly released National Provider Identifiers; they are prescriber identifiers, not patient identifiers. CMS suppression is retained; omitted cells must not be interpreted as zero.

The primary outcome is long-acting sulfonylurea 30-day fills divided by all sulfonylurea 30-day fills. The under-65 Part D group is predominantly disability-eligible. Interactions describe age-group trend differences, not a causal Beers policy effect. The 103 fully visible state-year sensitivity has a confidence interval crossing zero; ER/XL reclassification attenuates the estimate. See the frozen report for the full limitations.

## Deprecated clidinium matching

Historical substring rules incorrectly captured aclidinium and umeclidinium as clidinium products. **Do not use affected old tables, rankings, plots, or standalone historical scripts as current results.** `DEPRECATED.md`, effective definitions, the corrected T6 tables, and the unified entry identify the valid analysis. The four corrected Beers percentiles are 78.79, 84.85, 84.85, and 78.79; each is in Q4. The old 75.76 percentile is not valid.

## Publication and rights

This repository does not include the unpublished manuscript, private author contact sheets, or internal writing-review files. Authors report no specific funding for this secondary analysis and no conflicts of interest. CMS source materials retain their original provenance and applicable terms. No new license for third-party materials is asserted here; a reuse license for project-authored code has not been specified. Repository publication does not register a protocol or assign a DOI.
