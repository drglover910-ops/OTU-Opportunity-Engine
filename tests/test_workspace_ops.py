import base64,hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from engine import Engine
from attachment_store import AttachmentStore
from workspace_ops import WorkspaceOps
from backup_store import Backups

class WorkspaceOperations(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.e=Engine(self.tmp.name);self.files=AttachmentStore(self.e);self.ops=WorkspaceOps(self.e)
 def upload(self,scope,body=b'private photo and notes'):
  r=self.files.start({**scope,'name':'notes.txt','size':len(body)})
  self.files.chunk({'id':r['id'],'offset':0,'content':base64.b64encode(body).decode()});self.files.finish({'id':r['id']});return r['id']
 def test_legacy_menu_preserves_content_and_scope(self):
  self.e.add_work_note({'workspace':'contra','text':'Historical work'})
  row=next(t for t in self.ops.threads() if t['workspace']=='contra')
  project=self.ops.create_project({'name':'Client work'})['id'];key=row['key']
  self.ops.change({'key':key,'action':'move','project_id':project});self.ops.change({'key':key,'action':'rename','title':'Old work'})
  self.ops.change({'key':key,'action':'pin'});self.ops.change({'key':key,'action':'archive'})
  with self.assertRaises(ValueError):self.ops.change({'key':key,'action':'trash'})
  self.ops.change({'key':key,'action':'trash','confirmed':True});self.ops.change({'key':key,'action':'restore'})
  row=next(t for t in self.ops.threads() if t['key']==key)
  self.assertEqual((row['title'],row['workspace'],row['project_id'],row['pinned'],row['trashed']),('Old work','contra',project,True,False))
  self.assertEqual(self.e.conversation({'workspace':'contra'})['notes'][0]['text'],'Historical work')
 def test_full_backup_merges_uploads_chat_notes_and_metadata(self):
  oid=self.e.add({'company':'Private client','title':'CRM','workspace':'contra','url':'https://example.com/work'})['id']
  chat=self.e.create_chat({'workspace':'contra','opportunity_id':oid});scope={'workspace':'contra','opportunity_id':oid,'chat_id':chat['id']}
  self.e.add_work_note({**scope,'text':'Keep this exact conversation'})
  self.e.conversation_memory({**scope,'text':'Be practical'})
  fileid=self.upload(scope);project=self.ops.create_project({'name':'Growth'})['id'];self.ops.change({'key':chat['id'],'action':'move','project_id':project})
  self.e.set_setting('gmail_tokens',{'access_token':'DO-NOT-EXPORT'})
  path=Backups(self.e).export()
  with zipfile.ZipFile(path) as z:
   self.assertNotIn('DO-NOT-EXPORT',z.read('records.json').decode());self.assertEqual(z.read('attachments/'+fileid),b'private photo and notes')
  other=tempfile.TemporaryDirectory();self.addCleanup(other.cleanup);target=Engine(other.name);AttachmentStore(target);ops=WorkspaceOps(target)
  target.add({'company':'Existing','title':'Keep'})
  Backups(target).restore(path);Backups(target).restore(path)
  row=next(t for t in ops.threads() if t['id']==chat['id'])
  self.assertEqual(row['project_id'],project);self.assertEqual(row['opportunity_id'],2)
  self.assertEqual(target.conversation({**scope,'opportunity_id':2})['notes'][0]['text'],'Keep this exact conversation')
  self.assertEqual((target.data/'attachments'/fileid).read_bytes(),b'private photo and notes')
  self.assertEqual(len(target.list()),2)
  self.assertTrue(list((target.data/'backups').glob('before-restore-*.zip')))
 def test_corrupt_backup_does_not_change_records(self):
  fid=self.upload({'workspace':'assistant'});good=Backups(self.e).export();bad=self.e.data/'bad.zip'
  with zipfile.ZipFile(good) as source,zipfile.ZipFile(bad,'w') as out:
   for name in source.namelist():out.writestr(name,b'corrupt' if name=='attachments/'+fid else source.read(name))
  before=self.e.list()
  with self.assertRaises(ValueError):Backups(self.e).restore(bad)
  self.assertEqual(self.e.list(),before)
 def test_gmail_reads_and_local_folders_do_not_write_gmail(self):
  self.e.set_setting('gmail_owner','owner@example.com')
  raw={'id':'abc123','messages':[{'id':'m1','threadId':'abc123','labelIds':['INBOX'],'internalDate':'1000','payload':{'headers':[{'name':'From','value':'client@example.com'},{'name':'To','value':'owner@example.com'},{'name':'Subject','value':'Project'}],'mimeType':'text/plain','body':{'data':base64.urlsafe_b64encode(b'Can we discuss this project?').decode()}}}]}
  with patch.object(self.e,'gmail_token',return_value='fixture'),patch('workspace_ops.fetch_json',side_effect=[{'threads':[{'id':'abc123','snippet':'Project'}],'nextPageToken':'next'},raw,raw]) as fetch:
   page=self.ops.mail_list({'box':'inbox','search':'client'});self.assertEqual(page['next_page'],'next')
   thread=self.ops.mail_thread('abc123');self.assertEqual(thread['messages'][0]['body'],'Can we discuss this project?')
   self.assertEqual(len(fetch.call_args_list),3)
   self.assertTrue(all(not call.kwargs.get('method') and 'data' not in call.kwargs for call in fetch.call_args_list))
  oid=self.e.add({'company':'Mail client','title':'CRM work','workspace':'contra'})['id']
  self.ops.organize_mail({'action':'folder','name':'Follow up'});folder=self.ops.folders()[0]['id'];self.ops.organize_mail({'thread_id':'abc123','folder_id':folder,'followup':'2026-10-20','opportunity_id':oid})
  self.assertEqual(self.e.conversation({'workspace':'contra','opportunity_id':oid})['email_threads'][0]['messages'][0]['body'],'Can we discuss this project?')
  other=self.e.add({'company':'Other client','title':'Different'})['id']
  with self.assertRaises(ValueError):self.ops.organize_mail({'thread_id':'abc123','opportunity_id':other})
  with patch.object(self.e,'gmail_token',return_value='fixture'),patch('workspace_ops.fetch_json') as fetch:
   result=self.ops.mail_list({'box':folder});self.assertEqual(result['items'][0]['organization']['followup'],'2026-10-20');fetch.assert_not_called()

 def test_restore_without_url_and_project_name_collision(self):
  oid=self.e.add({'company':'No URL client','title':'Workflow','workspace':'contra'})['id']
  chat=self.e.create_chat({'workspace':'contra','opportunity_id':oid});project=self.ops.create_project({'name':'Shared name'})['id'];self.ops.change({'key':chat['id'],'action':'move','project_id':project})
  Backups(self.e).checkpoint();self.assertTrue(Backups(self.e).status()['preserved'])
  archive=Backups(self.e).export()
  with tempfile.TemporaryDirectory() as tmp:
   target=Engine(tmp);AttachmentStore(target);ops=WorkspaceOps(target);other=ops.create_project({'name':'Shared name'})['id']
   Backups(target).restore(archive)
   self.assertEqual(next(t for t in ops.threads() if t['id']==chat['id'])['project_id'],other)
