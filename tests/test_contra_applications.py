import json,tempfile,time,unittest
from unittest.mock import patch
from engine import Engine
from contra_applications import ContraApplications
from attachment_store import AttachmentStore
from workspace_ops import WorkspaceOps
from backup_store import Backups
URL='https://contra.com/opportunity/canva-native-fixture'
DRAFT='c257a0bd-bd72-4eb4-a40a-d569f56cd50d'
def job(applied=False):
 return {'structuredContent':{'ok':True,'job':{'title':'Canva to Google Slides Conversion Specialist','publicUrl':URL,'description':'Canva and Google Slides experience required.','status':'POSTED','jobPosting':{'jobPostingId':'posting-fixture'},'organization':{'name':'Example client'},'viewerApplication':{'appliedAt':'2026-10-18T00:00:00Z'} if applied else None}}}
PORT={'structuredContent':{'projects':[{'id':'project-fixture','title':'Actual presentation sample','description':'Canva and Slides','projectUrl':'https://contra.com/p/sample','isDraft':False}]}}
def read(calls):return {name+':'+str(i):PORT if name=='list_portfolio_projects' else job() for i,(name,args) in enumerate(calls)}
def prepared(calls):return {'apply_to_job_prepare:0':{'structuredContent':{'ok':True,'draftId':DRAFT,'preview':{'job':'Canva to Google Slides Conversion Specialist','message':calls[0][1]['message']}}}}
class NativeApplications(unittest.TestCase):
 def setUp(self):
  f=tempfile.TemporaryDirectory();self.addCleanup(f.cleanup);self.e=Engine(f.name);self.service=ContraApplications(self.e);self.scope={'workspace':'contra','chat_id':self.e.create_chat({'workspace':'contra'})['id']}
 def options(self):
  with patch('contra_mcp.ContraConnection.read_tools',side_effect=read):return self.service.options({**self.scope,'url':URL})
 def ready(self,**extra):
  a=self.options();d={**self.scope,'id':a['id'],'message':a['message'],'fit_reviewed':True,'project_ids':['project-fixture'],**extra}
  with patch('contra_mcp.ContraConnection.application_tools',side_effect=prepared):a=self.service.prepare(d)
  return a,d
 def test_options_read_only_and_does_not_infer_portfolio_fit(self):
  with patch('contra_mcp.ContraConnection.application_tools') as writes,patch.object(self.e,'ai_request') as ai:a=self.options()
  writes.assert_not_called();ai.assert_not_called();self.assertEqual(a['status'],'Options ready');self.assertEqual(a['projects'][0]['id'],'project-fixture');self.assertIn('unrelated CRM',a['fit_warning'])
 def test_portfolio_default_explicit_opt_out_and_fit_gate(self):
  a=self.options();d={**self.scope,'id':a['id'],'message':a['message'],'fit_reviewed':True,'project_ids':[]}
  with patch('contra_mcp.ContraConnection.application_tools',side_effect=prepared) as tool:
   with self.assertRaises(ValueError):self.service.prepare(d)
   with self.assertRaises(ValueError):self.service.prepare({**d,'project_ids':['foreign-project']})
   with self.assertRaises(ValueError):self.service.prepare({**d,'portfolio_opt_out':True,'fit_reviewed':False})
   tool.assert_not_called();r=self.service.prepare({**d,'portfolio_opt_out':True})
  self.assertEqual(tool.call_count,1);args=tool.call_args.args[0][0][1];self.assertTrue(args['portfolioAttachmentOptOutConfirmed']);self.assertNotIn('relatedPortfolioProjectIds',args);self.assertEqual(r['status'],'Preview ready')
 def test_preview_is_immutable_and_idempotent_and_reopens(self):
  a,d=self.ready()
  with patch('contra_mcp.ContraConnection.application_tools') as tool,patch('contra_mcp.ContraConnection.read_tools') as reads:
   self.assertEqual(self.service.prepare(d)['preview_digest'],a['preview_digest']);self.assertEqual(self.service.options({**self.scope,'url':URL})['id'],a['id'])
   with self.assertRaises(ValueError):self.service.prepare({**d,'message':'Changed message'})
   tool.assert_not_called();reads.assert_not_called()
 def test_submission_requires_exact_approval_and_verifies_application_afterward(self):
  a,d=self.ready();submit={**self.scope,'id':a['id'],'preview_digest':a['preview_digest'],'approved':True}
  with patch('contra_mcp.ContraConnection.application_tools',return_value={'apply_to_job_confirm:0':{'structuredContent':{'ok':True}}}) as tool,patch('contra_mcp.ContraConnection.read_tools',side_effect=[{'get_job_by_slug:0':job()},{'get_job_by_slug:0':job(True)}]) as reads:
   with self.assertRaises(ValueError):self.service.submit({**submit,'approved':False})
   with self.assertRaises(ValueError):self.service.submit({**submit,'preview_digest':'changed'})
   tool.assert_not_called();r=self.service.submit(submit);self.assertEqual(r['status'],'Submitted');self.assertEqual(tool.call_count,1);self.assertEqual(reads.call_count,2);self.assertEqual(tool.call_args.args[0],[('apply_to_job_confirm',{'draftId':DRAFT,'confirm':True})]);self.service.submit(submit);self.assertEqual(tool.call_count,1)
  self.assertEqual(self.e.conversation(self.scope)['application_receipts'][0]['status'],'Submitted')
 def test_ambiguous_send_is_not_retried_even_after_restart(self):
  a,d=self.ready()
  with patch('contra_mcp.ContraConnection.application_tools',side_effect=ValueError('lost reply')) as tool,patch('contra_mcp.ContraConnection.read_tools',side_effect=read):
   with self.assertRaises(ValueError):self.service.submit({**self.scope,'id':a['id'],'approved':True,'preview_digest':a['preview_digest']})
   self.assertEqual(self.service.record({**self.scope,'id':a['id']})['status'],'Submission uncertain');service=ContraApplications(self.e)
   with self.assertRaises(ValueError):service.submit({**self.scope,'id':a['id'],'approved':True,'preview_digest':a['preview_digest']})
   self.assertEqual(tool.call_count,1)
 def test_ok_without_recorded_application_is_uncertain(self):
  a,d=self.ready()
  with patch('contra_mcp.ContraConnection.application_tools',return_value={'confirm:0':{'structuredContent':{'ok':True}}}),patch('contra_mcp.ContraConnection.read_tools',side_effect=read):
   with self.assertRaises(ValueError):self.service.submit({**self.scope,'id':a['id'],'approved':True,'preview_digest':a['preview_digest']})
  self.assertEqual(self.service.record({**self.scope,'id':a['id']})['status'],'Submission uncertain')
 def test_existing_application_blocks_confirmation_before_write(self):
  a,d=self.ready()
  with patch('contra_mcp.ContraConnection.application_tools') as tool,patch('contra_mcp.ContraConnection.read_tools',return_value={'job:0':job(True)}):
   with self.assertRaises(ValueError):self.service.submit({**self.scope,'id':a['id'],'approved':True,'preview_digest':a['preview_digest']})
   tool.assert_not_called()
 def test_preview_expiration_and_cross_chat_scope_block_actions(self):
  a,d=self.ready();other={**self.scope,'chat_id':self.e.create_chat({'workspace':'contra'})['id']}
  with self.assertRaises(ValueError):self.service.record({**other,'id':a['id']})
  r=self.service.record({**self.scope,'id':a['id']});r['data']['expires']=time.time()-1;self.service.save(r,'Preview ready')
  with patch('contra_mcp.ContraConnection.application_tools') as tool:
   with self.assertRaises(ValueError):self.service.submit({**self.scope,'id':a['id'],'approved':True,'preview_digest':a['preview_digest']})
   tool.assert_not_called()
 def test_lost_prepare_never_retries_and_edit_retires_preview(self):
  a=self.options();d={**self.scope,'id':a['id'],'message':a['message'],'fit_reviewed':True,'project_ids':['project-fixture']}
  with patch('contra_mcp.ContraConnection.application_tools',side_effect=ValueError('lost preparation')) as tool:
   for _ in range(2):
    with self.assertRaises(ValueError):self.service.prepare(d)
   self.assertEqual(tool.call_count,1)
  self.assertEqual(self.service.record(d)['status'],'Prepare uncertain')
 def test_complete_backup_preserves_preview_but_cannot_replay_submission(self):
  a,d=self.ready();AttachmentStore(self.e);WorkspaceOps(self.e);archive=Backups(self.e).export()
  f=tempfile.TemporaryDirectory();self.addCleanup(f.cleanup);target=Engine(f.name);AttachmentStore(target);WorkspaceOps(target);Backups(target).restore(archive)
  restored=ContraApplications(target).record({**self.scope,'id':a['id']});self.assertEqual(restored['status'],'Restored');self.assertEqual(restored['remote_draft_id'],'');self.assertNotIn('preview_digest',restored['data']);self.assertTrue(restored['data']['preview'])
 def test_read_only_inspection_creates_no_ticket_or_native_draft(self):
  with patch('contra_mcp.ContraConnection.read_tools',side_effect=read),patch('contra_mcp.ContraConnection.application_tools') as writes:
   result=self.service.options({**self.scope,'url':URL,'inspect_only':True})
  writes.assert_not_called();self.assertEqual(result['status'],'Inspection only')
  with self.e.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM contra_application_actions').fetchone()[0],0)
 def test_read_allowlist_and_application_allowlist_are_separate(self):
  from contra_mcp import ContraConnection
  connection=ContraConnection(self.e)
  with patch.object(connection,'_tools') as dispatch:
   with self.assertRaises(ValueError):connection.read_tools([('apply_to_job_prepare',{})])
   with self.assertRaises(ValueError):connection.application_tools([('send_chat_message_confirm',{})])
   with self.assertRaises(ValueError):connection.application_tools([('apply_to_job_prepare',{}),('apply_to_job_confirm',{})])
   dispatch.assert_not_called()
 def test_retiring_preview_prevents_old_approval_replay(self):
  a,d=self.ready();self.service.discard({**self.scope,'id':a['id']})
  with patch('contra_mcp.ContraConnection.application_tools') as writes:
   with self.assertRaises(ValueError):self.service.submit({**self.scope,'id':a['id'],'approved':True,'preview_digest':a['preview_digest']})
   writes.assert_not_called()
