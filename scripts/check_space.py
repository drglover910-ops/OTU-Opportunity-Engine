"""Check runtime using GitHub's verified HF binding; publish no private records."""
import os,json,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from huggingface_hub import HfApi
SPACE='Dezz-9-10/OTU-Opportunity-Engine'
VERSION=Path('VERSION').read_text().strip()
api=HfApi(token=os.environ['HF_TOKEN']);report={'commit':os.getenv('GITHUB_SHA',''),'version':VERSION,'checked_at':datetime.now(timezone.utc).isoformat(),'upload':'completed','health':'unverified'}
base='https://dezz-9-10-otu-opportunity-engine.hf.space'
headers={'Authorization':'Bearer '+os.environ['HF_TOKEN'],'User-Agent':'OTU deployment smoke check'}
def request(path,data=None):
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={**headers,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=65 if path=='/api/browser' else 30) as r:return json.load(r)
for attempt in range(48):
    try:
        info=api.space_info(SPACE);stage=str(info.runtime.stage);report['runtime_stage']=stage
        if stage in ('BUILD_ERROR','RUNTIME_ERROR'):break
        if stage=='RUNNING':
            try:
                health=request('/health')
                if health.get('version')==VERSION:
                    report['health']='verified';status=request('/api/status')
                    report['storage']=status['storage'];report['opportunities']=status['counts']['opportunities'];report['last_discovery']=status.get('last_discovery',{});report['documents']=status['counts']['documents'];report['gmail_connected']=status['gmail'];report['ai_configured']=status['ai_configured']
                    report['connections']=request('/api/connections/check',{})
                    report['workspaces']=len(request('/api/workspaces'))
                    if status['ai_configured'] and not status.get('last_ai_success'):
                        question='What is the next step for finding paid work on Contra? Keep it to two short sentences.'
                        conversation=request('/api/conversation?workspace=contra')
                        if not any(n['text']==question for n in conversation['notes']):
                            try:
                                result=request('/api/conversation/ask',{'workspace':'contra','text':question})
                                report['ai_live_check']='passed' if result.get('answered') else 'not verified'
                            except Exception:report['ai_live_check']='not verified; inspect writing connection'
                        else:report['ai_live_check']='previous attempt recorded; no repeated paid check'
                    else:report['ai_live_check']='previous successful request recorded' if status.get('last_ai_success') else 'not configured'
                    try:
                        ready=request('/api/contra/prepare',{})
                        report['contra_signin_ready']=bool(ready.get('ready'))
                    except urllib.error.HTTPError as e:
                        report['contra_signin_ready']=False
                        try:report['contra_setup_detail']=json.load(e).get('error','')[:250]
                        except Exception:report['contra_setup_detail']='Registration could not be verified.'
                    if status.get('contra_connected'):
                        try:
                            report['contra_access']=request('/api/contra/check',{})
                            report['contra_tools']=request('/api/contra/tools')
                        except urllib.error.HTTPError as e:
                            try:report['contra_access_error']=json.load(e).get('error','')[:250]
                            except Exception:report['contra_access_error']='Account access could not be verified.'
                    report['platforms']=len(request('/api/platforms'))
                    report['browser']='not checked'
                    try:
                        existing=request('/api/browser',{'action':'status'})
                        if existing.get('open'):report['browser']='already open; left unchanged'
                        else:
                            opened=request('/api/browser',{'action':'start','platform':'contra','url':'https://contra.com/opportunities'})
                            page=request('/api/browser',{'action':'read'})
                            report['browser']='runtime verified; platform login still needed' if opened.get('http_status')==200 and not any(t in page['text'].lower() for t in ('verify you are human','access denied','unusual traffic','just a moment')) else 'runtime started; platform access restricted or unverified'
                            report['browser_http_status']=opened.get('http_status')
                            request('/api/browser',{'action':'stop'})
                    except urllib.error.HTTPError as e:
                        try:detail=json.load(e).get('error','')
                        except Exception:detail='Browser check failed.'
                        report['browser']='hosting configuration needed' if 'sandbox' in detail.lower() else 'not verified'
                        report['browser_detail']=detail[:260]
                    except Exception:report['browser']='not verified'
                    report['discovery']=request('/api/discover',{});break
            except urllib.error.HTTPError as e:
                report['app_http_status']=e.code
                if e.code in (401,403):break
            except Exception:report['app_connection']='unavailable'
    except Exception:report['runtime_api']='unavailable';break
    time.sleep(10)
if report['health']=='verified' and report.get('storage',{}).get('mount_detected') and not report['storage'].get('restart_verified'):
    try:
        marker=request('/api/storage/probe',{'action':'start'})
        api.restart_space(SPACE)
        report['restart_test']='started'
        time.sleep(10)
        for attempt in range(48):
            try:
                health=request('/health')
                if health.get('version')==VERSION:
                    proof=request('/api/storage/probe',{'action':'verify','nonce':marker['nonce']})
                    report['restart_test']='passed' if proof.get('verified') else 'failed'
                    status=request('/api/status');report['storage']=status['storage'];report['opportunities']=status['counts']['opportunities'];report['last_discovery']=status.get('last_discovery',{})
                    break
            except Exception:
                pass
            time.sleep(10)
    except Exception:
        report['restart_test']='unverified; check permissions or runtime'
Path('docs/LATEST_DEPLOYMENT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
print('Runtime verification complete.' if report['health']=='verified' else 'Upload completed, but app health could not be verified. Check the private Space runtime.')
