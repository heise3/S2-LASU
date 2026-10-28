from acquire import *
for r in catalog():
 if r['year']==2024:
  uid=r['api_url'].split('/')[-2];url='https://data.cms.gov/data-api/v1/dataset-resources/'+uid
  b=fetch(url,OUT/f"evidence/{r['source']}_resources.json");print(b.decode()[:15000])
fetch('https://data.cms.gov/sites/default/files/2026-05/MUP_DPR_RY26_20260421_Methodology_508.pdf',OUT/'evidence/CMS_methodology_2026.pdf')
fetch('https://data.cms.gov/sites/default/files/2022-07/MUP_DPR_RY22_20220715_DD_PRV_Drug.pdf',OUT/'evidence/CMS_provider_dictionary.pdf')
fetch('https://data.cms.gov/sites/default/files/2025-04/MUP_DPR_RY25_20250401_DD_Geo_508.pdf',OUT/'evidence/CMS_geography_dictionary.pdf')
