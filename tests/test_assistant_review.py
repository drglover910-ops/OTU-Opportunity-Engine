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

 def test_proposal_revision_sees_selected_draft_without_changing_it(self):
  draft=self.e.draft(self.pkg['draft_id']);original=draft['body']
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch('engine.fetch_json',return_value={'choices':[{'message':{'content':'Hello, a reviewed proposal suggestion.'}}]}) as req:
   result=self.e.ask_workspace({'workspace':'contra','opportunity_id':self.oid,'draft_id':draft['id'],'mode':'revise_proposal','text':'Make it more concise.'})
   payload=json.loads(req.call_args.args[1]['messages'][1]['content']);self.assertEqual(payload['prepared_proposals'][0]['body'],original)
  self.assertEqual(result['draft_id'],draft['id']);self.assertEqual(self.e.draft(draft['id'])['body'],original)

 def test_reconciled_status_and_personality_are_available_without_cross_case_context(self):
  knowledge=self.e.chat_knowledge({'workspace':'assistant'})
  statuses={r['name']:r['status'] for r in knowledge['status_report']['opportunities']}
  self.assertIn('Applied',statuses['GeekyAnts sponsorship']);self.assertIn('not sent',statuses['Podcast Outreach / Tarot Times With Heidi'])
  self.assertIn('friendly',knowledge['personality']['voice'])
  scoped=self.e.chat_knowledge({'workspace':'contra','opportunity_id':self.oid})
  self.assertEqual(scoped['status_report']['opportunities'],[])
  compact=self.e.chat_knowledge({'workspace':'contra','opportunity_id':self.oid,'mode':'revise_document'})
  self.assertLess(len(json.dumps(compact)),2200);self.assertIn('career_rules',compact)

 def test_actual_waiting_response_is_corrected_without_another_model_call(self):
  answer='Since you’ve already drafted a thoughtful reply asking for slide count, deadline, and editable Canva access, wait for their response on those three scope details. No action required until they clarify.'
  draft=self.e.draft(self.pkg['draft_id'])
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch.object(self.e,'ai_request',return_value={'choices':[{'message':{'content':answer}}]}) as model:
   result=self.e.ask_workspace({'workspace':'contra','opportunity_id':self.oid,'text':'What is next?'})
  self.assertEqual(model.call_count,1);self.assertEqual(result['grounding_status'],'unsupported_delivery_assumption_removed');self.assertIn('finish and review the application',result['answer']);self.assertNotIn('wait for their response',result['answer']);self.assertEqual(self.e.draft(draft['id']),draft)
  context=json.loads(model.call_args.args[0]['messages'][1]['content']);self.assertEqual(context['outreach_state']['delivery'],'not_confirmed')
 def test_approved_draft_stage_and_ai_notes_are_not_delivery_evidence(self):
  with self.e.connect() as c:
   c.execute('UPDATE drafts SET status="Approved" WHERE id=?',(self.pkg['draft_id'],));c.execute('UPDATE opportunities SET stage="Contacted" WHERE id=?',(self.oid,))
  self.e.add_work_note({'workspace':'contra','opportunity_id':self.oid,'text':'The message was sent.'},role='assistant')
  d={'workspace':'contra','opportunity_id':self.oid,'text':'What next?'}
  self.assertEqual(self.e.chat_outreach_state(d,self.e.conversation(d))['delivery'],'not_confirmed')
 def test_real_delivery_is_scoped_and_unknown_delivery_needs_checking(self):
  with self.e.connect() as c:c.execute('UPDATE drafts SET status="Sent",message_id="fixture-sent" WHERE id=?',(self.pkg['draft_id'],))
  d={'workspace':'contra','opportunity_id':self.oid,'text':'What next?'}
  state=self.e.chat_outreach_state(d,self.e.conversation(d));self.assertEqual(state['delivery'],'confirmed_outbound');self.assertFalse(self.e.ungrounded_wait('Wait for their response.',state,'advice'))
  d={'workspace':'contra','text':'What next?'};self.assertEqual(self.e.chat_outreach_state(d,self.e.conversation(d))['delivery'],'not_confirmed')
  with self.e.connect() as c:c.execute('UPDATE drafts SET status="Delivery unknown" WHERE id=?',(self.pkg['draft_id'],))
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch.object(self.e,'ai_request',return_value={'choices':[{'message':{'content':'Wait for their response.'}}]}):
   result=self.e.ask_workspace({'workspace':'contra','opportunity_id':self.oid,'text':'What next?'})
  self.assertIn('before sending again',result['answer']);self.assertEqual(result['outreach_state']['delivery'],'uncertain')
 def test_direct_owner_statement_and_client_facing_rewrite_are_distinct(self):
  for statement in ('I submitted this application. What next?', 'I’ve already sent the message. What next?'):
   d={'workspace':'contra','opportunity_id':self.oid,'text':statement};state=self.e.chat_outreach_state(d,self.e.conversation(d));self.assertEqual(state['delivery'],'owner_reported_outbound');self.assertFalse(self.e.ungrounded_wait('Wait for their response.',state,'advice'))
  self.assertFalse(self.e.ungrounded_wait('Wait for their response.',{'delivery':'not_confirmed'},'revise_proposal'))
 def test_contra_application_evidence_must_match_selected_url(self):
  with self.e.connect() as c:c.execute('UPDATE opportunities SET url=? WHERE id=?',('https://contra.com/opportunity/current-fixture',self.oid))
  d={'workspace':'contra','opportunity_id':self.oid,'text':'Next?'}
  with patch('contra_mcp.ContraConnection.inventory_details',return_value={'applications':[{'url':'https://contra.com/opportunity/other','applied':True}]}):
   self.assertFalse(self.e.chat_outreach_state(d,self.e.conversation(d))['contra_application_recorded'])
  with patch('contra_mcp.ContraConnection.inventory_details',return_value={'applications':[{'url':'https://contra.com/opportunity/current-fixture','applied':True}]}):
   self.assertTrue(self.e.chat_outreach_state(d,self.e.conversation(d))['contra_application_recorded'])
