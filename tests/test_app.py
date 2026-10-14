import os,tempfile,unittest,threading,urllib.request,json
os.environ['OTU_DATA_DIR']=tempfile.mkdtemp()
import app
class Workflow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
  threading.Thread(target=cls.server.serve_forever,daemon=True).start()
  cls.base='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
 def request(self,path,data=None):
  req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req) as r:return json.load(r)
 def test_persistence_duplicate_and_stage(self):
  d={'company':'Example','title':'CRM setup','url':'https://example.com/project','category':'CRM / GoHighLevel'}
  self.request('/api/add',d);self.request('/api/add',d)
  rows=self.request('/api/opportunities');self.assertEqual(len(rows),1)
  self.request('/api/update',{'id':rows[0]['id'],'stage':'Contacted','contact':'test@example.com','notes':'Private','followup':'2026-10-20'})
  self.assertEqual(self.request('/api/opportunities')[0]['stage'],'Contacted')
 def test_reject_script_link(self):
  with self.assertRaises(ValueError):app.save({'company':'X','title':'Y','url':'javascript:alert(1)'})
 def test_health(self):self.assertEqual(self.request('/health')['status'],'ok')
