"""Read public official docs and summarize safe operational facts/status."""
import urllib.request,urllib.error,json,re,os
from pathlib import Path
from html.parser import HTMLParser
class Extract(HTMLParser):
    def __init__(self): super().__init__(); self.text=[]; self.links=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag=='a':
            for k,v in attrs:
                if k=='href' and v:self.links.append(v)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip():self.text.append(data.strip())
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'OTU documentation research/0.2'}),timeout=30) as response:
        raw=response.read(3000000).decode('utf-8',errors='replace')
    p=Extract();p.feed(raw);return p
out=[]
for url in ['https://help.contra.com/en/','https://remotive.com/api/remote-jobs?search=crm']:
    try:
        if 'remotive' in url:
            with urllib.request.urlopen(url,timeout=30) as r:d=json.load(r)
            out.append({'source':url,'status':'verified response','job_count':len(d.get('jobs',[])),'examples':[{'title':j['title'],'company':j['company_name'],'url':j['url']} for j in d.get('jobs',[])[:5]]})
        else:
            p=fetch(url);out.append({'source':url,'status':'read','text':'\n'.join(p.text)[:20000]})
            links=[]
            for href in p.links:
                full=urllib.parse.urljoin(url,href)
                if urllib.parse.urlparse(full).hostname=='help.contra.com' and any(s in full.lower() for s in ['article','collection']) and full not in links:links.append(full)
            article_links=[]
            for link in links[:8]:
                try:
                    article=fetch(link);out.append({'source':link,'status':'read','text':'\n'.join(article.text)[:25000]})
                    for href in article.links:
                        full=urllib.parse.urljoin(link,href)
                        if urllib.parse.urlparse(full).hostname=='help.contra.com' and '/articles/' in full and any(term in full.lower() for term in ['applying-to-jobs','direct-message','fees-overview','case-study','one-liner','services','paid-projects','first-client','spam','discovery-score','profile','co-agent']):
                            if full not in article_links:article_links.append(full)
                except Exception as e:out.append({'source':link,'status':type(e).__name__})
            for link in article_links[:18]:
                try:
                    article=fetch(link);out.append({'source':link,'status':'read','text':'\n'.join(article.text)[:30000]})
                except Exception as e:out.append({'source':link,'status':type(e).__name__})
    except Exception as e:out.append({'source':url,'status':type(e).__name__,'http_status':getattr(e,'code',None)})
for url in ['https://weworkremotely.com/remote-jobs.rss','https://www.arbeitnow.com/api/job-board-api','https://remoteok.com/api']:
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'OTUOpportunityEngine/0.2'}),timeout=30) as r:raw=r.read(5000000)
        if url.endswith('.rss'):
            import xml.etree.ElementTree as ET
            root=ET.fromstring(raw);examples=[{'title':x.findtext('title'),'url':x.findtext('link'),'description':x.findtext('description','')[:2000]} for x in root.findall('.//item')[:5]]
        else:
            parsed=json.loads(raw);entries=parsed.get('data',[]) if isinstance(parsed,dict) else parsed[1:];examples=[{'title':x.get('title') or x.get('position'),'company':x.get('company_name') or x.get('company'),'url':x.get('url'),'location':x.get('location')} for x in entries[:5]]
        out.append({'source':url,'status':'verified response','examples':examples})
    except Exception as e:out.append({'source':url,'status':type(e).__name__,'http_status':getattr(e,'code',None)})
# Only non-secret Space configuration is recorded.
try:
    from huggingface_hub import HfApi
    api=HfApi(token=os.environ.get('HF_TOKEN'))
    info=api.space_info('Dezz-9-10/OTU-Opportunity-Engine')
    variables=api.get_space_variables('Dezz-9-10/OTU-Opportunity-Engine')
    out.append({'source':'Space configuration','private':info.private,'runtime_stage':str(info.runtime.stage),'storage_variable':variables['OTU_DATA_DIR'].value if 'OTU_DATA_DIR' in variables else 'not set'})
except Exception as e:out.append({'source':'Space configuration','status':type(e).__name__})
Path('docs/RESEARCH_RESULTS.json').write_text(json.dumps(out,indent=2))
print('Saved official research results. No token values recorded.')
