import numpy as np
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
