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
   try:self.e.ai_request(self.payload);return True
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
