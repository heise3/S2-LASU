"""Weighted FE with state-cluster CR1; weighted random-intercept Gaussian REML."""
import numpy as np
import pandas as pd
from scipy.stats import t
from scipy.optimize import minimize_scalar
from scipy.linalg import cho_factor, cho_solve, LinAlgError

def fe_fit(d,model=2,post=None,correction='full_rank'):
    d=d.copy();d['t']=d.year-2013;d['old_t']=d.old*d.t
    names=['old','t','old_t'] if model==1 else ['old','old_t']
    if post is not None:
        d['old_post']=d.old*(d.year>=post);names.append('old_post')
    X=d[names].to_numpy(float);y=d.share_pct.to_numpy(float);w=d.su_observed.to_numpy(float)
    assert np.isfinite(X).all() and np.isfinite(y).all() and (w>0).all()
    w=w/w.mean()
    g=pd.factorize(d.state if model==1 else d.state+'_'+d.year.astype(str))[0]
    c=pd.factorize(d.state)[0];G=c.max()+1;ng=g.max()+1;n=len(d)
    wg=np.bincount(g,weights=w);ym=np.bincount(g,weights=w*y)/wg
    xm=np.column_stack([np.bincount(g,weights=w*X[:,j])/wg for j in range(X.shape[1])])
    Xt=X-xm[g];yt=y-ym[g];bread=np.linalg.inv(Xt.T@(w[:,None]*Xt))
    beta=bread@(Xt.T@(w*yt));u=yt-Xt@beta
    scores=np.column_stack([np.bincount(c,weights=w*Xt[:,j]*u,minlength=G) for j in range(len(names))])
    k=ng+len(names);kadj=k if correction=='full_rank' else len(names)
    factor=G/(G-1)*(n-1)/(n-kadj)
    cov=factor*bread@(scores.T@scores)@bread
    se=np.sqrt(np.maximum(np.diag(cov),0));crit=t.ppf(.975,G-1)
    rows=[]
    for j,name in enumerate(names):
        rows.append(dict(term=name,coefficient=beta[j],se=se[j],ci_low=beta[j]-crit*se[j],ci_high=beta[j]+crit*se[j],p_value=2*t.sf(abs(beta[j]/se[j]),G-1),n_cells=n,n_states=G,n_FE_groups=ng,full_rank=k,df_cluster=G-1,CR1_factor=factor,correction=correction,model=model,post_start=post))
    # Influence weights verify estimates and enable fixed-weight suppression bounds.
    influence=bread@(Xt.T*w)
    assert np.allclose(influence@y,beta,atol=1e-8)
    return rows,dict(beta=beta,cov=cov,names=names,influence=influence,data=d)

def weighted_logit_reml(p,continuity=.5):
    """Exact marginal REML via Woodbury sufficient statistics; no fill-level expansion."""
    p=p.copy();s=p.su.to_numpy(float);L=p.long.to_numpy(float)
    z=np.log((L+continuity)/(s-L+continuity));w=s/s.mean()
    cat,levels=pd.factorize(p.specialty,sort=True);st,states=pd.factorize(p.state,sort=True)
    n=len(p);k=len(levels);G=len(states)
    Wc=np.bincount(cat,weights=w,minlength=k);Wcz=np.bincount(cat,weights=w*z,minlength=k)
    Ws=np.bincount(st,weights=w,minlength=G);Wsz=np.bincount(st,weights=w*z,minlength=G)
    U=np.zeros((G,k));np.add.at(U,(st,cat),w)
    zz=float(np.sum(w*z*z));logdetD=-np.log(w).sum()
    def profile(lam,details=False):
        a=lam/(1+lam*Ws)
        A=np.diag(Wc)-U.T@(a[:,None]*U);b=Wcz-U.T@(a*Wsz)
        try: cf=cho_factor(A,lower=True,check_finite=True)
        except LinAlgError: return np.inf
        ld=2*np.log(np.diag(cf[0])).sum()
        beta=cho_solve(cf,b);rss=zz-np.sum(a*Wsz**2)-b@beta
        if rss<=0:return np.inf
        sig=rss/(n-k);obj=(n-k)*np.log(sig)+logdetD+np.log1p(lam*Ws).sum()+ld
        if details:return beta,sig,lam*sig,cho_solve(cf,np.eye(k))*sig,a*(Wsz-U@beta),obj
        return obj
    opt=minimize_scalar(lambda q:profile(np.exp(q)),bounds=(-22,12),method='bounded',options={'xatol':1e-7})
    lam=float(np.exp(opt.x));zero=profile(0)
    if zero<=opt.fun:lam=0
    beta,sig,tau,cov,blup,obj=profile(lam,True)
    assert opt.success and np.isfinite(beta).all()
    wm=float(np.median(w));ref='Internal Medicine' if 'Internal Medicine' in levels else levels[np.argmax(Wc)];ri=list(levels).index(ref)
    fixed=[]
    for j,name in enumerate(levels):
        delta=beta[j]-beta[ri];se=np.sqrt(max(cov[j,j]+cov[ri,ri]-2*cov[j,ri],0))
        fixed.append(dict(specialty=name,reference=ref,logit_level=beta[j],contrast_logit=delta,se=se,ci_low=delta-1.96*se,ci_high=delta+1.96*se,n_prescribers=int((cat==j).sum())))
    meta=dict(n_prescribers=n,n_states=G,n_specialties=k,continuity=continuity,mean_SU_volume=s.mean(),median_SU_volume=np.median(s),tau2_state=tau,sigma2_at_mean_volume=sig,lambda_variance_ratio=lam,ICC_mean_volume=tau/(tau+sig),ICC_median_volume=tau/(tau+sig/wm),optimizer_success=bool(opt.success),optimizer_loglambda=float(opt.x),REML_objective=obj,zero_variance_objective=zero,boundary_zero_state_variance=lam==0,zero_share_n=int((L==0).sum()),one_share_n=int((L==s).sum()))
    random=pd.DataFrame(dict(state=states,random_intercept_logit=blup))
    return meta,pd.DataFrame(fixed),random
