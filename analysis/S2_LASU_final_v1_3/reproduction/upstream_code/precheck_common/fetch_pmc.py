from acquire import *
import xml.etree.ElementTree as ET
for pmc in ['PMC7967940','PMC4925288','PMC9022137','PMC6488408','PMC10272037']:
 u='https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/'+pmc+'/unicode'
 try:
  b=fetch(u,OUT/f'evidence/{pmc}_bioc.xml');t=ET.fromstring(b)
  pars=[''.join(x.itertext()) for x in t.findall('.//passage/text')]
  (OUT/f'evidence/{pmc}_extracted.txt').write_text('\n'.join(pars))
  print(pmc,len(pars),flush=True)
 except Exception as e:print(pmc,type(e).__name__,str(e),flush=True)
 time.sleep(.5)
