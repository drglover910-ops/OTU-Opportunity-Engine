"""Private single-owner Hugging Face Space. HF access controls provide authentication."""
import base64,json,os,threading,urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from engine import Engine,VERSION,STAGES
ROOT=Path(__file__).resolve().parent
engine=Engine()
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass  # No OAuth codes, inbox content, or credentials in logs.
    def output(self,body,ctype='application/json',status=200,download=None):
        if not isinstance(body,bytes):body=json.dumps(body).encode()
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        if ctype.startswith('text/html'):self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'")
        if download:self.send_header('Content-Disposition','attachment; filename="'+download+'"')
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        parsed=urllib.parse.urlsplit(self.path);path=parsed.path;query=urllib.parse.parse_qs(parsed.query)
        try:
            if path=='/health':return self.output({'status':'ok','version':VERSION})
            if path in ['/', '/ui.js','/ui.css']:
                name={'/':'ui.html','/ui.js':'ui.js','/ui.css':'ui.css'}[path];ctype={'/':'text/html; charset=utf-8','/ui.js':'text/javascript; charset=utf-8','/ui.css':'text/css; charset=utf-8'}[path]
                return self.output((ROOT/name).read_bytes(),ctype)
            if path=='/api/status':return self.output(engine.status())
            if path=='/api/opportunities':return self.output(engine.list())
            if path=='/api/documents':return self.output(engine.documents())
            if path=='/api/drafts':return self.output(engine.drafts())
            if path=='/api/history':return self.output(engine.history(query.get('id',[None])[0]))
            if path=='/api/messages':return self.output(engine.messages())
            if path=='/api/playbooks':return self.output(json.loads((ROOT/'playbooks.json').read_text()))
            if path=='/api/document':
                did=int(query['id'][0])
                with engine.connect() as c:d=c.execute('SELECT * FROM documents WHERE id=?',(did,)).fetchone()
                if not d:raise ValueError('Document not found')
                name=d['name'].replace('"','').replace('\r','').replace('\n','')
                return self.output(Path(d['path']).read_bytes(),'application/octet-stream',download=name)
            if path=='/api/export':return self.output(engine.backup(),'application/zip',download='OTU-private-backup-'+VERSION+'.zip')
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
            routes={'/api/add':engine.add,'/api/update':engine.update,'/api/draft':engine.create_draft,'/api/draft/edit':engine.edit_draft,'/api/approve':engine.approve,'/api/send':engine.send}
            if self.path in routes:return self.output(routes[self.path](d))
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
