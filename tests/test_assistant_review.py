import json,os,tempfile,unittest
from unittest.mock import patch
from engine import Engine
from document_review import save
from test_applications import MASTER

class AssistantReview(unittest.TestCase):
 def setUp(self):
  self.e=Engine(tempfile.mkdtemp());self.e.import_file('Master_Career_Resume_Fixture.txt',MASTER.encode())
  self.oid=self.e.add({'company':'Fixture','title':'CRM workflow setup','description':'GoHighLevel pipelines and testing','source':'Contra','workspace':'contra'})['id']
  self.pkg=self.e.create_package({'id':self.oid})
 def test_revision_preserves_originals_and_revokes_draft_approval(self):
  did=self.pkg['files']['resume_pdf'];original=self.e.document_preview(did);draft=self.e.draft(self.pkg['draft_id'])
  with self.e.connect() as c:c.execute('UPDATE drafts SET status="Approved" WHERE id=?',(draft['id'],))
  revised=save(self.e,{'document_id':did,'text':original['text']+'\nReviewed clarification.','reviewed':True})
  self.assertNotEqual(revised['document_id'],did);self.assertEqual(self.e.document_preview(did),original)
  current=self.e.draft(draft['id']);self.assertEqual(current['status'],'Draft');self.assertIn(revised['document_id'],json.loads(current['attachments']));self.assertNotIn(did,json.loads(current['attachments']))
  with self.assertRaises(ValueError):save(self.e,{'document_id':did,'text':original['text'],'reviewed':True})
 def test_document_revision_needs_review_and_prepared_artifact(self):
  with self.assertRaises(ValueError):save(self.e,{'document_id':self.pkg['files']['cover_pdf'],'text':'A complete revised cover letter.'})
  with self.assertRaises(ValueError):save(self.e,{'document_id':99999,'text':'A complete revised cover letter.','reviewed':True})
 def test_bridge_review_dedup_scoping_and_backup(self):
  d={'workspace':'contra','opportunity_id':self.oid,'text':'Add a clearer document revision button.'}
  with self.assertRaises(ValueError):self.e.queue_developer_request(d)
  r=self.e.queue_developer_request({**d,'reviewed':True});self.assertTrue(self.e.queue_developer_request({**d,'reviewed':True})['duplicate'])
  with self.assertRaises(ValueError):self.e.queue_developer_request({**d,'workspace':'assistant','reviewed':True})
  self.e.update_developer_request({'id':r['id'],'status':'In developer inbox','repo_commit':'1234567'})
  restored=Engine(tempfile.mkdtemp());restored.restore(self.e.backup());self.assertEqual(restored.developer_requests()[0]['id'],r['id'])
  self.assertEqual(restored.developer_requests()[0]['status'],'In developer inbox')
 def test_chat_uses_shared_memory_and_rejects_cross_opportunity_document(self):
  other=self.e.add({'company':'Other','title':'Other CRM','description':'CRM','source':'Contra'})['id']
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch('engine.fetch_json',return_value={'choices':[{'message':{'content':'A grounded answer.'}}]}) as req:
   self.e.ask_workspace({'workspace':'contra','opportunity_id':self.oid,'text':'What do we know?'})
   payload=json.loads(req.call_args.args[1]['messages'][1]['content']);self.assertEqual(payload['shared_project_knowledge']['owner'],'Desmond Glover')
   with self.assertRaises(ValueError):self.e.ask_workspace({'workspace':'contra','opportunity_id':other,'document_id':self.pkg['files']['resume_pdf'],'text':'Revise this.'})
   self.assertEqual(req.call_count,1)
 def test_obvious_credentials_are_not_exported(self):
  with self.assertRaises(ValueError):self.e.queue_developer_request({'workspace':'assistant','text':'Here is hf_'+'x'*30,'reviewed':True})
 def test_remembered_instructions_stay_scoped_and_survive_restore(self):
  self.e.conversation_memory({'workspace':'contra','opportunity_id':self.oid,'text':'Ask about weekly workload before quoting.'})
  self.assertEqual(self.e.conversation({'workspace':'assistant'})['memory'],[])
  restored=Engine(tempfile.mkdtemp());restored.restore(self.e.backup());notes=restored.conversation({'workspace':'contra','opportunity_id':self.oid})['memory']
  self.assertEqual(notes[0]['text'],'Ask about weekly workload before quoting.')
