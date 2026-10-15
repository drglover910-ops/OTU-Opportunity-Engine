import io,json,os,runpy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'scripts/sync_assistant_bridge.py'
class BridgeSync(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,{'HF_TOKEN':'fixture-hf','GITHUB_TOKEN':'fixture-github'});self.env.start();self.addCleanup(self.env.stop)
 def load(self):
  with patch.dict(os.environ,{'HF_TOKEN':'fixture-hf','GITHUB_TOKEN':'fixture-github'}):return runpy.run_path(str(SCRIPT),run_name='fixture_bridge')
 def test_public_repository_is_rejected_before_any_app_read(self):
  module=self.load()
  with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"private":false}')) as request,patch('sys.argv',['sync']):
   with self.assertRaises(ValueError):module['main']()
  self.assertEqual(request.call_count,1);self.assertEqual(request.call_args.args[0].get_header('Authorization'),'Bearer fixture-github')
 def test_only_reviewed_request_fields_are_transferred(self):
  module=self.load();root=tempfile.mkdtemp();row={'id':'a'*24,'workspace':'contra','opportunity_id':7,'text':'A reviewed change request','created':'2026-10-15','status':'Queued for repository sync','reply':'Private reply not auto-exported','repo_commit':''}
  requests=[]
  def response(req,**kwargs):
   requests.append(req)
   return io.BytesIO(json.dumps({'private':True} if 'api.github.com' in req.full_url else [row]).encode())
  before=os.getcwd()
  try:
   os.chdir(root)
   with patch('urllib.request.urlopen',side_effect=response),patch('subprocess.check_output',return_value='1234567'),patch('sys.argv',['sync']):module['main']()
   saved=json.loads(Path('docs/assistant_bridge/requests.json').read_text())[0]
   self.assertEqual(set(saved),{'id','workspace','opportunity_id','text','created'});self.assertEqual(saved['text'],row['text'])
   self.assertEqual(requests[1].get_header('Authorization'),'Bearer fixture-hf')
  finally:os.chdir(before)
