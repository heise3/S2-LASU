from pathlib import Path
import sys,re,json,hashlib
sys.dont_write_bytecode=True
import pandas as pd,numpy as np
from definitions import SPECS
O=Path(__file__).resolve().parents[1];E=O/'evidence';T=O/'tables'
# Locate original table boundaries, not mentions in discussion or reference lists.
x=(E/'Beers_2012.txt').read_text();a=x.index('First-generation antihistamines (as single agent');b=x.index('Correction made after online publication',a);text={2012:x[a:b]}
for y in [2015,2019]:
 x=(E/f'Beers_{y}_plain.txt').read_text();a=x.index(f'Table 2. {y}');b=x.index('Table 3.',a);text[y]=x[a:b]
x=(E/'Beers_2023_plain.txt').read_text();text[2023]=x[x.index('--- PAGE 6 ---'):x.index('--- PAGE 13 ---')]
for y,s in text.items():(E/f'Table2_{y}_extracted.txt').write_text(s)
urls={2012:'https://pmc.ncbi.nlm.nih.gov/articles/PMC3571677/',2015:'https://doi.org/10.1111/jgs.13702',2019:'https://doi.org/10.1111/jgs.15767',2023:'https://doi.org/10.1111/jgs.18372'}
# Literal components are audited separately from the first inclusion of the whole drug class.
components={
'antihistamines':'brompheniramine chlorpheniramine cyproheptadine dimenhydrinate diphenhydramine doxylamine hydroxyzine meclizine promethazine triprolidine carbinoxamine clemastine',
'antidepressants':'amitriptyline amoxapine clomipramine desipramine doxepin imipramine nortriptyline paroxetine trimipramine protriptyline',
'antipsychotics':'aripiprazole brexpiprazole cariprazine chlorpromazine clozapine fluphenazine haloperidol lurasidone olanzapine paliperidone perphenazine pimavanserin quetiapine risperidone ziprasidone loxapine pimozide thioridazine thiothixene trifluoperazine prochlorperazine asenapine iloperidone lumateperone molindone',
'barbiturates':'butalbital phenobarbital primidone amobarbital butabarbital mephobarbital pentobarbital secobarbital',
'benzodiazepines':'alprazolam chlordiazepoxide clobazam clonazepam clorazepate diazepam estazolam lorazepam midazolam oxazepam temazepam triazolam flurazepam quazepam remimazolam',
'sulfonylureas':'glimepiride glyburide glipizide chlorpropamide gliclazide tolbutamide tolazamide acetohexamide',
'long_su':'glimepiride glyburide chlorpropamide',
'alpha1':'doxazosin prazosin terazosin','central_alpha':'clonidine guanfacine guanabenz methyldopa reserpine',
'zdrugs':'eszopiclone zaleplon zolpidem','androgens':'methyltestosterone testosterone',
'ppi':'dexlansoprazole esomeprazole lansoprazole omeprazole pantoprazole rabeprazole',
'antispasmodics':'atropine clidinium dicyclomine hyoscyamine scopolamine propantheline',
'nsaids':'aspirin diclofenac diflunisal etodolac flurbiprofen ibuprofen indomethacin ketorolac meloxicam nabumetone naproxen oxaprozin piroxicam sulindac fenoprofen ketoprofen meclofenamate tolmetin',
'indomethacin_ketorolac':'indomethacin ketorolac','muscle_relaxants':'carisoprodol chlorzoxazone cyclobenzaprine metaxalone methocarbamol orphenadrine',
'antiparkinson':'benztropine trihexyphenidyl'}
rows=[]
for id,organ,label,pat,page,first,scope,qual in SPECS:
 aliases={'ergoloids':['ergoloid mesylates'],'estrogens':['estrogens','estradiol','estropipate'],'insulin_sliding':['insulin'],'thyroid':['desiccated thyroid'],'growth_hormone':['growth hormone','somatropin','somatrogon','somapacitan','somatrem'],'mineral_oil':['mineral oil']}
 tokens=aliases.get(id,components.get(id,id).split())
 for token in tokens:
  pat2=r'(?<![a-z])'+re.escape(token).replace(r'\ ',r'\s+')+r'(?![a-z])';ys=[y for y,s in text.items() if re.search(pat2,s,re.I)]
  # Explicit naming within a broad class is NOT necessarily new class coverage.
  rows.append(dict(entry=id,component=token,explicit_Table2_versions=';'.join(map(str,ys)),earliest_explicit_Table2_reviewed=min(ys) if ys else 'UNVERIFIED',class_criterion_first_reviewed=first,first_ever='UNVERIFIED',source_url=urls[min(ys)] if ys else '',note='Literal Table2 audit; class coverage may predate explicit naming; absence here does not prove absence from other Beers tables'))
