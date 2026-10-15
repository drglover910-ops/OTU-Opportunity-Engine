"""Anonymous, read-only protocol discovery. No login, tokens, tools/call, or account changes."""
import json,re,urllib.request,urllib.error,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
ENDPOINT='https://contra.com/mcp'

def probe(url,data=None,headers=None):
 req=urllib.request.Request(url,data=json.dumps(data).encode() if data else None,headers={'Accept':'application/json, text/event-stream','User-Agent':'OTU-Opportunity-Engine protocol discovery','Content-Type':'application/json',**(headers or {})})
 try:r=urllib.request.urlopen(req,timeout=25)
 except urllib.error.HTTPError as e:r=e
 except Exception as e:return {'url':url,'error':type(e).__name__}
 result={'url':url,'status':r.code,'content_type':r.headers.get('Content-Type',''),'www_authenticate':r.headers.get('WWW-Authenticate','')}
 if 'event-stream' in result['content_type']:
  result['stream']='present; not consumed';r.close();return result
 raw=r.read(300000).decode(errors='replace');r.close()
 try:
  obj=json.loads(raw)
  if isinstance(obj,dict):
   keys=['resource','authorization_servers','issuer','authorization_endpoint','token_endpoint','registration_endpoint','scopes_supported','response_types_supported','code_challenge_methods_supported','grant_types_supported','token_endpoint_auth_methods_supported','error','error_description','jsonrpc','id','result']
   result['metadata']={k:obj[k] for k in keys if k in obj}
 except ValueError:
  title=re.search(r'<title[^>]*>(.*?)</title>',raw,re.S|re.I)
  if title:result['page_title']=re.sub(r'\s+',' ',title.group(1))[:180]
 return result
report={'checked_at':datetime.now(timezone.utc).isoformat(),'mode':'anonymous protocol discovery; no account access or write tools'}
report['initialize']=probe(ENDPOINT,{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'OTU discovery','version':'0.1'}}})
report['protected_resource']=probe('https://contra.com/.well-known/oauth-protected-resource/mcp')
report['authorization_server']=probe('https://contra.com/.well-known/oauth-authorization-server')
report['openid']=probe('https://contra.com/.well-known/openid-configuration')
for server in report['protected_resource'].get('metadata',{}).get('authorization_servers',[])[:2]:
 p=urllib.parse.urlsplit(server)
 if p.scheme=='https' and p.hostname and (p.hostname=='contra.com' or p.hostname.endswith('.contra.com')):
  report.setdefault('additional_authorization_metadata',[]).append(probe(server.rstrip('/')+'/.well-known/oauth-authorization-server'))
Path('docs/CONTRA_MCP_DISCOVERY.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
