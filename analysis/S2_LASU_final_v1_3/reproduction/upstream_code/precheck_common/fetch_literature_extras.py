from acquire import *
import xml.etree.ElementTree as ET
ids=['32841366','31057695','34779654','38709112','29427177','33720673','27052559','33851113','34726745','36495141','37078149','41760122','42167878']
u='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urllib.parse.urlencode({'db':'pubmed','id':','.join(ids),'retmode':'xml'})
b=fetch(u,OUT/'evidence/literature_key_records.xml')
for a in ET.fromstring(b).findall('.//PubmedArticle'):
 txt=lambda p:''.join(a.find(p).itertext()) if a.find(p) is not None else ''
 auth=[' '.join([x.findtext('LastName',''),x.findtext('Initials','')]) for x in a.findall('.//Author')]
 print(txt('.//PMID'),'; '.join(auth),txt('.//ArticleTitle'),txt('.//Journal/Title'))
fetch('https://www.natap.org/2024/HIV/JAmericanGeriatrics2020FralicEstimatingPotentiallyInappropriateMedicationsAmongOlder.pdf',OUT/'evidence/Fralick2020.pdf')