pd.DataFrame(rows).to_csv(T/'component_version_audit.csv',index=False)
# Compact historical basis for every entry, with source/table locator and scope updates.
cat=pd.read_csv(T/'drug_criteria_manifest.csv');cat['historical_basis']=[f'AGS {int(y)} Table 2; see evidence/Table2_{int(y)}_extracted.txt' for y in cat.first_Table2_family_reviewed];cat['historical_source_url']=[urls[int(y)] for y in cat.first_Table2_family_reviewed]
cat['first_any_Beers_reviewed']=cat.first_Table2_family_reviewed.astype(str)
cat.loc[cat.entry.eq('aspirin'),'first_any_Beers_reviewed']='2012 (Table4 caution)'
cat.loc[cat.entry.eq('rivaroxaban'),'first_any_Beers_reviewed']='2015 (Table6 renal); 2019 (Table4 caution); 2023 (Table2 avoid)'
cat.loc[cat.entry.eq('warfarin'),'first_any_Beers_reviewed']='2015 (Table5 interactions); 2023 (Table2 initiation criterion)'
cat.to_csv(T/'drug_criteria_manifest.csv',index=False)
# Final primary filtering uses generic-name thresholds; preserve the original audit as well.
d=pd.read_csv(T/'matched_published_rows.csv.gz',dtype={'Prscrbr_Geo_Cd':str});n=d[d.Prscrbr_Geo_Lvl.eq('National')].drop_duplicates(['year','source_row']);v=n.groupby('Gnrc_Name').GE65_Tot_30day_Fills.sum().rename('national_ge65_2013_2024').reset_index();v['low_volume']=v.national_ge65_2013_2024.lt(100000);v.to_csv(T/'generic_volume_audit.csv',index=False)
# Compare rule endpoint scenarios, including complete subsets and zero-log losses.
c=pd.read_csv(T/'K2_all_coefficients.csv');c=c[c.term.eq('old_t')&c.model.eq('trend')];main=c[c.scenario.eq('observed')].set_index('entry');out=[]
for ent,g in c.groupby('entry'):
 ep=g[g.scenario.isin(['primary_small_lower','primary_small_upper','old_lower_young_upper','old_upper_young_lower'])];b=main.loc[ent,'coefficient'];out.append(dict(entry=ent,main_beta=b,endpoint_beta_min=ep.coefficient.min(),endpoint_beta_max=ep.coefficient.max(),all_four_same_sign=bool((ep.coefficient*b>0).all()),all_four_CI_same_direction_excludes0=bool((ep.ci_high<0).all() if b<0 else (ep.ci_low>0).all()),n_endpoint_pairs_min=ep.n_cells.min()/2,n_endpoint_pairs_max=ep.n_cells.max()/2,interpretation='four endpoint scenarios, not global sharp coefficient bounds; zero endpoints excluded from log models'))
pd.DataFrame(out).to_csv(T/'suppression_sensitivity_summary.csv',index=False)
print('Version audit',len(rows),'components; low-volume Gnrc_Name',int(v.low_volume.sum()),'of',len(v))
