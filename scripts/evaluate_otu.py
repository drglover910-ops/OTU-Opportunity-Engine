"""Offline retrieval baseline with synthetic records. Never calls a model or platform."""
import base64,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Engine
from attachment_store import AttachmentStore

def run_case(case):
 with tempfile.TemporaryDirectory() as folder:
  e=Engine(folder);a=AttachmentStore(e)
  main=e.create_chat({'workspace':'contra','title':'Synthetic planning'})
  scope={k:main[k] for k in ('workspace','opportunity_id')};scope['chat_id']=main['id']
  other=e.create_chat({'workspace':'contra','title':'Unrelated private conversation'})
  other_scope={**scope,'chat_id':other['id']}
  for record in case.get('records',[]):
   r=dict(record);kind=r['kind'];text=r['text'];target=other_scope if r.get('other_chat') else scope
   if kind=='master':e.import_file(r.get('name','Master_Career_Resume_Example.txt'),text.encode())
   elif kind=='example':e.import_file('Prior_Application_Example.txt',text.encode(),'resume')
   elif kind in ('owner','assistant'):e.add_work_note({**target,'text':text},role='user' if kind=='owner' else 'assistant')
   elif kind=='update':
    with e.connect() as c:c.execute('INSERT INTO career_updates(fact,type,category,source,created) VALUES(?,?,?,?,?)',(text,'user_fact','All','Confirmed by owner','2026-10-17T12:00:00Z'))
   elif kind=='file':
    raw=text.encode();f=a.start({**target,'name':r.get('name','Reference.txt'),'size':len(raw)});a.chunk({'id':f['id'],'offset':0,'content':base64.b64encode(raw).decode()});a.finish({'id':f['id']})
    if r.get('enabled'):e.knowledge.enable_file({**target,'id':f['id'],'confirmed':True,'enabled':True})
  for i in range(case.get('later_notes',0)):e.add_work_note({**scope,'text':'Unrelated meeting logistics '+str(i)},role='user')
  sources=e.knowledge.search({**scope,'text':case['query']});body=json.dumps(sources,ensure_ascii=False)
  failures=[]
  for phrase in case.get('contains',[]):
   if phrase not in body:failures.append('missing '+phrase)
  for phrase in case.get('excludes',[]):
   if phrase in body:failures.append('leaked '+phrase)
  if case.get('empty') and sources:failures.append('expected no evidence')
  if len(sources)>4 or len(body.encode())>4800:failures.append('evidence budget exceeded')
  return {'id':case['id'],'passed':not failures,'failures':failures}

def run_suite():
 cases=json.loads((Path(__file__).resolve().parents[1]/'evals/otu_cases.json').read_text())
 return [run_case(c) for c in cases]

if __name__=='__main__':
 results=run_suite();print(json.dumps({'scope':'Offline retrieval only; no model quality or action execution score','passed':sum(r['passed'] for r in results),'total':len(results),'results':results},indent=2));sys.exit(0 if all(r['passed'] for r in results) else 1)
