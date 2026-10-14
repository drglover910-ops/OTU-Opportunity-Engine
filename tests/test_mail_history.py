import base64,unittest,json,tempfile
from unittest.mock import patch
from engine import Engine,safe_url
from mail_history import body,summarize,study,refresh_known_thread
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

 def test_gmail_thread_links_remain_distinct(self):
  a=safe_url("https://mail.google.com/mail/u/0/#all/abc123")
  b=safe_url("https://mail.google.com/mail/u/0/#all/abc456")
  self.assertNotEqual(a,b)
  self.assertEqual(safe_url("https://example.com/listing#tracking"),"https://example.com/listing")

 def test_revised_offer_is_tracked_without_claiming_a_win(self):
  r=summarize([self.message('sent','Following up'),self.message('received','We increased the offer from 25% to 35% of net operating profit.')])
  self.assertEqual(r['stage'],'Offer / contract');self.assertFalse(r['paid_outcome_verified'])
 def test_newer_rejection_supersedes_old_interview(self):
  r=summarize([self.message('received','Let us schedule an interview'),self.message('sent','Thank you'),self.message('received','We are not moving forward.')])
  self.assertEqual(r['stage'],'Parked')

 def test_refresh_updates_thread_but_preserves_manual_outcome(self):
  e=Engine(tempfile.mkdtemp());oid=e.add({'company':'X','title':'Coaching','source':'Gmail history'})['id']
  e.update({'id':oid,'stage':'Contacted'})
  with e.connect() as c:c.execute('INSERT INTO email_threads VALUES(?,?,?,?,?,?,?)',('t',oid,'X','Coaching',json.dumps({'stage':'Contacted'}),'[]','2026-10-14'))
  raw={'id':'t','messages':[{'id':'m','threadId':'t','internalDate':'1791972000000','payload':{'mimeType':'text/plain','headers':[{'name':'From','value':'employer@example.com'}],'body':{'data':base64.urlsafe_b64encode(b'We are pleased to offer you this role.').decode()}}}]}
  refresh_known_thread(e,'t',raw)
  self.assertEqual(e.get(oid)['stage'],'Offer / contract')
  e.update({'id':oid,'stage':'Won'})
  raw['messages'][0]['payload']['body']['data']=base64.urlsafe_b64encode(b'We are not moving forward.').decode()
  refresh_known_thread(e,'t',raw)
  self.assertEqual(e.get(oid)['stage'],'Won')
  self.assertEqual(e.email_case('t')['summary']['stage'],'Parked')
