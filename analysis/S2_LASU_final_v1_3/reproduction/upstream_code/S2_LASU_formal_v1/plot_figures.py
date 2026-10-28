"""Vector PDFs and 300-dpi PNGs from the saved analysis tables."""
from pathlib import Path
import os
O=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(O/'evidence/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd,numpy as np
T=O/'tables';F=O/'figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':11,'axes.titlesize':12,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':300})
colors={'ge65':'#B34B36','lt65':'#247B96'};labels={'ge65':'Age ≥65','lt65':'Age <65'}
n=pd.read_csv(T/'A1_national_long.csv');n=n[(n.metric=='fills30')&(n.scenario=='primary')]
def lines(ax,fam):
    for age in ['ge65','lt65']:
        d=n[(n.family==fam)&(n.age==age)].sort_values('year')
        ax.plot(d.year,d.share_pct,color=colors[age],marker='o',markersize=3.8,lw=1.8,label=labels[age])
        ax.fill_between(d.year,d.share_lower_pct,d.share_upper_pct,color=colors[age],alpha=.18,lw=0)
    for node in [2015,2019,2023]:
        ax.axvline(node,color='#909090',lw=.85,ls=(0,(3,3)),zorder=0)
        ax.text(node,.98,f'Beers {node}',rotation=90,va='top',ha='right',transform=ax.get_xaxis_transform(),fontsize=8,color='#666666')
    ax.set_xlim(2012.7,2024.3);ax.set_xticks([2013,2015,2017,2019,2021,2023,2024]);ax.tick_params(axis='x',labelsize=9)
    ax.set_xlabel('Year');ax.grid(axis='y',color='#e7e7e7',lw=.6);ax.set_axisbelow(True)
def save(fig,name):
    for ext in ['pdf','png']:fig.savefig(F/f'{name}.{ext}',bbox_inches='tight',facecolor='white')
    plt.close(fig)
fig,ax=plt.subplots(figsize=(7.3,4.6));lines(ax,'long');ax.set_ylim(0,60)
ax.set_ylabel('Long-acting share of all SU 30-day fills (%)')
ax.legend(frameon=False,loc='lower left',ncol=2)
fig.text(.12,.005,'United States, Medicare Part D • Published age-visible drug rows; bounds are not confidence intervals.',fontsize=8,color='#555555')
fig.tight_layout(rect=(0,.035,1,1));save(fig,'F1_national_long_acting_share')
fig,axes=plt.subplots(1,2,figsize=(10,4.4),sharey=True)
for ax,fam,title in zip(axes,['glimepiride','glyburide'],['A   Glimepiride family','B   Glyburide family']):
    lines(ax,fam);ax.set_title(title,loc='left');ax.set_ylim(0,55)
axes[0].set_ylabel('Family share of all SU 30-day fills (%)');axes[0].legend(frameon=False,loc='lower left')
fig.text(.08,.005,'Each denominator includes all sulfonylureas (SU). Combination products follow the verified generic-name classification.',fontsize=8,color='#555555')
fig.tight_layout(rect=(0,.04,1,1));save(fig,'F2_glimepiride_glyburide_share')
d=pd.read_csv(T/'A2_state_gaps_2024.csv').sort_values('gap_pp').reset_index(drop=True)
fig,ax=plt.subplots(figsize=(7.4,12.4));y=np.arange(len(d));cc=np.where(d.gap_pp>=0,colors['ge65'],colors['lt65'])
ax.hlines(y,d.gap_lower_pp,d.gap_upper_pp,color=cc,lw=1.5)
ax.scatter(d.gap_pp,y,c=cc,s=20,zorder=3)
ax.axvline(0,color='#777777',lw=.9);ax.set_yticks(y,d.state_name,fontsize=8.5)
ax.set_ylim(-1,len(d));ax.set_xlabel('Age ≥65 minus age <65 (percentage points)')
ax.set_title('2024 state long-acting SU share difference',loc='left',pad=12)
ax.grid(axis='x',color='#e7e7e7',lw=.6);ax.set_axisbelow(True)
ax.text(.02,.99,f'{int(d.gap_pp.gt(0).sum())}/{len(d)} states above zero\n{int(d.gap_lower_pp.gt(0).sum())}/{len(d)} remain above zero across suppression bounds',transform=ax.transAxes,va='top',fontsize=8.5,bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
fig.text(.04,.004,'Dots: published age-visible shares. Horizontal lines: conservative suppression bounds, not 95% CIs.\n50 states only; DC and other non-state units excluded. Bounds omit wholly unpublished drug rows.',fontsize=8,color='#555555')
fig.tight_layout(rect=(0,.045,1,1));save(fig,'F3_state_age_gap_2024')
print('Saved F1–F3 as vector PDF and 300-dpi PNG.')
