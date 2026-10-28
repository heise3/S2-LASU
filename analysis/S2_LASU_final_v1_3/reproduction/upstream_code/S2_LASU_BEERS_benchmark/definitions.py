"""Frozen criterion-level identities derived from AGS 2023 Table 2 (PDF pp6–12).
No dose, duration, diagnosis or treatment-sequence inference is made from names.
Historical dates mean earliest confirmed appearance in the four reviewed editions,
not first-ever Beers inclusion. Main entries preserve Table-2 rows, including overlap.
"""
from pathlib import Path
import re
# id, organ, label, regex, 2023 PDF page, first Table2 family, full present scope, qualification
SPECS=[
('antihistamines','01 Antihistamines','First-generation antihistamines',r'brompheniramine|chlorpheniramine|cyproheptadine|dimenhydrinate|diphenhydramine|doxylamine|hydroxyzine|meclizine|promethazine|triprolidine|carbinoxamine|clemastine',6,2012,2012,'Oral diphenhydramine restriction; acute allergic reaction exceptions; route not fully resolved'),
('nitrofurantoin','02 Anti-infective','Nitrofurantoin',r'nitrofurantoin',6,2012,2012,'CrCl <30 or long-term suppression not measurable; threshold changed from 60 in 2015'),
('aspirin','03 Cardiovascular','Aspirin (primary prevention criterion)',r'aspirin',6,2023,2023,'Primary prevention and initiation/deprescribing not measurable; previously caution in 2012'),
('warfarin','03 Cardiovascular','Warfarin',r'warfarin',6,2023,2023,'New starts for nonvalvular AF/VTE and exceptions not measurable; previous interaction criteria are different'),
('rivaroxaban','03 Cardiovascular','Rivaroxaban',r'rivaroxaban',7,2023,2023,'AF/VTE and duration not measurable; prior renal criterion 2015, caution 2019'),
('dipyridamole','03 Cardiovascular','Short-acting dipyridamole',r'^dipyridamole$',7,2012,2012,'Exclude aspirin/ER combination; oral/IV route not explicit'),
('alpha1','03 Cardiovascular','Peripheral alpha-1 blockers',r'doxazosin|prazosin|terazosin',7,2012,2012,'Hypertension indication not measurable'),
('central_alpha','03 Cardiovascular','Central alpha agonists',r'clonidine|guanfacine|guanabenz|methyldopa|reserpine',7,2012,2012,'Hypertension/first-line use not measurable; older low-use members included under class scope'),
('nifedipine','03 Cardiovascular','Immediate-release nifedipine',r'^nifedipine$',7,2012,2012,'ER/XL/CC brands excluded; residual generic brand formulation may be uncertain'),
('amiodarone','03 Cardiovascular','Amiodarone',r'amiodarone',7,2012,2012,'First-line AF and HF/LVH exception not measurable'),
('dronedarone','03 Cardiovascular','Dronedarone',r'dronedarone',7,2012,2012,'Permanent AF/HF severity not measurable'),
('digoxin','03 Cardiovascular','Digoxin',r'digoxin',8,2012,2015,'Dose >0.125 mg/day and first-line use not measurable; first-line scope expanded 2015'),
('antidepressants','04 CNS','Strongly anticholinergic antidepressants',r'amitriptyline|amoxapine|clomipramine|desipramine|doxepin|imipramine|nortriptyline|paroxetine|trimipramine|protriptyline',8,2012,2015,'2012 tertiary TCAs subset; 2015 broader named class; doxepin >6 mg/day not measurable'),
('antiparkinson','04 CNS','Anticholinergic antiparkinsonian agents',r'benztropine|trihexyphenidyl',8,2012,2012,'Benztropine oral restriction not fully resolved'),
('antipsychotics','04 CNS','Antipsychotics',r'aripiprazole|brexpiprazole|cariprazine|chlorpromazine|clozapine|fluphenazine|haloperidol|lurasidone|olanzapine|paliperidone|perphenazine|pimavanserin|quetiapine|risperidone|ziprasidone|loxapine|pimozide|thioridazine|thiothixene|trifluoperazine|prochlorperazine|asenapine|iloperidone|lumateperone|molindone',8,2012,2012,'FDA-approved indication exceptions and dementia behavior not measurable; class covers unlisted agents'),
('barbiturates','04 CNS','Barbiturates',r'butalbital|phenobarb|primidone|amobarbital|butabarbital|mephobarbital|pentobarbital|secobarbital',9,2012,2012,'Class membership; primidone explicitly listed in 2023; historical molecule date separate'),
('benzodiazepines','04 CNS','Benzodiazepines',r'alprazolam|chlordiazepoxide|clobazam|clonazepam|clorazepate|diazepam|estazolam|lorazepam|midazolam|oxazepam|temazepam|triazolam|flurazepam|quazepam|remimazolam',9,2012,2012,'Indication exceptions not measurable; includes combination products'),
('zdrugs','04 CNS','Z-drugs',r'eszopiclone|zaleplon|zolpidem',9,2012,2015,'2012 chronic >90 day restriction removed in 2015; annual aggregate cannot assess duration'),
('meprobamate','04 CNS','Meprobamate',r'meprobamate',9,2012,2012,'Exposure identifiable'),
('ergoloids','04 CNS','Ergoloid mesylates',r'ergoloid',9,2012,2012,'Exposure identifiable'),
('androgens','05 Endocrine','Androgens',r'methyltestosterone|(?<!methyl)testosterone',10,2012,2012,'Hypogonadism exception not measurable'),
('estrogens','05 Endocrine','Systemic estrogens',r'estradiol|estrogens|estropipate|mestranol|ethinyl estrad|ethin\.estr|eth estr|e\.estr',10,2012,2012,'Vaginal forms excluded where explicit; generic estradiol/Premarin route unresolved; primary entry NOT_ESTIMABLE'),
('insulin_sliding','05 Endocrine','Sliding-scale insulin criterion (short/rapid proxy)',r'^insulin (aspart|lispro|glulisine|regular)',10,2012,2012,'Cannot observe sliding-scale regimen or concurrent basal insulin: exposure proxy only; excludes premixes'),
('sulfonylureas','05 Endocrine','All sulfonylureas',r'glimepiride|glyburide|glibenclamide|glipizide|chlorpropamide|gliclazide|tolbutamide|tolazamide|acetohexamide',10,2012,2023,'Long agents 2012; glimepiride added 2019; all SU expanded 2023; therapy-line exceptions not measurable'),
('thyroid','05 Endocrine','Desiccated thyroid',r'thyroid,pork|thyroid \(pork\)|thyroid,desiccated',10,2012,2012,'Exclude levothyroxine and parathyroid hormone'),
('megestrol','05 Endocrine','Megestrol',r'megestrol',11,2012,2012,'Exposure identifiable'),
('growth_hormone','05 Endocrine','Growth hormone',r'somatropin|somatrogon|somapacitan|somatrem',11,2012,2012,'Established growth-hormone deficiency exception not measurable'),
('ppi','06 GI','Proton-pump inhibitors',r'dexlansoprazole|esomeprazole|lansoprazole|omeprazole|pantoprazole|rabeprazole',11,2015,2015,'>8 weeks and indication exceptions not measurable; combinations included'),
('metoclopramide','06 GI','Metoclopramide',r'metoclopramide',11,2012,2012,'Gastroparesis/duration exceptions not measurable'),
('antispasmodics','06 GI','GI anticholinergic antispasmodics',r'atropine|clidinium|dicyclomine|hyoscyamine|scopolamine|belladonna|propantheline',11,2012,2012,'Atropine ophthalmic excluded where explicit; mixed-route generic atropine excluded; combination ingredients may be abbreviated'),
('mineral_oil','06 GI','Oral mineral oil',r'^mineral oil$',11,2012,2012,'Oral route not supplied; no matching plain mineral-oil generic is not proof of noncoverage'),
('desmopressin','07 GU','Desmopressin',r'desmopressin',11,2015,2015,'Nocturia/nocturnal polyuria indication not measurable'),
('nsaids','08 Pain','Oral nonselective NSAIDs',r'aspirin|diclofenac|diflunisal|etodolac|flurbiprofen|ibuprofen|indomethacin|ketorolac|meloxicam|nabumetone|naproxen|oxaprozin|piroxicam|sulindac|fenoprofen|ketoprofen|meclofenamate|mefenamic|tolmetin',11,2012,2012,'Chronic use, aspirin >325 mg/day, co-medications and gastroprotection not measurable; mixed-route generics excluded conservatively'),
('indomethacin_ketorolac','08 Pain','Indomethacin / ketorolac',r'indomethacin|ketorolac',12,2012,2012,'Ketorolac oral/parenteral versus ophthalmic unresolved for generic brand; exclude unresolved/ophthalmic/nasal rows'),
('meperidine','08 Pain','Meperidine',r'meperidine',12,2012,2012,'Exposure identifiable'),
('muscle_relaxants','08 Pain','Skeletal muscle relaxants',r'carisoprodol|chlorzoxazone|cyclobenzaprine|metaxalone|methocarbamol|orphenadrine',12,2012,2012,'Exclude baclofen and tizanidine as stated in Table 2'),
('long_su','05 Endocrine','Long-acting SU (LASU benchmark)',r'glimepiride|glyburide|chlorpropamide',10,2012,2019,'Nested benchmark only, excluded from K1 count and meta; definition frozen in LASU')]
STATE_CODES=dict(x.split(':') for x in '01:AL 02:AK 04:AZ 05:AR 06:CA 08:CO 09:CT 10:DE 12:FL 13:GA 15:HI 16:ID 17:IL 18:IN 19:IA 20:KS 21:KY 22:LA 23:ME 24:MD 25:MA 26:MI 27:MN 28:MS 29:MO 30:MT 31:NE 32:NV 33:NH 34:NJ 35:NM 36:NY 37:NC 38:ND 39:OH 40:OK 41:OR 42:PA 44:RI 45:SC 46:SD 47:TN 48:TX 49:UT 50:VT 51:VA 53:WA 54:WV 55:WI 56:WY'.split())
ER=r'(?<![A-Za-z])(?:ER|XL|XR|CC)(?![A-Za-z])|extended[ -]?release|Adalat|Afeditab|Nifediac|Nifedical'
def exclusion(entry,g,b):
 g=g.lower();b=b.lower()
 if entry=='nifedipine' and re.search(ER,b,re.I):return 'explicit_ER_XL_CC_formulation'
 if entry=='antidepressants' and b in ['silenor','zonalon','prudoxin']:return 'low_dose_or_topical_doxepin'
 if entry=='insulin_sliding' and re.search('prot|npl|degludec|glargine',g):return 'premixed_or_basal_insulin'
 if entry=='estrogens':return 'systemic_vs_vaginal_route_not_reliably_identifiable_at_whole_entry_level'
 if entry=='antispasmodics':
  if g.startswith('atropine'):return 'atropine_route_ambiguous_or_ophthalmic'
  if 'diphenoxylate' in g or 'difenoxin' in g:return 'antidiarrheal_not_target_GI_antispasmodic'
 if entry in ['nsaids','indomethacin_ketorolac']:
  if re.search('epolamine|capsicum|/pf',g) or re.search('pennsaid|flector|licart|solaraze|voltaren gel|bromsite|acular|acuvail|sprix|ocufen',b):return 'topical_ophthalmic_or_nasal'
  if g=='diclofenac sodium' and b in ['diclofenac sodium','voltaren']:return 'mixed_or_unknown_route_diclofenac'
  if g.startswith('ketorolac') and b not in ['toradol']:return 'mixed_or_unknown_route_ketorolac'
  if g.startswith('flurbiprofen') and 'sodium' in g:return 'ophthalmic_flurbiprofen'
 return ''
