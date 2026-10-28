"""R1–R5 patch. Read v1; all mutations stay in the v1.1 directory."""
from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
import numpy as np,pandas as pd
from v1_analysis import base,STATE_CODES,aggregate
from models import fe_fit
O=Path(__file__).resolve().parents[1];V=O.parent/'S2_LASU_formal_v1';T=O/'tables';E=O/'evidence'
def save(d,name):
    d=d if isinstance(d,pd.DataFrame) else pd.DataFrame(d);d.to_csv(T/name,index=False,float_format='%.12g');return d
def rule_bounds(d):
    d=d.copy();F=d.Tot_30day_Fills;C=d.Tot_Clms;old=d.GE65_Tot_30day_Fills;m=old.isna();star=d.GE65_Sprsn_Flag.eq('*');hash_=d.GE65_Sprsn_Flag.eq('#')
    assert d.loc[m,'GE65_Sprsn_Flag'].isin(['*','#']).all()
    assert (F>=C-1e-6).all() and (F<=12*C+1e-6).all()
    U=np.minimum(120,F-np.maximum(C-10,0));assert (U>=0).all()
    d['primary_small_age']=np.where(m,np.where(star,'ge65','lt65'),'none')
    d['small_fills_upper']=U.where(m,np.nan)
    d['old_lower']=old.where(~m,np.where(star,0,F-U));d['old_upper']=old.where(~m,np.where(star,U,F))
    d['young_lower']=F-d.old_upper;d['young_upper']=F-d.old_lower
    assert (d.old_lower<=d.old_upper+1e-8).all()
    assert np.allclose(d.old_lower+d.young_upper,F) and np.allclose(d.old_upper+d.young_lower,F)
    return d
def family_mask(d,family):
    if family=='SU':return pd.Series(True,index=d.index)
    if family=='long':return d['class'].eq('long')
    return d.Gnrc_Name.str.contains(family,case=False,regex=True)
