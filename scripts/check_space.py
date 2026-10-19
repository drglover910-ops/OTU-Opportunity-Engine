"""Check runtime using GitHub's verified HF binding; publish no private records."""
import os,json,time,urllib.request,urllib.error,base64
from pathlib import Path
from datetime import datetime,timezone
from huggingface_hub import HfApi
from chat_delivery_diagnostic import diagnose
SPACE='Dezz-9-10/OTU-Opportunity-Engine'
VERSION=Path('VERSION').read_text().strip()
api=HfApi(token=os.environ['HF_TOKEN']);report={'commit':os.getenv('GITHUB_SHA',''),'version':VERSION,'checked_at':datetime.now(timezone.utc).isoformat(),'upload':'completed','health':'unverified'}
base='https://dezz-9-10-otu-opportunity-engine.hf.space'
headers={'Authorization':'Bearer '+os.environ['HF_TOKEN'],'User-Agent':'OTU deployment smoke check'}
def request(path,data=None):
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={**headers,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180 if path in ('/api/contra/sync','/api/research/preview','/api/contra/application/options') else 65 if path=='/api/browser' else 30) as r:return json.load(r)
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
                    # Exercise the actual private HF proxy with bounded chunks, then remove the partial fixture.
                    upload_id=None
                    try:
                        limits=request('/api/files/storage')
                        fixture=request('/api/files/start',{'workspace':'assistant','name':'otu-deployment-upload-check.zip','size':1024**3});upload_id=fixture['id']
                        raw=base64.b64encode(b'0'*(4*1024**2)).decode()
                        first=request('/api/files/chunk',{'id':upload_id,'offset':0,'content':raw})
                        retry=request('/api/files/chunk',{'id':upload_id,'offset':0,'content':raw})
                        second=request('/api/files/chunk',{'id':upload_id,'offset':4*1024**2,'content':base64.b64encode(b'1'*1024**2).decode()})
                        report['large_upload_route']='passed' if first['received']==retry['received']==4*1024**2 and second['received']==5*1024**2 else 'failed'
                        report['upload_max_bytes']=limits['max_file']
                        report['upload_check_scope']='1 GiB reservation; 4 MiB chunk, retry and next chunk through private HF proxy. Full 1 GiB verified locally, not transferred in production smoke check.'
                    except Exception:report['large_upload_route']='not verified; check storage allowance and runtime'
                    finally:
                        if upload_id:
                            try:request('/api/files/cancel',{'id':upload_id});report['upload_fixture_cleanup']='passed'
                            except Exception:report['upload_fixture_cleanup']='needs attention; remove unfinished deployment check from conversation files'
                    report['connections']=request('/api/connections/check',{})
                    report['workspaces']=len(request('/api/workspaces'))
                    shared=request('/api/project-knowledge');report['assistant_knowledge_version']=shared['version'];report['working_status_report']='available' if shared.get('status_report',{}).get('opportunities') else 'unverified'
                    prepared=[d for d in request('/api/documents') if d['kind'] in ('resume','cover_letter')]
                    if prepared:
                        preview=request('/api/document-preview?id='+str(prepared[0]['id']))
                        report['document_preview']='passed' if preview.get('text') else 'empty'
                    pdf=next((d for d in prepared if d['name'].lower().endswith('.pdf')),None)
                    if pdf:
                        with urllib.request.urlopen(urllib.request.Request(base+'/api/document-page?id='+str(pdf['id']),headers=headers),timeout=40) as image:
                            report['designed_document_preview']='passed' if image.headers.get('Content-Type')=='image/png' and image.read(8)==b'\x89PNG\r\n\x1a\n' else 'unverified'
                    with urllib.request.urlopen(urllib.request.Request(base+'/matrix.js',headers=headers),timeout=30) as asset:
                        report['matrix_asset']='available' if b'matrix-rain' in asset.read(1000) else 'unverified'
                    with urllib.request.urlopen(urllib.request.Request(base+'/ui.js',headers=headers),timeout=30) as shell:
                        source=shell.read(200000);report['workspace_shell']='available' if b'closeWorkspacePanel' in source and b'browsingWorkspace' in source else 'unverified';report['read_aloud_controls']='asset available; device audio not tested' if b'readAnswer' in source else 'unverified';report['isis_voice_controls']='available; device preview required' if b'configureIsisVoice' in source and b'renderIsisVoices' in source else 'unverified'
                    report['voice_samples']={}
                    for voice in ('heart','bella'):
                        try:
                            sample_request=urllib.request.Request(base+'/voice-samples/'+voice+'.mp3',headers={**headers,'Range':'bytes=0-15'})
                            with urllib.request.urlopen(sample_request,timeout=30) as sample:
                                prefix=sample.read(16)
                                report['voice_samples'][voice]={'status':'verified' if sample.status==206 and sample.headers.get('Content-Type')=='audio/mpeg' and prefix.startswith(b'ID3') else 'unverified','http_status':sample.status,'content_range':sample.headers.get('Content-Range','')}
                        except Exception:report['voice_samples'][voice]={'status':'unverified'}
                    report['cpu_voice']=status.get('cpu_voice',{})
                    if report['cpu_voice'].get('available'):
                        try:
                            started_voice=time.time()
                            voice_question={'workspace':'assistant','text':'Hi Desmond. Heart is running on our CPU. This is a synthetic voice check.','voice':'heart'}
                            speech=request('/api/voice/prepare',voice_question)
                            for voice_attempt in range(80):
                                if speech.get('status') not in ('queued','running'):break
                                time.sleep(.5);speech=request('/api/voice/job?workspace=assistant&id='+speech['id'])
                            if speech.get('status')=='ready':
                                with urllib.request.urlopen(urllib.request.Request(base+'/api/voice/audio?workspace=assistant&id='+speech['id'],headers=headers),timeout=30) as audio:
                                    valid_voice=audio.headers.get('Content-Type')=='audio/wav' and audio.read(4)==b'RIFF'
                                repeat=request('/api/voice/prepare',voice_question)
                                report['cpu_voice_check']={'status':'verified' if valid_voice else 'unverified','duration':speech.get('duration'),'generation_seconds':speech.get('generation_seconds'),'first_prepare_round_trip_seconds':round(time.time()-started_voice,2),'replay_cached':repeat['id']==speech['id'],'validation':'Short synthetic CPU speech only, no hosted inference, chat notes or platform writes. Not a live-device listening score.'}
                            else:report['cpu_voice_check']={'status':speech.get('status','unverified')}
                        except Exception:report['cpu_voice_check']={'status':'unverified; device fallback remains available'}
                    conversation=request('/api/conversation?workspace=assistant')
                    report['acknowledged_chat_requests']='API available' if isinstance(conversation.get('requests'),list) else 'unverified'
                    report['response_actions']='asset available; local browser checks passed separately' if b'responseActions' in source and b'rate-answer' in source else 'unverified'
                    chat_threads=request('/api/chat-threads');report['chat_threads']=len(chat_threads)
                    report['chat_delivery']=diagnose(request,chat_threads)
                    report['projects']=len(request('/api/projects'))
                    report['recovery_checkpoint']=request('/api/recovery-status')
                    report['mail_workspace']='local drafts readable' if isinstance(request('/api/mail?box=drafts').get('items'),list) else 'unverified'
                    if status['gmail']:
                        try:report['gmail_mailbox_read']='passed' if isinstance(request('/api/mail?box=inbox&limit=1').get('items'),list) else 'unverified'
                        except Exception:report['gmail_mailbox_read']='unverified; check Gmail connection'
                    report['developer_request_queue']='available' if isinstance(request('/api/developer/requests'),list) else 'unverified'
                    report['ai_live_check']='not run; no paid inference during verification'
                    report['ai_budget']=status.get('ai_budget',{})
                    report['source_retrieval']=status.get('source_retrieval',{'status':'not available'})
                    report['source_controls']='asset available; local fixture tested separately' if b'answerSourcesHTML' in source and b'read-file' in source else 'unverified'
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
                            report['contra_inventory']=request('/api/contra/sync',{})
                            research=request('/api/research/preview',{'workspace':'contra','text':'Find Contra GoHighLevel opportunities','mode':'research'})
                            report['chat_research']={'checks':research.get('checks',[]),'returned':len(research.get('items',[])),'validation':'Bounded keyword read with at most one broader-feed fallback; no model inference, chat creation, submissions or account writes.'}
                            prepared=request('/api/research/preview',{'workspace':'contra','text':'Review application requirements for https://contra.com/opportunity/Mb3oNbXl-canva-to-google-slides-conversion-specialist','mode':'advice'})
                            report['application_review_check']={'focus':prepared.get('focus',{}),'status':prepared.get('application_review',{}).get('status'),'checks':prepared.get('checks',[]),'validation':'One exact-listing read; no AI writing, chat creation, application submission or purchase.'}
                            fields=request('/api/contra/application/options',{'workspace':'contra','url':'https://contra.com/opportunity/Mb3oNbXl-canva-to-google-slides-conversion-specialist','inspect_only':True})
                            report['contra_application_fields']={'status':fields.get('status'),'title':fields.get('title'),'posting_id_available':bool(fields.get('jobPostingId')),'portfolio_options':len(fields.get('projects',[])),'blockers':fields.get('blockers',[]),'validation':'Read listing and portfolio options only. No native draft, submission, model call or local application ticket created.'}
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
