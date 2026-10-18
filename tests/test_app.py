import os,tempfile,unittest,threading,urllib.request,json,io,zipfile,sqlite3
from pathlib import Path
from unittest.mock import patch
os.environ['OTU_DATA_DIR']=tempfile.mkdtemp()
import app
from engine import Engine,qualify,safe_url
class Core(unittest.TestCase):
    def setUp(self):self.engine=Engine(tempfile.mkdtemp())
    def lead(self,**kwargs):
        d={'company':'Example','title':'GoHighLevel CRM workflow setup','url':'https://example.com/project','description':'Build pipelines, Zapier automation and follow-up.','category':'CRM / GoHighLevel',**kwargs}
        return self.engine.add(d)['id']
    def test_existing_database_migration(self):
        path=Path(tempfile.mkdtemp());c=sqlite3.connect(path/'opportunities.sqlite3')
        c.execute('CREATE TABLE opportunities(id INTEGER PRIMARY KEY,company TEXT,title TEXT,url TEXT UNIQUE,category TEXT,stage TEXT,contact TEXT,notes TEXT,followup TEXT,created TEXT)')
        c.execute('INSERT INTO opportunities VALUES(1,"Old client","CRM setup","https://example.com/old","CRM / GoHighLevel","Contacted","a@example.com","Keep me","2026-10-20","2026-10-14")');c.commit();c.close()
        e=Engine(path);self.assertEqual(e.list()[0]['notes'],'Keep me');self.assertEqual(e.list()[0]['stage'],'Contacted')
    def test_duplicate_tracking_urls_and_no_url(self):
        self.lead();self.lead(url='https://example.com/project?utm_source=email#top');self.assertEqual(len(self.engine.list()),1)
        self.lead(url='');self.lead(url='');self.assertEqual(len(self.engine.list()),1)
        self.lead(url='',title='Other CRM project');self.lead(url='',title='Other CRM project');self.assertEqual(len(self.engine.list()),2)
    def test_script_url_rejected(self):
        with self.assertRaises(ValueError):safe_url('javascript:alert(1)')
    def test_ranking_uses_real_requirements(self):
        r=self.engine.get(self.lead());fit=qualify(r);self.assertGreater(fit['score'],50);self.assertIn('Pay not provided; ask before committing',fit['warnings'])
    def test_import_zip_internal_vs_resume_and_duplicates(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('../../00_START_HERE_Bot_Operating_Manual.txt','Internal record')
            z.writestr('Desmond_Glover_CRM_Resume.txt','GoHighLevel CRM experience')
        r=self.engine.import_file('archive.zip',out.getvalue());self.assertEqual(r['imported'],2)
        self.assertEqual(self.engine.import_file('archive.zip',out.getvalue())['imported'],0)
        docs=self.engine.documents();self.assertEqual({d['kind'] for d in docs},{'reference','resume'})
        self.assertFalse((self.engine.data/'00_START_HERE_Bot_Operating_Manual.txt').exists())
    def test_draft_approval_edit_resets_and_send_gate(self):
        oid=self.lead();self.engine.update({'id':oid,'contact':'recipient@example.com'})
        did=self.engine.create_draft({'id':oid})['id']
        with self.assertRaises(ValueError):self.engine.send({'id':did,'digest':self.engine.draft(did)['digest']})
        self.engine.approve({'id':did,'confirmation':'I reviewed recipient, content, attachments and history'})
        r=self.engine.draft(did);self.engine.edit_draft({**r,'body':'A changed message','attachments':[]})
        self.assertEqual(self.engine.draft(did)['status'],'Draft')
    def test_send_exactly_once_and_followup_confirmation(self):
        oid=self.lead();self.engine.update({'id':oid,'contact':'recipient@example.com'})
        did=self.engine.create_draft({'id':oid})['id'];self.engine.approve({'id':did,'confirmation':'I reviewed recipient, content, attachments and history'})
        with patch.object(self.engine,'gmail_token',return_value='test'),patch('engine.fetch_json',return_value={'id':'message-1'}) as api:
            self.engine.send({'id':did,'digest':self.engine.draft(did)['digest']})
            with self.assertRaises(ValueError):self.engine.send({'id':did,'digest':self.engine.draft(did)['digest']})
            self.assertEqual(api.call_count,1)
        self.engine.update({'id':oid,'relationship':'Follow-up'});follow=self.engine.create_draft({'id':oid})['id']
        with self.assertRaises(ValueError):self.engine.approve({'id':follow,'confirmation':'I reviewed recipient, content, attachments and history'})
        self.engine.approve({'id':follow,'confirmation':'I reviewed recipient, content, attachments and history','repeat_confirmed':True})
    def test_ambiguous_delivery_locks_retry(self):
        oid=self.lead();self.engine.update({'id':oid,'contact':'recipient@example.com'});did=self.engine.create_draft({'id':oid})['id'];self.engine.approve({'id':did,'confirmation':'I reviewed recipient, content, attachments and history'})
        with patch.object(self.engine,'gmail_token',return_value='test'),patch('engine.fetch_json',side_effect=ValueError('Connection')):
            with self.assertRaises(ValueError):self.engine.send({'id':did,'digest':self.engine.draft(did)['digest']})
        self.assertEqual(self.engine.draft(did)['status'],'Delivery unknown')
        with self.assertRaises(ValueError):self.engine.send({'id':did,'digest':self.engine.draft(did)['digest']})
    def test_internal_attachment_refused(self):
        oid=self.lead();self.engine.update({'id':oid,'contact':'a@example.com'});doc=self.engine.import_file('manual.txt',b'Internal material')['id'];did=self.engine.create_draft({'id':oid})['id'];r=self.engine.draft(did)
        self.engine.edit_draft({**r,'attachments':[doc]})
        with self.assertRaises(ValueError):self.engine.approve({'id':did,'confirmation':'I reviewed recipient, content, attachments and history'})
    def test_backup_restores_history_excludes_credentials_and_resets_approval(self):
        oid=self.lead();self.engine.update({'id':oid,'contact':'a@example.com'});self.engine.import_file('CRM_Resume.txt',b'CRM work');did=self.engine.create_draft({'id':oid})['id'];self.engine.approve({'id':did,'confirmation':'I reviewed recipient, content, attachments and history'})
        self.engine.set_setting('gmail_tokens',{'refresh_token':'SECRET-DO-NOT-EXPORT'})
        backup=self.engine.backup()
        with zipfile.ZipFile(io.BytesIO(backup)) as z:self.assertNotIn('SECRET-DO-NOT-EXPORT',z.read('records.json').decode())
        target=Engine(tempfile.mkdtemp());target.restore(backup);self.assertEqual(len(target.list()),1);self.assertEqual(len(target.documents()),1);self.assertEqual(target.drafts()[0]['status'],'Draft');self.assertFalse(target.setting('gmail_tokens'))
        self.assertEqual(target.restore(backup)['leads_added'],0)
    def test_restart_persists_records(self):
        self.lead();new=Engine(self.engine.data);self.assertEqual(len(new.list()),1)
    def test_storage_probe_reopens_database_and_file(self):
        value=self.engine.storage_probe({'action':'start'})
        with self.assertRaises(ValueError):self.engine.storage_probe({'action':'verify','nonce':value['nonce']})
        reopened=Engine(self.engine.data)
        with self.assertRaises(ValueError):reopened.storage_probe({'action':'verify','nonce':'wrong'})
        self.assertTrue(reopened.storage_probe({'action':'verify','nonce':value['nonce']})['verified'])
        self.assertTrue(reopened.storage()['restart_verified'])
    def test_oauth_state_required(self):
        with self.assertRaises(ValueError):self.engine.oauth_callback('unknown','code')
    def test_discovery_cache_and_source_attribution(self):
        fixture={'jobs':[{'company_name':'Example','title':'CRM specialist','url':'https://example.com/job','description':'<p>CRM pipelines</p>','salary':'$50/hour','candidate_required_location':'USA'}]}
        with patch('engine.urllib.request.urlopen',side_effect=ValueError('RSS offline')),patch('engine.fetch_json',return_value=fixture) as api:
            self.assertEqual(self.engine.scan()['added'],1);self.assertTrue(self.engine.scan()['cached']);self.assertEqual(api.call_count,1)
        self.assertEqual(self.engine.list()[0]['source'],'Remotive')
    def test_failed_discovery_can_retry(self):
        with patch('engine.urllib.request.urlopen',side_effect=ValueError('RSS offline')),patch('engine.fetch_json',side_effect=ValueError('blocked')):self.assertTrue(self.engine.scan()['errors'])
        with patch('engine.urllib.request.urlopen',side_effect=ValueError('RSS offline')),patch('engine.fetch_json',return_value={'jobs':[]}):self.assertIn('Remotive',self.engine.scan()['sources_ok'])
    def test_ai_requires_private_evidence_and_configuration(self):
        oid=self.lead()
        with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'test','HF_MODEL':'test'}):
            with self.assertRaises(ValueError):self.engine.create_draft({'id':oid,'mode':'ai'})
class HTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);threading.Thread(target=cls.server.serve_forever,daemon=True).start();cls.base='http://127.0.0.1:'+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def request(self,path,data=None,headers=None):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
        with urllib.request.urlopen(req) as r:return json.load(r)
    def test_health_and_status(self):
        self.assertEqual(self.request('/health')['version'],'0.19.3');self.assertIn('storage',self.request('/api/status'))
    def test_research_preview_never_calls_inference(self):
        with patch('research_tools.Research.run',return_value={'checks':[],'items':[]}) as reads,patch.object(app.engine,'ai_request') as model:
            result=self.request('/api/research/preview',{'workspace':'contra','mode':'research','text':'Find Contra CRM opportunities'})
        self.assertEqual(result['items'],[]);self.assertEqual(reads.call_count,1);model.assert_not_called()

    def test_workflow(self):
        result=self.request('/api/add',{'company':'HTTP client','title':'CRM project','url':'https://example.com/http'})
        self.request('/api/update',{'id':result['id'],'contact':'a@example.com'})
        draft=self.request('/api/draft',{'id':result['id']});self.assertIn('body',draft);self.assertTrue(self.request('/api/history'))
    def test_cross_origin_refused(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/add',{},headers={'Origin':'https://evil.example'})
        self.assertEqual(e.exception.code,403)
    def test_google_signin_direct_redirect(self):
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        with patch.object(app.engine,'oauth_url',return_value='https://accounts.google.com/o/oauth2/v2/auth?state=test'):
            opener=urllib.request.build_opener(NoRedirect)
            with self.assertRaises(urllib.error.HTTPError) as e:opener.open(self.base+'/oauth/google/start')
            self.assertEqual(e.exception.code,303)
            self.assertEqual(e.exception.headers['Location'],'https://accounts.google.com/o/oauth2/v2/auth?state=test')
    def test_static_ui(self):
        with urllib.request.urlopen(self.base+'/') as r:self.assertIn(b'My profile',r.read())
