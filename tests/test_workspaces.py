import json,os,tempfile,unittest
from unittest.mock import patch
from engine import Engine
class Workspaces(unittest.TestCase):
 def setUp(self):self.e=Engine(tempfile.mkdtemp())
 def test_conversations_are_separate_and_survive_backup(self):
  a=self.e.add({'company':'A','title':'CRM','source':'Contra'})['id'];b=self.e.add({'company':'B','title':'CRM','source':'Contra'})['id']
  self.e.add_work_note({'workspace':'contra','opportunity_id':a,'text':'A only'})
  self.e.add_work_note({'workspace':'contra','text':'Platform planning'})
  self.assertEqual(self.e.conversation({'workspace':'contra','opportunity_id':b})['notes'],[])
  with self.assertRaises(ValueError):self.e.conversation({'workspace':'gmail','opportunity_id':a})
  restored=Engine(tempfile.mkdtemp());restored.restore(self.e.backup())
  self.assertEqual(restored.conversation({'workspace':'contra','opportunity_id':a})['notes'][0]['text'],'A only')
 def test_owner_can_move_opportunity_and_notes_together(self):
  a=self.e.add({'company':'A','title':'CRM','source':'Contra'})['id'];w=self.e.add_workspace({'name':'Another platform'})['id']
  self.e.add_work_note({'workspace':'contra','opportunity_id':a,'text':'Keep with A'})
  self.e.update({'id':a,'workspace':w})
  self.assertEqual(self.e.conversation({'workspace':w,'opportunity_id':a})['notes'][0]['text'],'Keep with A')
 def test_ai_context_never_includes_other_opportunity(self):
  a=self.e.add({'company':'Selected','title':'CRM','source':'Contra'})['id'];b=self.e.add({'company':'Other private client','title':'CRM','source':'Contra'})['id']
  self.e.add_work_note({'workspace':'contra','opportunity_id':b,'text':'OTHER SECRET CONTEXT'})
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch('engine.fetch_json',return_value={'choices':[{'message':{'content':'Next step: review the requirements.'}}]}) as call:
   self.e.ask_workspace({'workspace':'contra','opportunity_id':a,'text':'What next?'})
  payload=json.dumps(call.call_args.args[1]);self.assertNotIn('OTHER SECRET CONTEXT',payload);self.assertNotIn('Other private client',payload)
  notes=self.e.conversation({'workspace':'contra','opportunity_id':a})['notes'];self.assertEqual(notes[-1]['role'],'assistant')
  self.assertEqual(self.e.setting('ai_usage')['count'],1)
 def test_connection_check_does_not_make_paid_ai_calls(self):
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch('engine.fetch_json') as call:
   result=self.e.check_connections()
  call.assert_not_called();self.assertEqual(result['writing']['status'],'configured');self.assertEqual(result['contra']['status'],'not_connected')
