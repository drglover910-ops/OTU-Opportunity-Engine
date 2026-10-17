import base64,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from engine import Engine
from attachment_store import AttachmentStore
from backup_store import Backups
from workspace_ops import WorkspaceOps
from scripts.evaluate_otu import run_suite

class KnowledgeTests(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup);self.e=Engine(self.folder.name);self.a=AttachmentStore(self.e)
  r=self.e.create_chat({'workspace':'contra','title':'Example planning'});self.scope={'workspace':'contra','chat_id':r['id']}
 def upload(self,name,text):
  raw=text.encode();r=self.a.start({**self.scope,'name':name,'size':len(raw)});self.a.chunk({'id':r['id'],'offset':0,'content':base64.b64encode(raw).decode()});return self.a.finish({'id':r['id']})
 def test_offline_task_baseline(self):
  results=run_suite();self.assertEqual(len(results),28);self.assertEqual([r for r in results if not r['passed']],[])
 def test_file_requires_review_scoping_and_supported_text(self):
  f=self.upload('Brief.txt','Example deliverables: two workflows.')
  with self.assertRaises(ValueError):self.e.knowledge.enable_file({**self.scope,'id':f['id']})
  other=self.e.create_chat({'workspace':'contra'})
  with self.assertRaises(ValueError):self.e.knowledge.enable_file({**self.scope,'chat_id':other['id'],'id':f['id'],'confirmed':True})
  with patch('engine.fetch_json') as provider:
   self.e.knowledge.enable_file({**self.scope,'id':f['id'],'confirmed':True})
   provider.assert_not_called()
  self.assertTrue(self.a.listing(self.scope)[0]['readable_by_isis'])
  self.assertIn('two workflows',json.dumps(self.e.knowledge.search({**self.scope,'text':'Summarize this file.'})))
  self.e.knowledge.enable_file({**self.scope,'id':f['id'],'enabled':False})
  self.assertFalse(self.a.listing(self.scope)[0]['readable_by_isis'])
  self.assertTrue((self.a.root/f['id']).is_file())
  pdf=self.upload('Brief.pdf','Saved document; no chat extraction.')
  with self.assertRaises(ValueError):self.e.knowledge.enable_file({**self.scope,'id':pdf['id'],'confirmed':True})
 def test_file_rejects_credentials_binary_damage_and_large_text(self):
  for name,text in [('Private.txt','api_key=hf_'+'x'*30),('Binary.txt','\x00Bad text'),('Huge.txt','x'*50001)]:
   f=self.upload(name,text)
   with self.assertRaises(ValueError):self.e.knowledge.enable_file({**self.scope,'id':f['id'],'confirmed':True})
  f=self.upload('Changed.txt','Original checklist');(self.a.root/f['id']).write_text('Changed checklist')
  with self.assertRaises(ValueError):self.e.knowledge.enable_file({**self.scope,'id':f['id'],'confirmed':True})
 def test_file_removal_removes_retrieval_copy(self):
  f=self.upload('Brief.md','Example campaign requirements.');self.e.knowledge.enable_file({**self.scope,'id':f['id'],'confirmed':True});self.a.remove({'id':f['id'],'confirmed':True})
  self.assertEqual(self.e.knowledge.search({**self.scope,'text':'campaign requirements'}),[])
  with self.e.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM file_knowledge').fetchone()[0],0)
 def test_references_are_supplied_and_persisted_without_extra_model_calls(self):
  self.e.add_work_note({**self.scope,'text':'Our reviewed project rate is $75 per hour.'},role='user')
  for i in range(8):self.e.add_work_note({**self.scope,'text':'Unrelated scheduling '+str(i)},role='user')
  response={'choices':[{'message':{'content':'You recorded $75 per hour [S1].'}}],'usage':{'total_tokens':100}}
  with patch.dict(os.environ,{'HF_INFERENCE_TOKEN':'fixture'}),patch('engine.fetch_json',return_value=response) as p:
   result=self.e.ask_workspace({**self.scope,'text':'What project rate did we discuss?'})
   payload=p.call_args.args[1];context=json.loads(payload['messages'][1]['content'])
   self.assertIn('$75',json.dumps(context['retrieved_sources']));self.assertEqual(p.call_count,1)
   self.assertLessEqual(len(json.dumps(payload['messages'],ensure_ascii=False).encode()),24000)
  note=self.e.conversation(self.scope)['notes'][-1];self.assertEqual(note['sources'],result['sources']);self.assertEqual(note['text'],'You recorded $75 per hour [S1].')
  reopened=Engine(self.folder.name);self.assertEqual(reopened.conversation(self.scope)['notes'][-1]['sources'],result['sources'])
 def test_complete_backup_preserves_opt_in_and_source_receipts(self):
  WorkspaceOps(self.e);f=self.upload('Brief.txt','Orion requirements: two workflows.');self.e.knowledge.enable_file({**self.scope,'id':f['id'],'confirmed':True})
  with self.e.connect() as c:c.execute('INSERT INTO work_notes(workspace,text,created,role,chat_id,sources) VALUES(?,?,?,?,?,?)',('contra','A reply.','2026-10-17','assistant',self.scope['chat_id'],json.dumps(self.e.knowledge.search({**self.scope,'text':'Orion requirements'}))))
  path=Backups(self.e).export()
  with tempfile.TemporaryDirectory() as target:
   restored=Engine(target);AttachmentStore(restored);WorkspaceOps(restored);Backups(restored).restore(path)
   self.assertIn('two workflows',json.dumps(restored.knowledge.search({**self.scope,'text':'Orion requirements'})))
   self.assertTrue(restored.conversation(self.scope)['notes'][-1]['sources'])
 def test_old_sources_are_not_mutated_and_only_four_bounded_references(self):
  self.e.import_file('Master_Career_Resume_Fixture.txt',('EXAMPLE OWNER\nWorkflow configuration. '*400).encode());before=self.e.documents()
  for i in range(10):self.e.add_work_note({**self.scope,'text':'Workflow requirement '+str(i)},role='user')
  result=self.e.knowledge.search({**self.scope,'text':'Workflow configuration requirement'})
  self.assertLessEqual(len(result),4);self.assertLessEqual(len(json.dumps(result,ensure_ascii=False).encode()),4800);self.assertEqual(self.e.documents(),before)
