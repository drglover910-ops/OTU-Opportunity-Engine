import json,unittest
from scripts.chat_delivery_diagnostic import diagnose
class DeliveryDiagnosticTests(unittest.TestCase):
 def test_only_safe_metadata_retained(self):
  def request(path):
   return {'notes':[{'id':4,'text':'PRIVATE_NOTE'}],'requests':[{'created':'2026-10-18T00:00:00Z','status':'complete','assistant_note_id':4,'payload':{'text':'Isis, find Contra GoHighLevel jobs.','mode':'advice','credential':'SECRET'},'result':{'answer':'Research results — direct summary of returned records. PRIVATE_ANSWER','research':{'checks':[{'tool':'list_job_feed','status':'cached','count':0,'private':'PRIVATE_LISTING'}]}}}]}
  result=diagnose(request,[{'workspace':'contra','id':'PRIVATE_CHAT_ID','title':'PRIVATE_TITLE','opportunity_id':None}]);encoded=json.dumps(result)
  self.assertNotIn('PRIVATE',encoded);self.assertNotIn('SECRET',encoded)
  row=result['conversations'][0]['requests'][0];self.assertTrue(row['matches_test_prompt']);self.assertTrue(row['answer_note_present']);self.assertEqual(row['answer_format'],'older_research_summary')
 def test_reads_are_bounded_and_exclude_other_workspaces(self):
  paths=[]
  def request(path):paths.append(path);return {'requests':[]}
  result=diagnose(request,[{'workspace':'public','id':'other'}]+[{'workspace':'contra','id':str(i),'opportunity_id':None} for i in range(15)])
  self.assertEqual(len(paths),8);self.assertEqual(len(result['conversations']),8);self.assertTrue(all('workspace=contra' in p for p in paths))
 def test_read_error_never_includes_exception_or_retries(self):
  def request(path):raise ValueError('PRIVATE_ERROR')
  result=diagnose(request,[{'workspace':'assistant','id':None,'opportunity_id':None}]);self.assertEqual(result['conversations'][0]['status'],'read_unavailable');self.assertNotIn('PRIVATE_ERROR',json.dumps(result))
