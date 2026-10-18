import os,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from engine import Engine

class AIBudget(unittest.TestCase):
 def setUp(self):
  self.e=Engine(tempfile.mkdtemp());self.env=patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'});self.env.start();self.addCleanup(self.env.stop)
  self.payload={'messages':[{'role':'user','content':'Hello'}],'max_tokens':700}
 def test_concurrent_calls_share_persistent_limit(self):
  self.e.save_ai_limits({'daily_requests':1,'daily_tokens':60000})
  def attempt(_):
   try:self.e.ai_request({**self.payload,'messages':[{'role':'user','content':str(_)}]});return True
   except ValueError:return False
  with patch('engine.fetch_json',return_value={'usage':{'total_tokens':12}}) as req:
   with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(attempt,range(4)))
  self.assertEqual(sum(results),1);self.assertEqual(req.call_count,1)
  reopened=Engine(str(self.e.data));self.assertEqual(reopened.ai_budget()['count'],1);self.assertEqual(reopened.ai_budget()['actual_tokens'],12)
 def test_pause_and_oversize_block_before_provider(self):
  with patch('engine.fetch_json') as req:
   self.e.save_ai_limits({'paused':True})
   with self.assertRaises(ValueError):self.e.ai_request(self.payload)
   self.e.save_ai_limits({'paused':False})
   with self.assertRaises(ValueError):self.e.ai_request({'messages':[{'content':'x'*25000}]})
   req.assert_not_called()
 def test_failed_attempt_keeps_reservation_and_never_retries(self):
  with patch('engine.fetch_json',side_effect=ValueError('provider unavailable')) as req:
   with self.assertRaises(ValueError):self.e.ai_request(self.payload)
  self.assertEqual(req.call_count,1);self.assertEqual(self.e.ai_budget()['count'],1);self.assertGreater(self.e.ai_budget()['reserved_tokens'],700)
 def test_token_budget_blocks_even_with_requests_remaining(self):
  self.e.save_ai_limits({'daily_requests':10,'daily_tokens':10})
  with patch('engine.fetch_json') as req:
   with self.assertRaises(ValueError):self.e.ai_request(self.payload)
   req.assert_not_called()

 def test_identical_success_is_reused_without_another_charge(self):
  with patch('engine.fetch_json',return_value={'usage':{'total_tokens':12},'choices':[{'message':{'content':'Example'}}]}) as req:
   first=self.e.ai_request(self.payload);second=self.e.ai_request(self.payload)
  self.assertEqual(first,second);self.assertEqual(req.call_count,1);self.assertEqual(self.e.ai_budget()['count'],1)

 def test_success_settles_only_own_reservation_and_cache_is_free(self):
  today=self.e.ai_budget()['date'];self.e.set_setting('ai_usage',{'date':today,'count':1,'reserved_tokens':3000,'actual_tokens':1000})
  response={'usage':{'total_tokens':120},'choices':[{'message':{'content':'A complete reply.'}}]}
  with patch('engine.fetch_json',return_value=response) as provider:
   self.e.ai_request(self.payload);self.e.ai_request(self.payload)
  budget=self.e.ai_budget();self.assertEqual(provider.call_count,1);self.assertEqual(budget['count'],2);self.assertEqual(budget['reserved_tokens'],3120);self.assertEqual(budget['actual_tokens'],1120)
 def test_missing_invalid_or_zero_measurement_keeps_estimate(self):
  for measured in (None,0,-1,True,'120'):
   with self.subTest(measured=measured):
    self.e.set_setting('ai_usage',{'date':self.e.ai_budget()['date'],'count':0,'reserved_tokens':0,'actual_tokens':0});self.e.set_setting('ai_response_cache',{})
    response={'usage':{'total_tokens':measured},'choices':[{'message':{'content':'Complete but unmeasured.'}}]}
    with patch('engine.fetch_json',return_value=response):self.e.ai_request(self.payload)
    self.assertGreater(self.e.ai_budget()['reserved_tokens'],700);self.assertEqual(self.e.ai_budget()['actual_tokens'],0)
 def test_concurrent_settlement_preserves_failed_attempt_estimate(self):
  def provider(url,payload,**kwargs):
   if payload['messages'][0]['content']=='failed':raise ValueError('fixture failure')
   return {'usage':{'total_tokens':12},'choices':[{'message':{'content':'Complete.'}}]}
  def send(value):
   try:self.e.ai_request({**self.payload,'messages':[{'role':'user','content':value}]})
   except ValueError:pass
  with patch('engine.fetch_json',side_effect=provider):
   with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(send,['failed','success']))
  budget=self.e.ai_budget();self.assertEqual(budget['count'],2);self.assertEqual(budget['actual_tokens'],12);self.assertGreater(budget['reserved_tokens'],700)
 def test_personal_migration_once_preserves_history_pause_and_later_choices(self):
  today=self.e.ai_budget()['date'];self.e.set_setting('ai_usage',{'date':today,'count':2,'reserved_tokens':42863,'actual_tokens':9348});self.e.save_ai_limits({'daily_requests':5,'daily_tokens':60000,'paused':True})
  with self.e.connect() as c:c.execute("DELETE FROM settings WHERE key='personal_allowance_v194'")
  upgraded=Engine(str(self.e.data));budget=upgraded.ai_budget();self.assertEqual((budget['daily_requests'],budget['daily_tokens']),(50,250000));self.assertTrue(budget['paused']);self.assertEqual(budget['reserved_tokens'],42863);self.assertEqual(budget['count'],2)
  upgraded.save_ai_limits({'daily_requests':12,'daily_tokens':90000});reopened=Engine(str(self.e.data));self.assertEqual(reopened.ai_budget()['daily_requests'],12);self.assertEqual(reopened.ai_budget()['daily_tokens'],90000)
 def test_warnings_use_requests_or_counted_and_held_tokens(self):
  self.e.save_ai_limits({'daily_requests':50,'daily_tokens':1000})
  for reserved,level in ((700,None),(750,75),(900,90)):
   self.e.set_setting('ai_usage',{'date':self.e.ai_budget()['date'],'count':1,'reserved_tokens':reserved,'actual_tokens':100})
   budget=self.e.ai_budget();self.assertEqual(budget['warning_level'],level);self.assertEqual(budget['unsettled_tokens'],reserved-100)
