import io,json,os,tempfile,time,unittest,urllib.parse,zipfile
from unittest.mock import patch
from engine import Engine
from contra_mcp import ContraConnection,REGISTER,AUTH,TOKEN,RESOURCE
class ContraOAuth(unittest.TestCase):
 def setUp(self):
  self.e=Engine(tempfile.mkdtemp());self.c=ContraConnection(self.e)
  self.env=patch.dict(os.environ,{'PUBLIC_URL':'https://example.hf.space'});self.env.start();self.addCleanup(self.env.stop)
 def prepared(self):self.e.set_setting('contra_oauth_client',{'client_id':'fixture-client','redirect_uri':'https://example.hf.space/oauth/contra/callback'})
 def test_public_registration_is_reused(self):
  with patch('contra_mcp.request',return_value=({'client_id':'fixture-client','token_endpoint_auth_method':'none'},{})) as req:
   self.c.prepare();self.c.prepare()
  self.assertEqual(req.call_count,1);self.assertEqual(req.call_args.args[0],REGISTER)
  self.assertEqual(req.call_args.args[1]['redirect_uris'],['https://example.hf.space/oauth/contra/callback'])
 def test_pkce_and_one_time_state(self):
  self.prepared();url=self.c.authorize();query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
  self.assertTrue(url.startswith(AUTH));self.assertEqual(query['code_challenge_method'],['S256'])
  self.assertNotIn('code_verifier',query);state=query['state'][0]
  with patch('contra_mcp.request',return_value=({'access_token':'fixture-access','refresh_token':'fixture-refresh','expires_in':3600},{})) as req:
   with self.assertRaises(ValueError):self.c.callback('wrong-state','code')
   req.assert_not_called();self.c.callback(state,'code')
   self.assertEqual(req.call_args.args[0],TOKEN);self.assertTrue(req.call_args.args[1]['code_verifier'])
   with self.assertRaises(ValueError):self.c.callback(state,'code')
  self.assertEqual(self.c.token(),'fixture-access')
 def test_expired_state_is_rejected(self):
  self.e.set_setting('contra_oauth_states',{'expired':{'expires':time.time()-1,'verifier':'fixture'}})
  with patch('contra_mcp.request') as req:
   with self.assertRaises(ValueError):self.c.callback('expired','code')
  req.assert_not_called()
 def test_refresh_keeps_refresh_token_if_not_replaced(self):
  self.prepared();self.e.set_setting('contra_tokens',{'access_token':'old','refresh_token':'retained','expires_at':0})
  with patch('contra_mcp.request',return_value=({'access_token':'new','expires_in':3600},{})):self.assertEqual(self.c.token(),'new')
  self.assertEqual(self.e.setting('contra_tokens')['refresh_token'],'retained')
 def test_discovery_never_invokes_account_tools(self):
  self.e.set_setting('contra_tokens',{'access_token':'fixture','expires_at':time.time()+300})
  replies=[({'result':{'protocolVersion':'2025-03-26'}},{'Mcp-Session-Id':'fixture-session'}),({},{}),({'result':{'tools':[{'name':'example_read_tool'},{'name':'example_send_tool'}]}},{})]
  with patch('contra_mcp.request',side_effect=replies) as req:result=self.c.discover()
  self.assertEqual(result['tools'],2);methods=[c.args[1]['method'] for c in req.call_args_list]
  self.assertEqual(methods,['initialize','notifications/initialized','tools/list'])
  self.assertTrue(all(c.args[0]==RESOURCE for c in req.call_args_list));self.assertEqual(req.call_args_list[-1].kwargs['headers']['Mcp-Session-Id'],'fixture-session')
 def test_credentials_excluded_from_backup_and_disconnect_can_reconnect(self):
  self.prepared();self.e.set_setting('contra_tokens',{'access_token':'DO_NOT_EXPORT_CONTRA_TOKEN'})
  with zipfile.ZipFile(io.BytesIO(self.e.backup())) as z:self.assertNotIn('DO_NOT_EXPORT_CONTRA_TOKEN',z.read('records.json').decode())
  self.c.disconnect()
  with patch('contra_mcp.request',return_value=({'client_id':'new-client'},{})):self.assertTrue(self.c.authorize().startswith(AUTH))
 def test_read_tool_allowlist_rejects_writes_before_network(self):
  with patch('contra_mcp.request') as req:
   with self.assertRaises(ValueError):self.c.read_tools([('send_chat_message_confirm',{'confirm':True})])
   req.assert_not_called()
 def test_sync_uses_only_allowlisted_reads_and_reuses_cache(self):
  with patch.object(self.c,'read_tools',return_value={'fixture':{'content':[]}}) as req:
   first=self.c.sync();second=self.c.sync()
  self.assertEqual(req.call_count,1);self.assertTrue(second['cached'])
  self.assertEqual(first['read_checks'],1)
  self.assertIn(('list_job_feed',{'preset':'APPLIED','first':100}),req.call_args.args[0])
 def test_private_snapshot_extracts_public_jobs_and_challenges(self):
  self.e.set_setting('contra_account_snapshot',{
   'list_job_feed:4':{'structuredContent':{'ok':True,'entries':[{'job':{'title':'CRM build','publicUrl':'https://contra.com/opportunity/abc','budget':{'feeMin':300,'feeMax':500,'type':'FIXED'}}}]}},
   'list_active_challenges:6':{'content':[{'type':'text','text':json.dumps({'ok':True,'challenges':[{'title':'Build challenge','challengeUrl':'https://contra.com/community/test','prize':{'formatted':'$100'},'submissionsDeadline':'2026-10-20'}]})}]},
   'detail_get_job_by_slug:0':{'structuredContent':{'job':{'title':'CRM build','publicUrl':'https://contra.com/opportunity/abc','description':'A full verified source description'}}}})
  data=self.c.inventory_details();self.assertEqual(len(data['public_opportunities']),2)
  jobs={x['title']:x for x in data['public_opportunities']}
  self.assertEqual(jobs['CRM build']['description'],'A full verified source description')
  self.assertEqual(jobs['Build challenge']['kind'],'Challenge / prize')
  self.assertFalse(jobs['CRM build']['requirements_verified'])
