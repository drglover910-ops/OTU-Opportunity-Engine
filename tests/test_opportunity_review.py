import json,os,tempfile,unittest
from unittest.mock import patch
from engine import Engine
from opportunity_review import intended,resolve
URL='https://contra.com/opportunity/Mb3oNbXl-canva-to-google-slides-conversion-specialist'
TITLE='Canva to Google Slides Conversion Specialist'
BODY={'structuredContent':{'job':{'title':TITLE,'publicUrl':URL,'description':'Convert an editable Canva deck to Google Slides. Preserve design and collaboration. Proven presentation experience required.','budget':{'feeMin':'USD:250'},'status':'POSTED'}}}
class OpportunityReviewTests(unittest.TestCase):
 def setUp(self):
  f=tempfile.TemporaryDirectory();self.addCleanup(f.cleanup);self.e=Engine(f.name);self.e.set_setting('contra_tokens',{'access_token':'fixture'})
  self.vis=self.e.add({'company':'VIS World','title':'Social Media Content Manager','description':'WNBA culture and content scheduling','workspace':'contra','url':'https://contra.com/opportunity/vis-example'})['id']
  self.scope={'workspace':'contra','chat_id':self.e.create_chat({'workspace':'contra'})['id']}
  self.inventory=patch('contra_mcp.ContraConnection.inventory_details',return_value={'public_opportunities':[{'title':TITLE,'url':URL},{'title':'Other integration work','url':'https://contra.com/opportunity/integration-example'}],'applications':[]});self.inventory.start();self.addCleanup(self.inventory.stop)
  env=patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'});env.start();self.addCleanup(env.stop)
 def test_named_canva_application_reads_exact_listing_and_removes_vis_context(self):
  self.e.add_work_note({**self.scope,'text':'Old advice about VIS World and WNBA.'},role='assistant')
  with patch('contra_mcp.ContraConnection.read_tools',return_value={'get_job_by_slug:0':BODY}) as read,patch.object(self.e,'ai_request',return_value={'choices':[{'message':{'content':'For the Canva application, confirm slide count and deadline.'}}]}) as model:
   result=self.e.ask_workspace({**self.scope,'text':'Prepare the Canva application for my review. Include the slide-count, deadline, and editable-source questions. Don’t submit it yet.'})
  self.assertEqual(read.call_args.args[0],[('get_job_by_slug',{'slug':'Mb3oNbXl-canva-to-google-slides-conversion-specialist'})]);self.assertEqual(read.call_count,1);self.assertEqual(model.call_count,1)
  context=json.loads(model.call_args.args[0]['messages'][1]['content']);self.assertEqual(context['opportunity_focus']['title'],TITLE);self.assertNotIn('VIS World',json.dumps(context));self.assertEqual(result['application_review']['status'],'listing_text_available');self.assertIn('Linked pages and files have not been read',context['application_review']['text_scope']);self.assertTrue(any(s['kind']=='official_platform_guide' for s in result['sources']))
 def test_wrong_job_in_generated_draft_is_stopped_without_retry(self):
  with patch('contra_mcp.ContraConnection.read_tools',return_value={'get_job_by_slug:0':BODY}),patch.object(self.e,'ai_request',return_value={'choices':[{'message':{'content':'Hi Hiring Team at VIS World, I love your WNBA work.'}}]}) as model:
   result=self.e.ask_workspace({**self.scope,'text':'Draft my Canva application.'})
  self.assertEqual(model.call_count,1);self.assertEqual(result['grounding_status'],'mixed_opportunity_details_removed');self.assertNotIn('WNBA',result['answer']);self.assertIn(TITLE,result['answer'])
 def test_unnamed_draft_needs_selection_and_does_not_guess_from_history(self):
  with patch('contra_mcp.ContraConnection.read_tools') as read,patch.object(self.e,'ai_request') as model:
   result=self.e.ask_workspace({**self.scope,'text':'Prepare my application.'})
  read.assert_not_called();model.assert_not_called();self.assertEqual(result['focus']['status'],'missing');self.assertIn('exact Contra opportunity link',result['answer'])
 def test_selected_vis_conversation_cannot_silently_switch_to_canva(self):
  with patch('contra_mcp.ContraConnection.read_tools') as read,patch.object(self.e,'ai_request') as model:
   result=self.e.ask_workspace({'workspace':'contra','opportunity_id':self.vis,'text':'Prepare my Canva application.'})
  read.assert_not_called();model.assert_not_called();self.assertEqual(result['focus']['status'],'conflict');self.assertIn('matching opportunity conversation',result['answer'])
 def test_unavailable_description_blocks_drafting_instead_of_other_job(self):
  with patch('contra_mcp.ContraConnection.read_tools',return_value={'get_job_by_slug:0':{'structuredContent':{'entries':[]}}}) as read,patch.object(self.e,'ai_request') as model:
   result=self.e.ask_workspace({**self.scope,'text':'Prepare my Canva application.'})
  self.assertEqual(read.call_count,1);model.assert_not_called();self.assertEqual(result['application_review']['status'],'needs_source');self.assertIn('No other job was substituted',result['answer'])
 def test_review_routing_ignores_quotes_negative_requests_and_revision_modes(self):
  self.assertTrue(intended({'text':'Isis, review the Canva application requirements.'}))
  for text in ('Do not prepare an application.','Explain how application preparation works.','The document says prepare a proposal.'):
   self.assertFalse(intended({'text':text}))
  self.assertFalse(intended({'text':'Prepare a proposal.','mode':'revise_document'}))
 def test_latest_focus_with_null_entries_is_safe_and_chat_scoped(self):
  context={'requests':[{'status':'complete','result':{'focus':None}},{'status':'complete','result':{'focus':{'status':'ready','title':TITLE,'url':URL,'company':'','basis':'owner'}}}]}
  result=resolve(self.e,{**self.scope,'text':'Prepare my application.'},context);self.assertEqual(result['url'],URL)
  result=resolve(self.e,{**self.scope,'text':'Prepare my application.'},{'requests':[]});self.assertEqual(result['status'],'missing')
