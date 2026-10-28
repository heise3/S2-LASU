from pathlib import Path
import os
os.environ.setdefault("MPLCONFIGDIR","/tmp/s2_v16_mpl")
# Academic Figure Skill Typography Baseline — COPY VERBATIM, place at TOP of script
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 8,
    "figure.titlesize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
})

# Academic Figure Skill Nature/Cell/Science Color Palette -- COPY VERBATIM
CATEGORICAL = ["#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666"]
CATEGORICAL_EXTENDED = [
    "#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666",
    "#4393C3", "#D6604D", "#5AAE61", "#B35806", "#9970AB", "#999999",
]
DIVERGING   = ["#2166AC", "#F7F7F7", "#B2182B"]
SEQUENTIAL  = ["#F7FBFF", "#6BAED6", "#08306B"]
ACCENT_RED  = "#B2182B"
GREY        = "#999999"
BLACK       = "#222222"

# Academic Figure Skill Export Baseline — COPY VERBATIM
mpl.rcParams.update({
    "pdf.fonttype": 42,         # TrueType font embedding
    "svg.fonttype": "none",     # editable text in SVG
    "savefig.bbox": "tight",    # trim whitespace
    "savefig.dpi": 300,
})

def save_cns_figure(fig, filename):
    """Standard Academic Figure Skill export: vector PDF + 300dpi PNG preview."""
    fig.savefig(f"{filename}.pdf", bbox_inches="tight", dpi=300)
    fig.savefig(f"{filename}.png", bbox_inches="tight", dpi=300)

import json, hashlib
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
O=Path(__file__).resolve().parents[1];T=O/'tables';F=O/'figures'
n=pd.read_csv(T/'national_annual_gaps.csv')
d=pd.read_csv(T/'state_2019_2024_figure_data.csv').sort_values('gap_pp_2024',ascending=False)
assert len(n)==12 and len(d)==50
COL={'glimepiride':CATEGORICAL[0],'glyburide':CATEGORICAL[4],'glipizide':CATEGORICAL[2]}
def export(fig,name):
    # Fixed physical dimensions supersede tight cropping so width stays exactly183mm.
    box=mpl.transforms.Bbox.from_bounds(0,0,*fig.get_size_inches())
    fig.savefig(F/(name+'.pdf'),bbox_inches=box)
    fig.savefig(F/(name+'.png'),bbox_inches=box,dpi=400)
fig,axs=plt.subplots(2,1,figsize=(183/25.4,153/25.4),sharex=True)
fig.subplots_adjust(left=.13,right=.97,bottom=.09,top=.91,hspace=.30)
for fam in ['glipizide','glimepiride','glyburide']:
    for age,ls,mk in [('ge65','-','o'),('lt65','--','s')]:
        axs[0].plot(n.year,n[fam+'_'+age],color=COL[fam],ls=ls,marker=mk,markersize=2.8,lw=1.15)
axs[0].set_ylabel('Share of all sulfonylurea\n30-day fills (%)');axs[0].set_ylim(0,70)
handles=[Line2D([0],[0],color=COL[x],label=x.capitalize(),lw=1.7) for x in ['glimepiride','glyburide','glipizide']]
handles += [Line2D([0],[0],color=BLACK,ls='-',marker='o',label='Age ≥65',markersize=3),Line2D([0],[0],color=BLACK,ls='--',marker='s',label='Age <65',markersize=3)]
handles += [Line2D([0],[0],color='#bdbdbd',ls=':',label='Beers updates',lw=.8)]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.995),ncol=3,fontsize=7,columnspacing=1.1)
axs[1].axhline(0,color=BLACK,lw=.85,zorder=1)
axs[1].plot(n.year,n.long_gap_pp,color=GREY,ls='--',lw=1,label='All long-acting agents')
for fam,lw,mk in [('glimepiride',1.9,'o'),('glyburide',1.1,'^')]:axs[1].plot(n.year,n[fam+'_gap_pp'],color=COL[fam],lw=lw,marker=mk,markersize=3,label=fam.capitalize())
axs[1].set_ylim(min(n.glyburide_gap_pp.min(),n.long_gap_pp.min())-1,5.5);axs[1].set_ylabel('Age ≥65 minus age <65\n(percentage points)');axs[1].set_xlabel('Year')
axs[1].text(.015,.95,'Older higher',transform=axs[1].transAxes,va='top',fontsize=7,color=BLACK)
axs[1].text(.015,.04,'Younger higher',transform=axs[1].transAxes,va='bottom',fontsize=7,color=BLACK)
for y,dx,dy in [(2019,0,.7),(2024,-.5,.65)]:
    v=n.set_index('year').loc[y,'glimepiride_gap_pp'];axs[1].annotate(f'{v:.1f}',(y,v),(y+dx,v+dy),fontsize=7,color=COL['glimepiride'],ha='center')