def run():
    national={};states={};allgeo={};boundslog=[];combos=[];er=[]
    for y in range(2013,2025):
        b=rule_bounds(base.load('B',y));b['year']=y
        allgeo[y]=b;national[y]=b[b.Prscrbr_Geo_Lvl.eq('National')].copy();states[y]=b[b.Prscrbr_Geo_Lvl.eq('State')&b.Prscrbr_Geo_Cd.isin(STATE_CODES)].copy()
        boundslog.append(b[b.GE65_Tot_30day_Fills.isna()])
        combos.append(b[b.Gnrc_Name.str.contains('/',regex=False)]);er.append(b[b.glipizide_er_xl])
    save(pd.concat(boundslog),'R2_suppressed_drug_row_bounds.csv')
    save(pd.concat(combos),'R3_excluded_combination_rows.csv');save(pd.concat(er),'R3_ER_XL_reclassified_rows.csv')
    names=pd.concat([x[['Gnrc_Name','Brnd_Name','class','glipizide_er_xl','year']] for x in allgeo.values()]).drop_duplicates();names['is_combination']=names.Gnrc_Name.str.contains('/',regex=False);save(names,'drug_definition_audit.csv')
    # R1: v1 visible numerator + rule-aware numerator bounds, both ages directly observed enrollment.
    den=pd.read_csv(T/'R1_enrollment_denominators.csv');den=den.set_index(['year','age'])
    rates=[]
    for y,d in national.items():
        for age in ['ge65','lt65']:
            v=d.GE65_Tot_30day_Fills if age=='ge65' else d.Tot_30day_Fills-d.GE65_Tot_30day_Fills
            prefix='old' if age=='ge65' else 'young';D=den.loc[(y,age),'enrollee_person_years']
            for family in ['SU','long','glimepiride','glyburide','glipizide']:
                m=family_mask(d,family);obs=v[m].sum();lo=d.loc[m,prefix+'_lower'].sum();hi=d.loc[m,prefix+'_upper'].sum()
                rates.append(dict(year=y,age=age,family=family,enrollee_person_years=D,fills30_observed=obs,fills30_rule_lower=lo,fills30_rule_upper=hi,rate_observed_per1000py=1000*obs/D,rate_rule_lower_per1000py=1000*lo/D,rate_rule_upper_per1000py=1000*hi/D,age_suppressed_rows=int(v[m].isna().sum())))
    r=save(rates,'R1_rates_long.csv');wide=r.pivot(index=['year','age','enrollee_person_years'],columns='family',values='rate_observed_per1000py').reset_index();save(wide,'R1_rates_wide.csv')
    changes=[]
    for (age,fam),g in r.groupby(['age','family']):
        g=g.set_index('year');end=g.loc[2024]
        for start in [2013,2019,2020]:
            x=g.loc[start];raw=100*(end.fills30_observed/x.fills30_observed-1);std=100*(end.rate_observed_per1000py/x.rate_observed_per1000py-1)
            changes.append(dict(age=age,family=fam,start_year=start,end_year=2024,raw_volume_change_pct=raw,standardized_rate_change_pct=std,denominator_change_pct=100*(end.enrollee_person_years/x.enrollee_person_years-1),direction_reversed=bool(raw*std<0),rate_change_lower_pct=100*(end.rate_rule_lower_per1000py/x.rate_rule_upper_per1000py-1),rate_change_upper_pct=100*(end.rate_rule_upper_per1000py/x.rate_rule_lower_per1000py-1)))
    changes=save(changes,'R1_direction_comparison.csv')
    # R2 four coupled endpoint allocations. Never independently assign ages inconsistent with all-age total.
    scenarios=['primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower']
    extras=['share_old_lower_young_upper','share_old_upper_young_lower']
    panels=[];coeff=[];rowalloc=[];allocation_qa=[]
    for scenario in scenarios+extras:
        rows=[]
        for y,d in states.items():
            d=d.copy();missing=d.GE65_Tot_30day_Fills.isna();star=d.GE65_Sprsn_Flag.eq('*');islong=d['class'].eq('long')
            if scenario=='primary_small_lower':v=np.where(star,d.old_lower,d.old_upper)
            elif scenario=='primary_small_upper':v=np.where(star,d.old_upper,d.old_lower)
            elif scenario=='old_lower_young_upper':v=d.old_lower
            elif scenario=='old_upper_young_lower':v=d.old_upper
            elif scenario=='share_old_lower_young_upper':v=np.where(islong,d.old_lower,d.old_upper)
            else:v=np.where(islong,d.old_upper,d.old_lower)
            d['old_imputed']=v;d['young_imputed']=d.Tot_30day_Fills-d.old_imputed
            assert np.allclose(d.loc[~missing,'old_imputed'],d.loc[~missing,'GE65_Tot_30day_Fills'])
            assert np.allclose(d.old_imputed+d.young_imputed,d.Tot_30day_Fills)
            allocation_qa.append(dict(scenario=scenario,year=y,n_missing=int(missing.sum()),min_age_volume=min(d.old_imputed.min(),d.young_imputed.min()),max_conservation_error=float((d.old_imputed+d.young_imputed-d.Tot_30day_Fills).abs().max())))
            z=d[missing].copy();z['scenario']=scenario;rowalloc.append(z)
            for code,g in d.groupby('Prscrbr_Geo_Cd'):
                for age,prefix in [('ge65','old'),('lt65','young')]:
                    S=g[prefix+'_imputed'].sum();L=g.loc[g['class'].eq('long'),prefix+'_imputed'].sum()
                    rows.append(dict(year=y,state=STATE_CODES[code],state_name=g.Prscrbr_Geo_Desc.iloc[0],age=age,old=int(age=='ge65'),su_observed=S,long_volume=L,share_pct=100*L/S,scenario=scenario))
        p=pd.DataFrame(rows);panels.append(p);rr,_=fe_fit(p,2)
        coeff += [q|dict(scenario=scenario,role='primary_four' if scenario in scenarios else 'supplementary_share_extreme') for q in rr]
    save(pd.concat(panels),'R2_endpoint_panels.csv');save(pd.concat(rowalloc),'R2_imputed_drug_rows.csv');save(allocation_qa,'R2_allocation_QA.csv')
    vpan=pd.read_csv(V/'tables/A2_state_age_panel.csv');complete=vpan[vpan.age_suppressed_rows.eq(0)].copy();save(complete,'R2_complete_state_year_age_panel.csv')
    rr,_=fe_fit(complete,2);coeff += [q|dict(scenario='complete_published_state_years',role='complete_subset') for q in rr]
    save(complete[['state','state_name','year']].drop_duplicates().sort_values(['state','year']),'R2_complete_state_years.csv')
    incl=complete.groupby(['state','state_name']).agg(n_state_years=('year','nunique'),years=('year',lambda x:','.join(map(str,sorted(set(x)))))).reset_index();save(incl,'R2_complete_state_list.csv')
    cf=save(coeff,'R2_model2_coefficients.csv');main=cf[cf.role.eq('primary_four')&cf.term.eq('old_t')]
    decision='FRAGILE' if (main.coefficient<=1e-8).any() else ('ROBUST' if main.ci_low.gt(0).all() else 'DIRECTIONAL')
    (O/'R2_decision.json').write_text(json.dumps(dict(status=decision,reference_direction='positive',n_scenarios=4,n_states=50,n_cells=1200,definition='four primary small-cell/age-volume endpoint allocations; t49 state-cluster CI; full-rank CR1',complete_state_years=len(complete)//2,complete_states=complete.state.nunique(),does_not_claim_global_optimization=True),indent=2)+'\n')
    # R3 independent definition changes: include ER as long; exclude all observed combination generic names.
    ng=[];npan=[];r3coef=[]
    for definition in ['v1_primary','ER_XL_as_long','exclude_all_SU_combinations']:
        for y in range(2013,2025):
            for level,d in [('National',national[y]),('State',states[y])]:
                d=d.copy()
                if definition=='ER_XL_as_long':d.loc[d.glipizide_er_xl,'class']='long'
                if definition=='exclude_all_SU_combinations':d=d[~d.Gnrc_Name.str.contains('/',regex=False)]
                groups=[('',d)] if level=='National' else d.groupby('Prscrbr_Geo_Cd')
                for code,g in groups:
                    for row in aggregate(g,y,'long','fills30','primary'):
                        row['definition']=definition
                        if level=='National':ng.append(row)
                        else:row.update(state=STATE_CODES[code],state_name=g.Prscrbr_Geo_Desc.iloc[0]);npan.append(row)
        p=pd.DataFrame(npan);p=p[p.definition.eq(definition)];rr,_=fe_fit(p,2);r3coef += [q|dict(definition=definition) for q in rr]
    ng=save(ng,'R3_national_age_long.csv');save(npan,'R3_state_age_panels.csv');save(r3coef,'R3_model2_coefficients.csv')
    seq=[]
    for (y,definition),g in ng.groupby(['year','definition']):
        g=g.set_index('age');a=g.loc['ge65'];b=g.loc['lt65'];seq.append(dict(year=y,definition=definition,ge65_share_pct=a.share_pct,lt65_share_pct=b.share_pct,gap_pp=a.share_pct-b.share_pct,ge65_SU=a.su_observed,lt65_SU=b.su_observed,ge65_long=a.target_observed,lt65_long=b.target_observed,age_suppressed_rows=a.age_suppressed_rows))
    save(seq,'R3_national_annual.csv')
    # R4 inherits continuous hinge estimates; endpoint changes are explicitly separate.
    sl=pd.read_csv(V/'tables/A1_segment_slopes.csv');sl=sl[sl.metric.eq('fills30')&sl.scenario.eq('primary')&sl.family.eq('long')]
    save(sl,'R4_v1_segment_slopes_long.csv');sl=sl.pivot(index=['start','end','segment'],columns='age',values='slope_pp_per_year').reset_index()
    annual=pd.read_csv(V/'tables/A1_national_annual.csv');a=annual[annual.metric.eq('fills30')&annual.scenario.eq('primary')&annual.family.eq('long')].set_index('year')
    sl['observed_gap_at_start']=[a.loc[y,'gap_pp'] for y in sl.start];sl['observed_gap_at_end']=[a.loc[y,'gap_pp'] for y in sl.end];sl['observed_gap_change']=sl.observed_gap_at_end-sl.observed_gap_at_start
    save(sl,'R4_segment_slopes.csv')
    # R5 union bounds for published age-count-visible rows, not hidden products.
    d=national[2024];items=[]
    for family in ['glimepiride','glyburide','long']:
        g=d[family_mask(d,family)];assert g.GE65_Tot_Benes.notna().all();largest=g.loc[g.GE65_Tot_Benes.idxmax()]
        low=g.GE65_Tot_Benes.max();high=g.GE65_Tot_Benes.sum();D=den.loc[(2024,'ge65'),'enrollee_person_years']
        items.append(dict(year=2024,family=family,n_published_rows=len(g),published_union_lower=low,published_union_upper=high,possible_duplicate_excess_max=high-low,largest_row_generic=largest.Gnrc_Name,largest_row_brand=largest.Brnd_Name,combination_row_count=int(g.Gnrc_Name.str.contains('/',regex=False).sum()),combination_beneficiary_row_sum=g.loc[g.Gnrc_Name.str.contains('/',regex=False),'GE65_Tot_Benes'].sum(),lower_per1000_enrollee_py=1000*low/D,upper_per1000_enrollee_py=1000*high/D,scope='union of these published rows only; not a bound on omitted entire products'))
    save(items,'R5_beneficiary_union_bounds.csv');save(d[family_mask(d,'long')],'R5_long_drug_beneficiary_rows.csv')
    inputs=[O.parent/f'data/B_{y}_su.csv.gz' for y in range(2013,2025)]+[O.parent/'code/analyze.py',O.parent/'field_mapping.csv',O.parent/'matched_generic_names.csv',O.parent/'matched_generic_brand_names.csv',V/'code/run_analysis.py',V/'code/models.py']
    (E/'input_manifest.json').write_text(json.dumps([dict(path=str(p.relative_to(O.parent)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in inputs],indent=2)+'\n')
    print('R2',decision);print(main[['scenario','coefficient','ci_low','ci_high']].to_string(index=False));print('R1 reversals');print(changes[changes.direction_reversed].to_string(index=False))
if __name__=='__main__':run()
