"""Contra OAuth with PKCE and MCP capability discovery. No account write-tool calls."""
import base64,hashlib,json,secrets,time,urllib.request,urllib.error,urllib.parse
BASE='https://contra.com'
RESOURCE=BASE+'/mcp'
AUTH=BASE+'/api/mcp/oauth/authorize'
TOKEN=BASE+'/api/mcp/oauth/token'
REGISTER=BASE+'/api/mcp/oauth/register'

def request(url,data=None,form=False,headers=None,allow_empty=False):
 payload=urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode() if data is not None else None
 req=urllib.request.Request(url,data=payload,headers={'Content-Type':'application/x-www-form-urlencoded' if form else 'application/json','Accept':'application/json, text/event-stream',**(headers or {})})
 try:
  with urllib.request.urlopen(req,timeout=35) as r:
   response_headers=dict(r.headers)
   if r.status in (202,204) or r.headers.get('Content-Length')=='0':return {},response_headers
   if 'text/event-stream' in r.headers.get('Content-Type',''):
    for line in r:
     if line.startswith(b'data:'):
      try:value=json.loads(line[5:])
      except ValueError:continue
      if 'result' in value or 'error' in value:return value,response_headers
    if allow_empty:return {},response_headers
    raise ValueError('Contra returned no protocol result. Please retry the connection check.')
   return json.load(r),response_headers
 except urllib.error.HTTPError as e:raise ValueError(f'Contra connection returned HTTP {e.code}. Check access before retrying.') from None
 except urllib.error.URLError:raise ValueError('Contra could not be reached. Try the connection check again later.') from None

class ContraConnection:
 def __init__(self,engine):self.engine=engine
 def prepare(self):
  public=__import__('os').getenv('PUBLIC_URL','').rstrip('/')
  p=urllib.parse.urlsplit(public)
  if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('The app needs its public HTTPS address before connecting Contra.')
  redirect=public+'/oauth/contra/callback';client=self.engine.setting('contra_oauth_client',{})
  if not client or client.get('redirect_uri')!=redirect:
   result,_=request(REGISTER,{'client_name':'OTU Opportunity Engine','client_uri':public,'redirect_uris':[redirect],'grant_types':['authorization_code','refresh_token'],'response_types':['code'],'token_endpoint_auth_method':'none','scope':'mcp:tools'})
   if not result.get('client_id') or result.get('token_endpoint_auth_method','none')!='none':raise ValueError('Contra registration did not return a supported public client. No account actions were taken.')
   client={'client_id':result['client_id'],'redirect_uri':redirect};self.engine.set_setting('contra_oauth_client',client)
  return {'ready':True,'message':'Contra sign-in is ready. You approve access on Contra’s own page.'}
 def authorize(self):
  self.prepare();client=self.engine.setting('contra_oauth_client');state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
  challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
  with self.engine.lock:
   states=self.engine.setting('contra_oauth_states',{}) or {};states={k:v for k,v in states.items() if v['expires']>time.time()};states[state]={'verifier':verifier,'expires':time.time()+600};self.engine.set_setting('contra_oauth_states',states)
  return AUTH+'?'+urllib.parse.urlencode({'client_id':client['client_id'],'redirect_uri':client['redirect_uri'],'response_type':'code','scope':'mcp:tools','state':state,'code_challenge':challenge,'code_challenge_method':'S256','resource':RESOURCE})
 def callback(self,state,code):
  with self.engine.lock:
   states=self.engine.setting('contra_oauth_states',{}) or {};pending=states.pop(state,None);self.engine.set_setting('contra_oauth_states',states)
  if not pending or pending['expires']<time.time() or not code:raise ValueError('This Contra sign-in expired or was not recognized. Start again from Connections.')
  client=self.engine.setting('contra_oauth_client');tokens,_=request(TOKEN,{'grant_type':'authorization_code','client_id':client['client_id'],'code':code,'redirect_uri':client['redirect_uri'],'code_verifier':pending['verifier'],'resource':RESOURCE},form=True)
  if not tokens.get('access_token'):raise ValueError('Contra did not return account access. Start again from Connections.')
  tokens['expires_at']=time.time()+int(tokens.get('expires_in',3600))-60;self.engine.set_setting('contra_tokens',tokens)
  return {'connected':True}
 def token(self):
  with self.engine.lock:
   tokens=self.engine.setting('contra_tokens',{})
   if not tokens or not tokens.get('access_token'):raise ValueError('Sign in with Contra first.')
   if tokens.get('expires_at',0)<time.time():
    if not tokens.get('refresh_token'):raise ValueError('Contra access expired. Reconnect from Connections.')
    client=self.engine.setting('contra_oauth_client');new,_=request(TOKEN,{'grant_type':'refresh_token','refresh_token':tokens['refresh_token'],'client_id':client['client_id'],'resource':RESOURCE},form=True)
    if not new.get('access_token'):raise ValueError('Contra access could not be renewed. Reconnect from Connections.')
    tokens.update(new);tokens['expires_at']=time.time()+int(new.get('expires_in',3600))-60;self.engine.set_setting('contra_tokens',tokens)
   return tokens['access_token']
 def discover(self):
  headers={'Authorization':'Bearer '+self.token()}
  result,response_headers=request(RESOURCE,{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'OTU Opportunity Engine','version':'0.8.0'}}},headers=headers)
  if result.get('error'):raise ValueError('Contra could not initialize the connection. No account tools were run.')
  protocol=result.get('result',{}).get('protocolVersion','2025-03-26');headers['MCP-Protocol-Version']=protocol
  session=next((v for k,v in response_headers.items() if k.lower()=='mcp-session-id'),None)
  if session:headers['Mcp-Session-Id']=session
  request(RESOURCE,{'jsonrpc':'2.0','method':'notifications/initialized'},headers=headers,allow_empty=True)
  tools=[];cursor=None
  for index in range(20):
   response,_=request(RESOURCE,{'jsonrpc':'2.0','id':index+2,'method':'tools/list','params':{'cursor':cursor} if cursor else {}},headers=headers)
   if response.get('error'):raise ValueError('Contra did not allow the tool list. Your account has not been changed.')
   body=response.get('result',{});tools.extend(body.get('tools',[]));cursor=body.get('nextCursor')
   if not cursor:break
  self.engine.set_setting('contra_tool_catalog',tools)
  summary={'connected':True,'checked_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'tools':len(tools),'history_access':'Co-Agent AI history is not assumed available.','actions':'Capability discovery only; no account tools called.'}
  self.engine.set_setting('contra_last_check',summary);return summary
 def disconnect(self):
  for key in ('contra_tokens','contra_oauth_client','contra_oauth_states','contra_tool_catalog','contra_last_check'):self.engine.set_setting(key,None)
  return {'disconnected':True,'message':'Stored Contra access removed locally. You can also revoke access in Contra.'}
