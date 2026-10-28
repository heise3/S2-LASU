# v1.7 geographic decomposition specification

Frozen 2026-10-28T13:41:20.310475+00:00 before calculating new decomposition tables. This is a post hoc descriptive check prompted by reviewer comments; prior outcomes and supplied example values are already known. It is not prospective preregistration.

**pooled50**: D50=sum(a_o*p_o)-sum(a_y*p_y)

**within**: W=sum(q*(p_o-p_y))

**composition**: C=sum((a_o-q)*p_o)-sum((a_y-q)*p_y); D50=W+C

**kitagawa**: Kwithin=sum((a_o+a_y)/2*(p_o-p_y)); Kcomposition=sum((a_o-a_y)*(p_o+p_y)/2); D50=Kwithin+Kcomposition

**young_standardization**: Ywithin=sum(a_y*(p_o-p_y)); Ycomposition=sum((a_o-a_y)*p_o); D50=Ywithin+Ycomposition

**national_bridge**: Dnational=D50+E+R, E=Dall_published_subnational_visible-D50; R=Dnational-Dall_published_subnational_visible. Thus Dnational=W+C+E+R.

- Geographic weights are prescription-volume shares, not beneficiary residence distributions.
- E measures adding the observed published non-50-state units; R cannot be attributed exclusively to non-state units and will be audited for age-suppressed published rows plus national-vs-published-subnational total-volume discrepancy.
- Share differences are nonlinear, so geographic addition effects are arithmetic, reference-dependent.
- Annual within-state weighted differences are distinct from pooled2013-2024 beta4.04; pooled estimate equals annual W weighted by each year total unnormalized harmonic weight.
- No causal interpretation; do not claim equal coverage of suppressed or unreported cells.
- Harmonic weights are not declared approximately young-volume weights until ratios/normalized-weight distances are summarized.
