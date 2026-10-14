"""Check runtime using GitHub's verified HF binding; publish no private records."""
import os,json,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from huggingface_hub import HfApi
SPACE='Dezz-9-10/OTU-Opportunity-Engine'
VERSION=Path('VERSION').read_text().strip()
api=HfApi(token=os.environ['HF_TOKEN']);report={'version':VERSION,'checked_at':datetime.now(timezone.utc).isoformat(),'upload':'completed','health':'unverified'}
base='https://dezz-9-10-otu-opportunity-engine.hf.space'
headers={'Authorization':'Bearer '+os.environ['HF_TOKEN'],'User-Agent':'OTU deployment smoke check'}
def request(path,data=None):
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={**headers,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
for attempt in range(24):
    try:
        info=api.space_info(SPACE);stage=str(info.runtime.stage);report['runtime_stage']=stage
        if stage in ('BUILD_ERROR','RUNTIME_ERROR'):break
        if stage=='RUNNING':
            try:
                health=request('/health')
                if health.get('version')==VERSION:
                    report['health']='verified';status=request('/api/status')
                    report['storage']=status['storage'];report['opportunities']=status['counts']['opportunities'];report['last_discovery']=status.get('last_discovery',{});report['documents']=status['counts']['documents'];report['gmail_connected']=status['gmail'];report['ai_configured']=status['ai_configured']
                    report['discovery']=request('/api/discover',{});break
            except urllib.error.HTTPError as e:
                report['app_http_status']=e.code
                if e.code in (401,403):break
            except Exception:report['app_connection']='unavailable'
    except Exception:report['runtime_api']='unavailable';break
    time.sleep(10)
Path('docs/LATEST_DEPLOYMENT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
print('Runtime verification complete.' if report['health']=='verified' else 'Upload completed, but app health could not be verified. Check the private Space runtime.')
