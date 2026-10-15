import tempfile,unittest
from engine import Engine
class ChatThreads(unittest.TestCase):
 def setUp(self):self.e=Engine(tempfile.mkdtemp())
 def test_notes_and_memory_do_not_cross_new_chats_or_original(self):
  a=self.e.create_chat({'workspace':'assistant'});b=self.e.create_chat({'workspace':'assistant'})
  one={'workspace':'assistant','chat_id':a['id']};two={'workspace':'assistant','chat_id':b['id']}
  self.e.add_work_note({**one,'text':'Only chat A'});self.e.conversation_memory({**one,'text':'A instruction'})
  self.assertEqual(self.e.conversation(two)['notes'],[]);self.assertEqual(self.e.conversation(two)['memory'],[])
  self.assertEqual(self.e.conversation({'workspace':'assistant'})['notes'],[])
  self.e.rename_chat({'id':a['id'],'title':'My income plan'});self.assertEqual(next(t for t in self.e.chat_threads() if t['id']==a['id'])['title'],'My income plan')
 def test_scope_cannot_be_forged(self):
  a=self.e.create_chat({'workspace':'assistant'})
  with self.assertRaises(ValueError):self.e.add_work_note({'workspace':'contra','chat_id':a['id'],'text':'Wrong workspace'})
 def test_restore_retains_original_and_new_chat_separation(self):
  a=self.e.create_chat({'workspace':'assistant'});self.e.add_work_note({'workspace':'assistant','chat_id':a['id'],'text':'New chat'})
  self.e.add_work_note({'workspace':'assistant','text':'Original chat'})
  self.e.conversation_memory({'workspace':'assistant','chat_id':a['id'],'text':'Keep this scoped'})
  request=self.e.queue_developer_request({'workspace':'assistant','chat_id':a['id'],'text':'Improve my review panel.','reviewed':True})
  target=Engine(tempfile.mkdtemp());target.restore(self.e.backup())
  self.assertEqual(target.conversation({'workspace':'assistant','chat_id':a['id']})['notes'][0]['text'],'New chat')
  self.assertEqual(target.conversation({'workspace':'assistant'})['notes'][0]['text'],'Original chat')
  self.assertEqual(target.developer_requests()[0]['chat_id'],a['id'])
  self.assertEqual(len(target.conversation({'workspace':'assistant','chat_id':a['id']})['memory']),1)
 def test_moving_opportunity_preserves_thread(self):
  oid=self.e.add({'company':'A','title':'CRM','source':'Contra','workspace':'contra'})['id'];chat=self.e.create_chat({'workspace':'contra','opportunity_id':oid})
  self.e.add_work_note({'workspace':'contra','opportunity_id':oid,'chat_id':chat['id'],'text':'Keep this work'})
  self.e.update({'id':oid,'workspace':'other'})
  self.assertEqual(self.e.conversation({'workspace':'other','opportunity_id':oid,'chat_id':chat['id']})['notes'][0]['text'],'Keep this work')
 def test_ai_context_and_reply_remain_in_selected_chat(self):
  import os,json
  from unittest.mock import patch
  a=self.e.create_chat({'workspace':'assistant'});b=self.e.create_chat({'workspace':'assistant'})
  self.e.add_work_note({'workspace':'assistant','chat_id':a['id'],'text':'PRIVATE_A_ONLY'})
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch('engine.fetch_json',return_value={'choices':[{'message':{'content':'Answer for B'}}]}) as request:
   self.e.ask_workspace({'workspace':'assistant','chat_id':b['id'],'text':'Help with B'})
   context=json.loads(request.call_args.args[1]['messages'][1]['content']);self.assertNotIn('PRIVATE_A_ONLY',str(context))
  self.assertEqual(self.e.conversation({'workspace':'assistant','chat_id':b['id']})['notes'][-1]['text'],'Answer for B')
  self.assertEqual(len(self.e.conversation({'workspace':'assistant','chat_id':a['id']})['notes']),1)
