from acquire import *
r=[r for r in catalog() if r['source']=='A' and r['year']==2024][0]
p={'filter[su][group][conjunction]':'OR','size':2}
for i,drug in enumerate(['glimepiride','glyburide','chlorpropamide','glipizide','tolbutamide','tolazamide','gliclazide','gliquidone','glibenclamide','acetohexamide']):
 p.update({f'filter[d{i}][condition][path]':'Gnrc_Name',f'filter[d{i}][condition][operator]':'CONTAINS',f'filter[d{i}][condition][value]':drug,f'filter[d{i}][condition][memberOf]':'su'})
for endpoint in ['data','data/stats']:
 url=r['api_url'].removesuffix('data')+endpoint+'?'+urllib.parse.urlencode(p)
 b=fetch(url,WORK/('probe_'+endpoint.replace('/','_')+'.json'));print(endpoint,b.decode()[:3000])
