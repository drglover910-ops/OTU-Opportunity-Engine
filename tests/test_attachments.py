import base64,io,tempfile,unittest
from unittest.mock import patch
from engine import Engine
from attachment_store import AttachmentStore,MAX_FILE,CHUNK
class Attachments(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.e=Engine(self.temp.name);self.s=AttachmentStore(self.e)
 def start(self,**values):return self.s.start({'workspace':'assistant','name':'example.txt','size':6,**values})
 def chunk(self,key,raw,offset):return self.s.chunk({'id':key,'offset':offset,'content':base64.b64encode(raw).decode()})
 def test_resume_restart_and_idempotent_retry(self):
  key=self.start()['id'];self.chunk(key,b'abc',0)
  self.s=AttachmentStore(Engine(self.temp.name));self.assertEqual(self.s.row(key)['received'],3)
  self.assertEqual(self.chunk(key,b'abc',0)['received'],3)
  with self.assertRaises(ValueError):self.chunk(key,b'bad',0)
  with self.assertRaises(ValueError):self.s.finish({'id':key})
  self.chunk(key,b'def',3);self.s.finish({'id':key});path,row=self.s.file(key);self.assertEqual(path.read_bytes(),b'abcdef');self.assertEqual(row['state'],'complete');self.assertEqual(self.s.status()['used'],6)
 def test_capacity_and_reservations(self):
  with patch.dict('os.environ',{'OTU_ATTACHMENT_QUOTA_BYTES':str(MAX_FILE)}):
   key=self.start(size=MAX_FILE)['id'];self.assertEqual(self.s.status()['reserved'],MAX_FILE)
   with self.assertRaises(ValueError):self.start()
   self.s.cancel({'id':key});self.assertEqual(self.s.status()['reserved'],0)
  with self.assertRaises(ValueError):self.start(size=MAX_FILE+1)
  with self.assertRaises(ValueError):self.start(name='script.html')
 def test_scope_isolation_and_invalid_opportunity(self):
  first=self.e.create_chat({'workspace':'assistant'});second=self.e.create_chat({'workspace':'assistant'})
  self.start(chat_id=first['id']);self.assertEqual(len(self.s.listing({'workspace':'assistant','chat_id':first['id']})),1)
  self.assertEqual(self.s.listing({'workspace':'assistant','chat_id':second['id']}),[])
  with self.assertRaises(ValueError):self.start(workspace='contra',chat_id=first['id'])
  with self.assertRaises(ValueError):self.s.row('../../etc/passwd')
 def test_photo_preview_is_decoded_and_bounded(self):
  from PIL import Image
  raw=io.BytesIO();Image.new('RGB',(40,40),'green').save(raw,format='PNG');data=raw.getvalue()
  key=self.start(name='image.png',size=len(data))['id'];self.chunk(key,data,0);self.s.finish({'id':key});preview=self.s.photo(key);self.assertTrue(preview.startswith(b'\xff\xd8'));self.assertLess(len(preview),10000)
 def test_scope_follows_moved_opportunity(self):
  oid=self.e.add({'company':'Example','title':'CRM role','description':'CRM','workspace':'contra'})['id']
  key=self.start(workspace='contra',opportunity_id=oid)['id'];row=self.e.get(oid);row['workspace']='assistant';self.e.update(row)
  self.assertEqual(self.s.row(key)['workspace'],'assistant')

 def test_completed_removal_requires_explicit_confirmation(self):
  key=self.start()['id'];self.chunk(key,b'abcdef',0);self.s.finish({'id':key})
  with self.assertRaises(ValueError):self.s.remove({'id':key})
  self.s.remove({'id':key,'confirmed':True});self.assertEqual(self.s.status()['used'],0)
