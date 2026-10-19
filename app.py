"""Private single-owner Hugging Face Space. HF access controls provide authentication."""
import base64,json,os,threading,urllib.parse,secrets,time,re
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from engine import Engine,VERSION,STAGES
ROOT=Path(__file__).resolve().parent
engine=Engine()
from attachment_store import AttachmentStore
attachments=AttachmentStore(engine)
from backup_store import Backups
backups=Backups(engine)
backups.checkpoint()
from workspace_ops import WorkspaceOps
workspace_ops=WorkspaceOps(engine)
from chat_service import ChatService
chat_service=ChatService(engine)
from contra_applications import ContraApplications
contra_applications=ContraApplications(engine)
class Handler(BaseHTTPRequestHandler):
    developer_sessions={}
    def log_message(self,*args):pass  # No OAuth codes, inbox content, or credentials in logs.
    def output(self,body,ctype='application/json',status=200,download=None):
        if not isinstance(body,bytes):body=json.dumps(body).encode()
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        if ctype.startswith('text/html'):self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; media-src 'self'; base-uri 'none'; form-action 'self'")
        if download:self.send_header('Content-Disposition','attachment; filename="'+download+'"')
        self.end_headers();self.wfile.write(body)
    def voice_sample(self,path,head=False):
        names={'/voice-samples/heart.mp3':'heart.mp3','/voice-samples/bella.mp3':'bella.mp3'}
        if path not in names:return False
        body=(ROOT/'voice_samples'/names[path]).read_bytes();size=len(body);start=0;end=size-1;status=200
        value=self.headers.get('Range') if not head else None
        if value:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',value)
            try:
                if not match or not any(match.groups()):raise ValueError()
                left,right=match.groups()
                if left:start=int(left);end=min(int(right),size-1) if right else size-1
                else:
                    count=int(right)
                    if count<=0:raise ValueError()
                    start=max(0,size-count)
                if start>=size or end<start:raise ValueError()
                status=206
            except ValueError:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.send_header('Cache-Control','no-store');self.end_headers();return True
        self.send_response(status);self.send_header('Content-Type','audio/mpeg');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        if not head:self.wfile.write(body[start:end+1])
        return True
    def do_HEAD(self):
        if not self.voice_sample(urllib.parse.urlsplit(self.path).path,head=True):
            self.send_response(404);self.send_header('Content-Length','0');self.end_headers()
    def do_GET(self):
        parsed=urllib.parse.urlsplit(self.path);path=parsed.path;query=urllib.parse.parse_qs(parsed.query)
        try:
            if self.voice_sample(path):return
            if path=='/api/files/photo':return self.output(attachments.photo(query['id'][0]),'image/jpeg')
            if path=='/api/files/storage':return self.output(attachments.status())
            if path=='/api/files/list':return self.output(attachments.listing({k:v[0] for k,v in query.items()}))
            if path=='/api/files/status':return self.output(attachments.row(query['id'][0]))
            if path=='/api/files/download':
                file,record=attachments.file(query['id'][0]);self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(record['size']));self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+urllib.parse.quote(record['name']));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
                with file.open('rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''):self.wfile.write(block)
                return
            if path=='/health':return self.output({'status':'ok','version':VERSION})
            if path in ['/', '/ui.js','/ui.css','/matrix.js']:
                name={'/':'ui.html','/ui.js':'ui.js','/ui.css':'ui.css','/matrix.js':'matrix.js'}[path];ctype={'/':'text/html; charset=utf-8','/ui.js':'text/javascript; charset=utf-8','/ui.css':'text/css; charset=utf-8','/matrix.js':'text/javascript; charset=utf-8'}[path]
                return self.output((ROOT/name).read_bytes(),ctype)
            if path=='/api/platforms':return self.output(engine.platforms())
            if path=='/api/platform-profile':return self.output(engine.platform_profile(query['id'][0]))
            if path=='/api/browser/frame':return self.output(engine.browser_action({'action':'frame'}),'image/jpeg')
            if path=='/api/workspaces':return self.output(engine.workspaces())
            if path=='/api/chat-threads':return self.output(workspace_ops.threads())
            if path=='/api/recovery-status':return self.output(backups.status())
            if path=='/api/projects':return self.output(workspace_ops.projects())
            if path=='/api/mail':return self.output(workspace_ops.mail_list({k:v[0] for k,v in query.items()}))
            if path=='/api/mail/thread':return self.output(workspace_ops.mail_thread(query['id'][0]))
            if path=='/api/chat/request':return self.output(chat_service.row(query['id'][0]))
            if path=='/api/conversation':return self.output(engine.conversation({k:v[0] for k,v in query.items()}))
            if path=='/oauth/contra/start':
                from contra_mcp import ContraConnection
                url=ContraConnection(engine).authorize();self.send_response(303);self.send_header('Location',url);self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','no-referrer');self.end_headers();return
            if path=='/oauth/contra/callback':
                from contra_mcp import ContraConnection
                ContraConnection(engine).callback(query.get('state',[''])[0],query.get('code',[''])[0])
                return self.output(b'<html><body><h1>Contra sign-in saved.</h1><p>Return to your Opportunity Engine, open Connections, and press Check Contra access. No messages or applications were sent.</p></body></html>','text/html; charset=utf-8')
            if path=='/api/contra/summary':
                from contra_mcp import ContraConnection
                return self.output({**(engine.setting('contra_sync_summary',{}) or {}),**ContraConnection(engine).inventory_details()})
            if path=='/api/contra/snapshot':return self.output(engine.setting('contra_account_snapshot',{}) or {})
            if path=='/api/contra/tools':return self.output(engine.setting('contra_tool_catalog',[]) or [])
            if path=='/api/status':return self.output(engine.status())
            if path=='/api/opportunities':return self.output(engine.list())
            if path=='/api/project-knowledge':return self.output(engine.project_knowledge())
            if path=='/api/developer/requests':return self.output(engine.developer_requests())
            if path=='/api/document-page':
                from document_preview import render_page
                with engine.connect() as c:doc=c.execute('SELECT * FROM documents WHERE id=?',(int(query['id'][0]),)).fetchone()
                if not doc or not doc['name'].lower().endswith('.pdf'):raise ValueError('Choose a PDF document for its designed preview.')
                return self.output(render_page(doc['path'],int(query.get('page',['0'])[0])),'image/png')
            if path=='/api/document-preview':return self.output(engine.document_preview(query['id'][0]))
            if path=='/api/documents':return self.output(engine.documents())
            if path=='/api/email-cases':return self.output(engine.email_cases())
            if path=='/api/email-case':return self.output(engine.email_case(query['id'][0]))
            if path=='/api/packages':return self.output(engine.packages())
            if path=='/api/career-updates':return self.output(engine.career_updates())
            if path=='/api/master-resume':
                from applications import master_document
                record=engine.master_record()
                return self.output(master_document(record),'application/vnd.openxmlformats-officedocument.wordprocessingml.document',download='Desmond_Glover_Master_Career_Record_v'+str(len(record['updates']))+'.docx')
            if path=='/api/master-record':return self.output(json.dumps(engine.master_record(),indent=2).encode(),'application/json',download='OTU_Master_Record_'+VERSION+'.json')
            if path=='/api/drafts':return self.output(engine.drafts())
            if path=='/api/history':return self.output(engine.history(query.get('id',[None])[0]))
            if path=='/api/messages':return self.output(engine.messages())
            if path=='/api/playbooks':return self.output(json.loads((ROOT/'playbooks.json').read_text()))
            if path=='/api/document':
                did=int(query['id'][0])
                with engine.connect() as c:d=c.execute('SELECT * FROM documents WHERE id=?',(did,)).fetchone()
                if not d:raise ValueError('Document not found')
                name=d['name'].replace('"','').replace('\r','').replace('\n','')
                if query.get('inline')==['1'] and name.lower().endswith('.pdf'):return self.output(Path(d['path']).read_bytes(),'application/pdf')
                return self.output(Path(d['path']).read_bytes(),'application/octet-stream',download=name)
            if path=='/api/export':
                file=backups.export()
                try:
                    self.send_response(200);self.send_header('Content-Type','application/zip');self.send_header('Content-Length',str(file.stat().st_size));self.send_header('Content-Disposition','attachment; filename="OTU-complete-backup-'+VERSION+'.zip"');self.send_header('Cache-Control','no-store');self.end_headers()
                    with file.open('rb') as stream:
                        for block in iter(lambda:stream.read(1024*1024),b''):self.wfile.write(block)
                finally:file.unlink(missing_ok=True)
                return
            if path=='/oauth/google/start':
                url=engine.oauth_url()
                self.send_response(303);self.send_header('Location',url)
                self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','no-referrer')
                self.end_headers();return
            if path=='/oauth/google/callback':
                engine.oauth_callback(query.get('state',[''])[0],query.get('code',[''])[0])
                return self.output(b'<html><body><p>Gmail connected. Close this window and refresh your Opportunity Engine.</p></body></html>','text/html; charset=utf-8')
            return self.output({'error':'Not found'},status=404)
        except (ValueError,KeyError) as e:return self.output({'error':str(e)},status=400)
        except Exception:return self.output({'error':'Operation failed. Check the storage connection or service configuration.'},status=500)
    def do_POST(self):
        try:
            origin=self.headers.get('Origin')
            # HF reverse proxies may rewrite Host; only the configured public origin is also accepted.
            valid={self.headers.get('Host'),urllib.parse.urlsplit(os.getenv('PUBLIC_URL','')).netloc}
            if origin and urllib.parse.urlsplit(origin).netloc not in valid:return self.output({'error':'Cross-origin request refused'},status=403)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Use a JSON request')
            length=int(self.headers.get('Content-Length',0))
            if length<=0 or length>90*1024*1024:raise ValueError('Request size invalid')
            d=json.loads(self.rfile.read(length))
            if self.path=='/api/research/preview':
                from research_tools import Research,requested
                from opportunity_review import intended,resolve,review
                if intended(d):
                    focus=resolve(engine,d,engine.conversation(d))
                    if focus['status']!='ready':return self.output({'focus':focus,'checks':[],'items':[]})
                    report=Research(engine).run({**d,'text':str(d.get('text',''))+'\nListing to review: '+focus['url']})
                    details=review(focus,report);report['items']=[i for i in report['items'] if i['url'].split('?',1)[0].rstrip('/')==focus['url']]
                    return self.output({**report,'focus':{k:v for k,v in focus.items() if k!='excluded_labels'},'application_review':details})
                if not requested(d):raise ValueError('Ask for opportunity research first.')
                return self.output(Research(engine).run(d))
            if self.path=='/api/files/read-in-chat':return self.output(engine.knowledge.enable_file(d))
            if self.path=='/api/files/start':return self.output(attachments.start(d))
            if self.path=='/api/files/chunk':return self.output(attachments.chunk(d))
            if self.path=='/api/files/finish':return self.output(attachments.finish(d))
            if self.path=='/api/files/remove':return self.output(attachments.remove(d))
            if self.path=='/api/files/cancel':return self.output(attachments.cancel(d))
            if self.path=='/api/developer/unlock':
                if d.get('confirmation')!='OPEN DEVELOPER TOOLS':raise ValueError('Confirm that you want to open developer tools.')
                token=secrets.token_urlsafe(32);self.developer_sessions[token]=time.time()+1800
                return self.output({'token':token,'expires_in':1800})
            if self.path=='/api/developer/lock':
                self.developer_sessions.pop(self.headers.get('X-Developer-Key',''),None);return self.output({'locked':True})
            if self.path in ('/api/settings','/api/restore','/api/restore-complete') and self.developer_sessions.get(self.headers.get('X-Developer-Key',''),0)<time.time():return self.output({'error':'Open developer tools before changing technical settings.'},status=403)
            if self.path in ('/api/contra/prepare','/api/contra/check','/api/contra/disconnect'):
                from contra_mcp import ContraConnection
                connection=ContraConnection(engine)
                return self.output({'/api/contra/prepare':connection.prepare,'/api/contra/check':connection.discover,'/api/contra/disconnect':connection.disconnect}[self.path]())
            if self.path.startswith('/api/contra/application/'):
                method={'options':contra_applications.options,'prepare':contra_applications.prepare,'submit':contra_applications.submit,'discard':contra_applications.discard,'status':lambda d:contra_applications.view(contra_applications.record(d))}.get(self.path.rsplit('/',1)[-1])
                if not method:raise ValueError('Unknown application action.')
                return self.output(method(d))
            if self.path=='/api/ai/limits':return self.output(engine.save_ai_limits(d))
            if self.path=='/api/contra/sync':
                from contra_mcp import ContraConnection
                return self.output(ContraConnection(engine).sync())
            if self.path=='/api/platforms':return self.output(engine.add_platform(d))
            if self.path=='/api/platform-profile':return self.output(engine.save_platform_profile(d))
            if self.path=='/api/browser':return self.output(engine.browser_action(d))
            if self.path=='/api/connections/check':return self.output(engine.check_connections())
            if self.path=='/api/projects':return self.output(workspace_ops.create_project(d))
            if self.path=='/api/chat/organize':return self.output(workspace_ops.change(d))
            if self.path=='/api/mail/organize':return self.output(workspace_ops.organize_mail(d))
            if self.path=='/api/restore-complete':
                if d.get('confirmed') is not True:raise ValueError('Confirm restoring this complete backup.')
                file,record=attachments.file(d.get('id'))
                return self.output(backups.restore(file,record['id']))
            if self.path=='/api/chat/new':return self.output(engine.create_chat(d))
            if self.path=='/api/chat/rename':return self.output(engine.rename_chat(d))
            if self.path=='/api/workspaces':return self.output(engine.add_workspace(d))
            if self.path=='/api/developer/request':return self.output(engine.queue_developer_request(d))
            if self.path=='/api/developer/request-update':return self.output(engine.update_developer_request(d))
            if self.path=='/api/document/revise':
                from document_review import save
                return self.output(save(engine,d))
            if self.path=='/api/chat/request':return self.output(chat_service.start(d))
            if self.path=='/api/conversation/feedback':return self.output(engine.response_feedback(d))
            if self.path=='/api/conversation/ask':return self.output(engine.ask_workspace(d))
            if self.path=='/api/conversation/memory':return self.output(engine.conversation_memory(d))
            if self.path=='/api/conversation/note':return self.output(engine.add_work_note(d))
            routes={'/api/add':engine.add,'/api/update':engine.update,'/api/draft':engine.create_draft,'/api/draft/edit':engine.edit_draft,'/api/approve':engine.approve,'/api/send':engine.send}
            if self.path in routes:return self.output(routes[self.path](d))
            if self.path=='/api/gmail/history':return self.output(engine.start_history_study())
            if self.path=='/api/package':return self.output(engine.create_package(d))
            if self.path=='/api/career-update':return self.output(engine.add_career_update(d))
            if self.path=='/api/storage/probe':return self.output(engine.storage_probe(d))
            if self.path=='/api/discover':return self.output(engine.scan())
            if self.path=='/api/upload':return self.output(engine.import_file(d['name'],base64.b64decode(d['content'],validate=True),d.get('kind','reference')))
            if self.path=='/api/restore':return self.output(engine.restore(base64.b64decode(d['content'],validate=True)))
            if self.path=='/api/gmail/connect':return self.output({'url':engine.oauth_url()})
            if self.path=='/api/gmail/sync':return self.output(engine.sync_inbox())
            if self.path=='/api/gmail/disconnect':engine.set_setting('gmail_tokens',None);return self.output({'disconnected':True})
            if self.path=='/api/settings':
                if 'scheduler_enabled' in d:engine.set_setting('scheduler_enabled',bool(d['scheduler_enabled']))
                if 'storage_verified' in d:engine.set_setting('storage_verified',bool(d['storage_verified']))
                return self.output({'saved':True})
            return self.output({'error':'Not found'},status=404)
        except (ValueError,KeyError) as e:return self.output({'error':str(e)},status=400)
        except Exception:return self.output({'error':'Operation failed. Check the file type, storage or connection settings.'},status=500)
if __name__=='__main__':
    threading.Thread(target=engine.schedule_loop,daemon=True).start()
    ThreadingHTTPServer(('0.0.0.0',int(os.getenv('PORT','7860'))),Handler).serve_forever()