for i,ax in enumerate(axs):
    for yr in [2015,2019,2023]:ax.axvline(yr,ls=':',color='#bdbdbd',lw=.7,zorder=0)
    ax.set_xlim(2012.8,2024.25);ax.set_xticks([2013,2015,2017,2019,2021,2023,2024]);ax.text(-.115,1.02,'AB'[i],transform=ax.transAxes,fontweight='bold',fontsize=9)
axs[0].tick_params(labelbottom=False)
axs[1].legend(loc='lower right',bbox_to_anchor=(1,.04),fontsize=6.5)
export(fig,'F1_molecule_shares_and_age_gaps');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(183/25.4,186/25.4),sharex=True)
fig.subplots_adjust(left=.16,right=.98,bottom=.11,top=.94,wspace=.65)
for i,(ax,g) in enumerate(zip(axs,[d.iloc[:25],d.iloc[25:]])):
    yy=np.arange(len(g));ax.axvline(0,color=BLACK,lw=.8,zorder=0)
    for j,(_,r) in enumerate(g.iterrows()):ax.plot([r.gap_pp_2019,r.gap_pp_2024],[j,j],color='#bdbdbd',lw=.85,zorder=1)
    ax.scatter(g.gap_pp_2019,yy,marker='o',s=16,facecolors='white',edgecolors='#666666',linewidths=.8,zorder=2)
    ax.scatter(g.gap_pp_2024,yy,marker='s',s=15,color=COL['glimepiride'],zorder=3)
    ax.set_yticks(yy,g.state_name);ax.invert_yaxis();ax.tick_params(axis='y',length=0,labelsize=7)
    ax.set_xlim(min(d.gap_pp_2019.min(),d.gap_pp_2024.min())-.7,max(d.gap_pp_2019.max(),d.gap_pp_2024.max())+.7)
    ax.text(-.04,1.015,'AB'[i],transform=ax.transAxes,fontweight='bold',fontsize=9)
fig.legend(handles=[Line2D([0],[0],marker='o',color='none',markerfacecolor='white',markeredgecolor='#666666',label='2019'),Line2D([0],[0],marker='s',color='none',markerfacecolor=COL['glimepiride'],markeredgecolor=COL['glimepiride'],label='2024')],loc='upper center',ncol=2,bbox_to_anchor=(.57,.995),fontsize=8)
fig.supxlabel('Glimepiride share: age ≥65 minus age <65 (percentage points)',fontsize=8,y=.04)
export(fig,'F2_state_glimepiride_gaps_2019_2024');plt.close(fig)
(O/'audit/FIGURE_BUILD.json').write_text(json.dumps({'status':'RENDERED_REQUIRES_VISUAL_REVIEW','F1_mm':[183,153],'F2_mm':[183,186],'PNG_dpi':400,'all_national_years':12,'all_states':50,'F2_order':'2024 gap descending; first25 left and next25 right','source':'Recomputed addendum tables; no statistical annotation beyond frozen estimands','production_asset_review':'Skill LineTrend has cumulative area plots with simulated publication counts; PairedBoxScatter uses simulated subject data and paired t tests. Both are semantically incompatible. Reused project v1.5 line/dot figure grammar with skill typography/color/export baselines; new paired state endpoints, no new tests.'},indent=2)+'\n')
print('Figures rendered')

