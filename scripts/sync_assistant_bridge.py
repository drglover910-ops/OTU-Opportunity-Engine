"""Transfer only owner-reviewed request text to a verified private repository. No AI or code execution."""
import json,os,sys,urllib.request,subprocess
from pathlib import Path
BASE='https://dezz-9-10-otu-opportunity-engine.hf.space'
REPO='drglover910-ops/OTU-Opportunity-Engine'
HEADERS={'Authorization':'Bearer '+os.environ['HF_TOKEN'],'Content-Type':'application/json'}
def app(path,data=None):
 req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=40) as response:return json.load(response)
def main():
 ledger=Path('docs/assistant_bridge/requests.json')
 if '--ack' in sys.argv:
  commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
  requests=json.loads(ledger.read_text()) if ledger.exists() else []
  statuses={r['id']:r for r in app('/api/developer/requests')}
  for row in requests:
   if statuses.get(row['id'],{}).get('status')=='Queued for repository sync':app('/api/developer/request-update',{'id':row['id'],'status':'In developer inbox','repo_commit':commit})
  print('Repository receipts acknowledged.');return
 token=os.environ['GITHUB_TOKEN']
 req=urllib.request.Request('https://api.github.com/repos/'+REPO,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'OTU private request bridge'})
 with urllib.request.urlopen(req,timeout=30) as response:repository=json.load(response)
 if repository.get('private') is not True:raise ValueError('Request transfer requires a verified private repository.')
 rows=app('/api/developer/requests');saved=json.loads(ledger.read_text()) if ledger.exists() else [];known={r['id'] for r in saved}
 for row in rows:
  if row['status']=='Queued for repository sync' and row['id'] not in known:
   saved.append({**{k:row[k] for k in ('id','workspace','opportunity_id','text','created')},**({'chat_id':row['chat_id']} if row.get('chat_id') else {})});known.add(row['id'])
 ledger.parent.mkdir(parents=True,exist_ok=True);ledger.write_text(json.dumps(saved,indent=2)+'\n')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 for file in Path('docs/assistant_bridge/replies').glob('*.json'):
  reply=json.loads(file.read_text());key=file.stem
  if not any(r['id']==key for r in rows):continue
  if reply.get('status') not in ('Developer replied','Completed'):raise ValueError('A reply must explicitly state its status.')
  if not isinstance(reply.get('message'),str) or not 1<=len(reply['message'])<=8000:raise ValueError('A reply needs a concise plain-text message.')
  app('/api/developer/request-update',{'id':key,'reply':reply['message'],'status':reply['status'],'repo_commit':commit})
 print('Private request bridge checked. No AI calls, agent starts, platform writes or messages to clients.')
if __name__=='__main__':
 try:main()
 except Exception as exc:raise SystemExit('Bridge sync incomplete ('+type(exc).__name__+'). Requests remain saved; check private repository access and bot runtime.') from None
