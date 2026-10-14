import base64,unittest,json,tempfile
from unittest.mock import patch
from engine import Engine
from mail_history import body,summarize,study
class MailHistory(unittest.TestCase):
 def message(self,direction,text,automated=False):return {'direction':direction,'body':text,'automated':automated,'date':'2026-10-14T10:00:00+00:00'}
 def test_mime_text_and_quote_removal(self):
  data=base64.urlsafe_b64encode(b'Hello, I am interested.\nOn Wednesday, Brian wrote:\nOld quoted message').decode().rstrip('=')
  self.assertEqual(body({'mimeType':'text/plain','body':{'data':data}}),'Hello, I am interested.')
 def test_acknowledgment_is_not_human_success(self):
  r=summarize([self.message('sent','Application'),self.message('received','We received your application',True)])
  self.assertEqual(r['status'],'Automated acknowledgment only');self.assertEqual(r['human_replies'],0);self.assertFalse(r['paid_outcome_verified'])
 def test_interview_and_paperwork_have_different_context(self):
  r=summarize([self.message('sent','I am interested'),self.message('received','We would like an interview. Please send your resume.')])
  self.assertEqual(r['stage'],'Interview / meeting');self.assertEqual(r['relationship'],'Requested paperwork');self.assertFalse(r['paid_outcome_verified'])
 def test_import_uses_sent_and_full_thread_without_sending(self):
  e=Engine(tempfile.mkdtemp());data=base64.urlsafe_b64encode(b'I am interested in Buffalo Stallions. Please find my resume attached.').decode()
  thread={'messages':[{'id':'m1','threadId':'t1','labelIds':['SENT'],'internalDate':'1791972000000','payload':{'mimeType':'text/plain','headers':[{'name':'From','value':'owner@example.com'},{'name':'To','value':'coach@example.com'},{'name':'Subject','value':'Buffalo Stallions coaching'}],'body':{'data':data}}}]}
  def response(url,**kw):
   if url.endswith('/profile'):return {'emailAddress':'owner@example.com'}
   if '/threads/' in url:return thread
   return {'messages':[{'id':'m1','threadId':'t1'}]}
  with patch.object(e,'gmail_token',return_value='test'),patch('mail_history.fetch_json',side_effect=response) as api:study(e)
  self.assertEqual(len(e.email_cases()),1);self.assertEqual(e.list()[0]['source'],'Gmail history');self.assertEqual(e.setting('history_study')['status'],'complete');self.assertEqual(e.setting('outreach_style')['sent_messages_reviewed'],1)
  self.assertTrue(all('/send' not in c.args[0] for c in api.call_args_list))
  oid=e.list()[0]['id'];did=e.create_draft({'id':oid})['id'];self.assertTrue(e.draft(did)['subject'].startswith('Re:'))
  with self.assertRaises(ValueError):e.approve({'id':did,'confirmation':'I reviewed recipient, content, attachments and history'})
  e.approve({'id':did,'confirmation':'I reviewed recipient, content, attachments and history','repeat_confirmed':True})
 def test_threads_survive_backup(self):
  e=Engine(tempfile.mkdtemp());oid=e.add({'company':'X','title':'Conversation'})['id']
  with e.connect() as c:c.execute('INSERT INTO email_threads VALUES(?,?,?,?,?,?,?)',('t',oid,'X','Subject',json.dumps({'status':'No reply found'}),'[]','2026-10-14'))
  target=Engine(tempfile.mkdtemp());target.restore(e.backup());self.assertEqual(len(target.email_cases()),1)
