"""Use names only, never load volume/age outcomes; freeze mapping before model fitting."""
from pathlib import Path
import sys,re,json,hashlib,datetime,shutil
sys.dont_write_bytecode=True
import pandas as pd
O=Path(__file__).resolve().parents[1];ROOT=O.parents[1];T=O/'tables';E=O/'evidence';B=O.parent/'S2_BEERS_precheck'
assert not (E/'mapping_freeze.json').exists(),'Frozen already; do not replace after seeing outcomes'
m=pd.read_csv(T/'therapeutic_class_map_frozen.csv');names=set();inputhash=[]
for year in range(2013,2025):
 f=ROOT/f'work/full_csv/B_{year}.csv';d=pd.read_csv(f,usecols=['Gnrc_Name'],dtype=str,keep_default_na=False);names.update(d.Gnrc_Name)
 inputhash.append(dict(year=year,path=str(f.relative_to(ROOT)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(E/'B_input_hashes.json').write_text(json.dumps(inputhash,indent=2))
def norm(x):return re.sub(r'[^a-z0-9]+',' ',x.lower()).strip()
# Ingredient synonym normalization is frozen before volumes are loaded.
alias={'insulin aspart human':['insulin aspart'],'insulin lispro human':['insulin lispro'],'insulin glulisine human':['insulin glulisine'],'insulin regular human':['insulin regular'],'nph insulin human':['insulin nph'],'nph insulin pork':['insulin nph'],'glyburide':['glibenclamide'],'meperidine':['pethidine'],'aspirin':['acetylsalicylic acid']}
(E/'ingredient_aliases_frozen.json').write_text(json.dumps(alias,indent=2))
memberrows=[];match=[]
for c in sorted(set(';'.join(m.ATC_classes).split(';'))):
 j=json.loads((E/f'ATC_{c}_members.json').read_text());members=j.get('drugMemberGroup',{}).get('drugMember',[]);assert members,c
 for r in members:
  x=r['minConcept'];attrs=r.get('nodeAttr',[]);memberrows.append(dict(ATC_class=c,**x,attributes=json.dumps(attrs)))
  parts=[norm(s) for s in x['name'].split(' / ')];patterns=[]
  for s in parts:
   alts=[s]+alias.get(s,[]);patterns.append(re.compile(r'(?<![a-z0-9])(?:'+'|'.join(re.escape(a) for a in alts)+r')(?![a-z0-9])'))
  for g in sorted(names):
   if all(p.search(norm(g)) for p in patterns):match.append(dict(Gnrc_Name=g,ATC_class=c,rxcui=x['rxcui'],RxNorm_name=x['name'],TTY=x['tty']))
pd.DataFrame(memberrows).to_csv(T/'ATC_members_frozen.csv',index=False);mch=pd.DataFrame(match);mch.to_csv(T/'generic_atc_matches_frozen.csv',index=False)
pd.DataFrame({'Gnrc_Name':sorted(names-set(mch.Gnrc_Name))}).to_csv(T/'names_outside_selected_ATC_or_unmapped.csv',index=False)
n=pd.read_csv(B/'tables/drug_filtered/matched_names_by_year.csv',keep_default_na=False);n=n[n.entry.isin(m.entry)];n.to_csv(T/'numerator_names_frozen.csv',index=False)
exceptions=[]
for _,r in m.iterrows():
 accepted=set(mch[mch.ATC_class.isin(r.ATC_classes.split(';'))].Gnrc_Name)
 ex=n[n.entry.eq(r.entry)&~n.Gnrc_Name.isin(accepted)].copy();exceptions.append(ex)
pd.concat(exceptions).to_csv(T/'numerator_membership_exceptions_frozen.csv',index=False)
shutil.copy2(B/'tables/drug_filtered/drug_criteria_manifest.csv',T/'inherited_numerator_manifest.csv')
files=[O/'analysis_contract.json',T/'therapeutic_class_map_frozen.csv',T/'ATC_members_frozen.csv',T/'generic_atc_matches_frozen.csv',T/'numerator_names_frozen.csv',T/'numerator_membership_exceptions_frozen.csv',E/'ingredient_aliases_frozen.json',Path(__file__)]+list(E.glob('ATC_*_members.json'))
freeze=dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_share_results_seen=False,n_unique_generic_names=len(names),n_matched_generic_names=mch.Gnrc_Name.nunique(),n_criteria=33,n_benchmark=1,files=[dict(path=str(p.relative_to(O)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
(E/'mapping_freeze.json').write_text(json.dumps(freeze,indent=2));print({k:v for k,v in freeze.items() if k!='files'});print('Membership exceptions',len(pd.concat(exceptions).drop_duplicates(['entry','Gnrc_Name','Brnd_Name'])))
