import json,os,tempfile,threading,time,unittest
from unittest.mock import patch
from engine import Engine
from chat_service import ChatService
from attachment_store import AttachmentStore
from workspace_ops import WorkspaceOps
from backup_store import Backups

class AcknowledgedChat(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.e=Engine(self.tmp.name);self.service=ChatService(self.e)
  self.chat=self.e.create_chat({'workspace':'contra'});self.scope={'workspace':'contra','chat_id':self.chat['id']}
 def request(self,key='a'*32,**extra):return {**self.scope,'text':'Help me choose paid CRM work.','mode':'advice','request_id':key,**extra}
 def wait(self,key):
  deadline=time.monotonic()+4
  while time.monotonic()<deadline:
   row=self.service.row(key)
   if row['status'] not in ('queued','running'):return row
   time.sleep(.01)
  self.fail('Fixture request did not complete')
 def test_immediate_ack_dedup_one_saved_question_and_budget_call(self):
  ready=threading.Event();release=threading.Event();calls=[]
  def model(payload):
   calls.append(payload);ready.set();release.wait(3)
   return {'choices':[{'message':{'content':'Review the existing unsent draft first.'}}]}
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch.object(self.e,'ai_request',side_effect=model):
   start=time.monotonic();row=self.service.start(self.request());self.assertLess(time.monotonic()-start,.5);self.assertTrue(ready.wait(1))
   self.assertEqual(self.service.start(self.request())['id'],row['id'])
   with self.assertRaises(ValueError):self.service.start(self.request(key='b'*32))
   context=self.e.conversation(self.scope);self.assertEqual([n['role'] for n in context['notes']],['user']);self.assertEqual(context['notes'][0]['text'],'Help me choose paid CRM work.')
   release.set();result=self.wait(row['id']);self.assertEqual(result['status'],'complete');self.assertEqual(len(calls),1)
   self.service.start(self.request());self.assertEqual(len(calls),1)
  notes=self.e.conversation(self.scope)['notes'];self.assertEqual([n['role'] for n in notes],['user','assistant']);self.assertEqual(result['assistant_note_id'],notes[-1]['id'])
  user_payload=json.loads(calls[0]['messages'][1]['content']);self.assertEqual(user_payload['previous_notes'],[])
  with self.assertRaises(ValueError):self.service.start(self.request(text='A different question'))
 def test_failure_keeps_question_and_does_not_retry(self):
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch.object(self.e,'ai_request',side_effect=ValueError('Provider temporarily unavailable')) as model:
   row=self.service.start(self.request());result=self.wait(row['id']);self.assertEqual(result['status'],'failed')
   self.service.start(self.request());self.assertEqual(model.call_count,1)
  self.assertEqual(len(self.e.conversation(self.scope)['notes']),1)
 def test_feedback_scoped_and_in_next_context(self):
  answer=self.e.add_work_note({**self.scope,'text':'A poorly supported suggestion'},role='assistant')['id']
  self.e.response_feedback({**self.scope,'note_id':answer,'rating':-1})
  other=self.e.create_chat({'workspace':'contra'})
  with self.assertRaises(ValueError):self.e.response_feedback({'workspace':'contra','chat_id':other['id'],'note_id':answer,'rating':1})
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch.object(self.e,'ai_request',return_value={'choices':[{'message':{'content':'Here is a grounded correction.'}}]}) as model:
   self.e.ask_workspace({**self.scope,'text':'Correct that suggestion.'})
   context=json.loads(model.call_args.args[0]['messages'][1]['content']);self.assertEqual(context['previous_notes'][0]['owner_rating'],-1)
   self.assertIn('wallet verification',model.call_args.args[0]['messages'][0]['content'])
  self.e.response_feedback({**self.scope,'note_id':answer,'rating':0});self.assertEqual(self.e.conversation(self.scope)['notes'][0]['feedback'],0)
 def test_restart_and_complete_backup_preserve_ratings_receipts_and_notes(self):
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch.object(self.e,'ai_request',return_value={'choices':[{'message':{'content':'Saved reply'}}]}):
   row=self.service.start(self.request());result=self.wait(row['id'])
  self.e.response_feedback({**self.scope,'note_id':result['assistant_note_id'],'rating':1})
  with self.e.connect() as c:c.execute("UPDATE chat_requests SET status='running' WHERE id=?",(row['id'],))
  ChatService(self.e);self.assertEqual(self.service.row(row['id'])['status'],'interrupted')
  AttachmentStore(self.e);WorkspaceOps(self.e);archive=Backups(self.e).export()
  with tempfile.TemporaryDirectory() as folder:
   target=Engine(folder);AttachmentStore(target);WorkspaceOps(target);target.add_work_note({'workspace':'assistant','text':'Existing work must remain.'})
   with patch.object(target,'ai_request') as inference:Backups(target).restore(archive);inference.assert_not_called()
   imported=target.conversation(self.scope);self.assertEqual(len(imported['notes']),2);self.assertEqual(imported['notes'][-1]['feedback'],1)
   job=ChatService(target).row(row['id']);self.assertEqual(job['status'],'interrupted');self.assertEqual(job['assistant_note_id'],imported['notes'][-1]['id']);self.assertEqual(job['result']['note_id'],job['assistant_note_id'])
   self.assertEqual(target.conversation({'workspace':'assistant'})['notes'][0]['text'],'Existing work must remain.')

 def test_global_limit_and_safe_project_move_during_inference(self):
  oid=self.e.add({'company':'Scope fixture','title':'CRM','workspace':'contra'})['id'];chat=self.e.create_chat({'workspace':'contra','opportunity_id':oid});release=threading.Event()
  def provider(payload):release.wait(3);return {'choices':[{'message':{'content':'Keep this in its scope.'}}]}
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch.object(self.e,'ai_request',side_effect=provider):
   first=self.service.start({'workspace':'contra','opportunity_id':oid,'chat_id':chat['id'],'text':'A scoped question','request_id':'c'*32})
   rows=[first]
   for key in ('d','e'):
    other=self.e.create_chat({'workspace':'assistant'});rows.append(self.service.start({'workspace':'assistant','chat_id':other['id'],'text':'Another conversation','request_id':key*32}))
   with self.assertRaises(ValueError):self.service.start(self.request(key='f'*32))
   with self.assertRaises(ValueError):self.e.update({'id':oid,'workspace':'other'})
   ops=WorkspaceOps(self.e);project=ops.create_project({'name':'Safe grouping'})['id'];ops.change({'key':chat['id'],'action':'move','project_id':project})
   release.set()
   for row in rows:self.assertEqual(self.wait(row['id'])['status'],'complete')
  self.e.update({'id':oid,'workspace':'other'});moved=self.service.row(first['id']);self.assertEqual(moved['workspace'],'other');self.assertEqual(moved['payload']['workspace'],'other')
  self.assertEqual(self.e.conversation({'workspace':'other','opportunity_id':oid,'chat_id':chat['id']})['notes'][-1]['text'],'Keep this in its scope.')
