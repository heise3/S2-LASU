# v1.7 geography decomposition

Status: PASS. Post hoc exact arithmetic audit; old analyses are unchanged.

All shares refer to glimepiride-family 30-day fills / all sulfonylurea 30-day fills. Geographic weights describe dispensing volumes, not beneficiary counts or residence distributions.

|Year|National gap|50-state pooled gap|Annual paired-weight within-state gap|Geographic weight component|Adding visible non50 units|Publication/suppression residual|
|---|---:|---:|---:|---:|---:|---:|
|2013|2.448951|2.520694|3.170439|-0.649745|-0.063803|-0.007939|
|2019|3.427341|3.580924|4.372307|-0.791382|-0.151845|-0.001738|
|2024|2.563222|2.823918|3.909925|-1.086008|-0.251496|-0.009199|

All differences are percentage points. The last four columns sum exactly to the national difference. Within-state plus geographic weight columns sum exactly to the 50-state pooled difference.

For each year, p_o and p_y are state shares; a_o and a_y are age-specific normalized state SU volumes; q is proportional to V_o V_y/(V_o+V_y). W=sum[q(p_o-p_y)] and C=sum[(a_o-q)p_o]−sum[(a_y-q)p_y]. Thus D50=W+C. CSV also supplies symmetric Kitagawa and younger-volume standardizations; no decomposition is uniquely causal.

Pooled 2013–2024 estimate: 4.039863824843 pp, matching v1.6. It is the annual within-state differences averaged using annual sums of unnormalized paired weights, not the 2024 within-state or national value.

Geographic weight component is negative in all 12 years. Reweighting older-group state shares by younger-group SU-volume weights increases the older-group mean. This supports a volume-composition explanation for the smaller pooled age difference; it does not establish beneficiary residence or causal selection.

National-minus-50-state difference is not assigned wholly to excluded units. The exact bridge separates (i) adding visible published rows for DC, territories, overseas and unknown units and (ii) remaining national-versus-visible-subnational residual. The latter includes age-suppressed published rows at both national and subnational levels and national/subnational publication-universe or rounding discrepancies. Entire omitted geography-product cells cannot be allocated to ages from these public tables.

The final volume column equals column 2 plus column 3 minus column 4; national suppressed age rows are omitted from both age groups just as in v1.6.

|Year|National minus published subnational all-age SU|All-age SU in age-suppressed subnational rows|All-age SU in age-suppressed national rows|National minus visible subnational SU|
|---|---:|---:|---:|---:|
|2013|1099.10|19175.20|0.00|20274.30|
|2019|1009.00|12695.10|1307.70|12396.40|
|2024|487.30|17938.70|0.00|18426.00|

Across 600 state-years, harmonic/young-volume ratio range 0.7781–0.9413, median 0.8853. Annual total-variation distance between normalized harmonic and young-volume weights range 0.0089–0.0146. Paired weight favors the smaller-volume age group but is not identical to young-group volume. Methods should give the exact formula instead of an unnecessary approximation.

Recommended Results: In 2024, the annual within-state difference was 3.91 percentage points, versus 2.56 nationally; age-specific geographic distributions of sulfonylurea dispensing volumes partly explained the difference. The 4.04-point estimate pools all 12 years.

Reproduce: python code/decompose.py --input-dir ../S2_LASU_glimepiride_addendum_v1_6 --output-dir /new/isolated/directory. Five CSV inputs are hashed before and after. No network access required.
