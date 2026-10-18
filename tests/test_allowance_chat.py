import json,os,tempfile,time,unittest
from datetime import datetime,timezone
from unittest.mock import patch
from engine import Engine,AIAllowanceError
from chat_service import ChatService
from tests.test_research_tools import BODY

class AllowanceChatTests(unittest.TestCase):
 def setUp(self):
  folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.e=Engine(folder.name);self.service=ChatService(self.e)
  self.scope={'workspace':'contra','chat_id':self.e.create_chat({'workspace':'contra'})['id']}
  env=patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'});env.start();self.addCleanup(env.stop)
 def wait(self,key):
  for _ in range(150):
   row=self.service.row(key)
   if row['status'] not in ('queued','running'):return row
   time.sleep(.01)
  self.fail('Request did not finish')
 def research(self):
  self.e.set_setting('contra_tokens',{'access_token':'fixture'})
  with patch('contra_mcp.ContraConnection.read_tools',return_value={'list_job_feed:0':BODY}),patch.object(self.e,'ai_request',return_value={'choices':[{'message':{'content':'A returned option.'}}]}):
   return self.wait(self.service.start({**self.scope,'text':'Find Contra CRM jobs','request_id':'r'*32})['id'])
 def test_token_cap_blocks_with_requests_remaining_and_saves_local_reply(self):
  usage={'date':self.e.ai_budget()['date'],'count':2,'reserved_tokens':59999,'actual_tokens':9000};self.e.set_setting('ai_usage',usage)
  with patch.object(self.e,'ai_request') as model,patch('contra_mcp.ContraConnection.read_tools') as platform:
   row=self.wait(self.service.start({**self.scope,'text':'Which option should I review?','request_id':'t'*32})['id'])
  model.assert_not_called();platform.assert_not_called();self.assertEqual(row['status'],'complete');self.assertFalse(row['result']['ai_used']);self.assertEqual(row['result']['writing_status']['reason'],'tokens');self.assertIn('2 of 5',row['result']['answer']);self.assertIn('not your Hugging Face credit balance',row['result']['answer']);self.assertEqual(self.e.setting('ai_usage'),usage)
 def test_blocked_followup_returns_only_same_conversation_saved_research(self):
  self.research();self.e.save_ai_limits({'daily_requests':0})
  with patch.object(self.e,'ai_request') as model,patch('contra_mcp.ContraConnection.read_tools') as platform:
   row=self.wait(self.service.start({**self.scope,'text':'Tell me more about the first one.','request_id':'f'*32})['id'])
  model.assert_not_called();platform.assert_not_called();self.assertEqual(row['status'],'complete');result=row['result'];self.assertIn('Example CRM contract',result['answer']);self.assertIn('no new platform check',result['answer']);self.assertEqual(result['research']['checks'][-1]['status'],'previous_read');self.assertEqual(result['writing_status']['reason'],'requests')
  other={'workspace':'contra','chat_id':self.e.create_chat({'workspace':'contra'})['id']}
  result=self.e.ask_workspace({**other,'text':'Which option should I review?'})
  self.assertIsNone(result['research']);self.assertNotIn('Example CRM contract',result['answer']);self.assertEqual(result['sources'],[])
 def test_paused_edit_never_becomes_a_document_suggestion(self):
  oid=self.e.add({'company':'Document fixture','title':'CRM','workspace':'contra'})['id'];self.e.save_ai_limits({'paused':True})
  with patch.object(self.e,'packages',return_value=[{'opportunity_id':oid,'files':json.dumps({'resume':123})}]),patch.object(self.e,'document_preview',return_value={'id':123,'text':'Original document text','name':'original.pdf'}),patch.object(self.e,'ai_request') as model:
   result=self.e.ask_workspace({'workspace':'contra','opportunity_id':oid,'document_id':123,'mode':'revise_document','text':'Improve this document.'})
  model.assert_not_called();self.assertIsNone(result['document_id']);self.assertIsNone(result['draft_id']);self.assertEqual(result['writing_status']['reason'],'paused')
 def test_concurrent_allowance_denial_is_local_not_provider_failure(self):
  with patch.object(self.e,'ai_request',side_effect=AIAllowanceError('tokens','Local reservation blocked.')) as model:
   result=self.e.ask_workspace({**self.scope,'text':'Explain the options.'})
  self.assertEqual(model.call_count,1);self.assertFalse(result['ai_used']);self.assertEqual(result['writing_status']['reason'],'tokens');self.assertNotIn('attempt may still count',result['answer']);self.assertEqual(self.e.ai_budget()['count'],0)
 def test_reset_is_next_utc_midnight(self):
  reset=datetime.fromisoformat(self.e.ai_budget()['next_reset_at']);self.assertEqual(reset.tzinfo,timezone.utc);self.assertEqual((reset.hour,reset.minute,reset.second),(0,0,0));self.assertGreater(reset,datetime.now(timezone.utc))
