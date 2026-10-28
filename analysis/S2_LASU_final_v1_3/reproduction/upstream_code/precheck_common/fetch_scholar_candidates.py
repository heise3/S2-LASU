"""Archive primary records for candidates identified in the saved Scholar pages."""
from acquire import fetch, OUT
import urllib.parse
import xml.etree.ElementTree as ET

ids = ['32675267','36451895','39923965','36175759','32757475','41510365','40227682','42663988','22593859']
url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?' + urllib.parse.urlencode({'db':'pubmed','id':','.join(ids),'retmode':'xml'})
b=fetch(url, OUT/'evidence/scholar_candidate_records.xml')
for a in ET.fromstring(b).findall('.//PubmedArticle'):
    def t(p):
        e=a.find(p)
        return ''.join(e.itertext()) if e is not None else ''
    print(t('.//PMID'), t('.//ArticleTitle'), t('.//Journal/Title'), t('.//PubDate'))
    print(t('.//Abstract'))
