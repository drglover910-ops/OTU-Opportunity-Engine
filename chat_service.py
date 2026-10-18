"""Acknowledged, idempotent chat requests. Only an explicit send starts inference."""
import hashlib,json,os,re,threading
from engine import now
class ChatService:
 def __init__(self,e):
  self.e=e
  with e.connect() as c:c.execute("UPDATE chat_requests SET status='interrupted',error=?,updated=? WHERE status IN ('queued','running')",('The app restarted before completion was confirmed. Check the conversation before sending again.',now()))
 def row(self,key):
  if not re.fullmatch(r'[a-zA-Z0-9-]{24,64}',str(key)):raise ValueError('Request not found.')
  with self.e.connect() as c:r=c.execute('SELECT * FROM chat_requests WHERE id=?',(key,)).fetchone()
  if not r:raise ValueError('Request not found.')
  r=dict(r);r['payload']=json.loads(r['payload']);r['result']=json.loads(r['result'] or '{}');return r
 def start(self,d):
  workspace,oid=self.e.conversation_scope(d);chat=self.e.chat_key(d,workspace,oid);key=str(d.get('request_id',''))
  if not re.fullmatch(r'[a-zA-Z0-9-]{24,64}',key):raise ValueError('A send identifier is required.')
  payload={k:d.get(k) for k in ('workspace','opportunity_id','chat_id','text','mode','document_id','draft_id')};payload.update(workspace=workspace,opportunity_id=oid,chat_id=chat,text=str(d.get('text','')).strip(),mode=d.get('mode') or 'advice')
  if not 1<=len(payload['text'])<=4000:raise ValueError('Write a question of up to 4,000 characters.')
  if payload['mode'] not in ('advice','reply','predict','negotiate','revise_document','revise_proposal','research'):raise ValueError('Choose a supported conversation mode.')
  encoded=json.dumps(payload,sort_keys=True);fingerprint=hashlib.sha256(encoded.encode()).hexdigest()
  with self.e.lock:
   with self.e.connect() as c:
    existing=c.execute('SELECT fingerprint FROM chat_requests WHERE id=?',(key,)).fetchone()
    if existing:
     if existing['fingerprint']!=fingerprint:raise ValueError('This send identifier belongs to a different message.')
     return self.row(key)
    if c.execute("SELECT id FROM chat_requests WHERE workspace=? AND opportunity_id IS ? AND chat_id IS ? AND status IN ('queued','running')",(workspace,oid,chat)).fetchone():raise ValueError('Isis is already answering in this conversation. Wait for that reply first.')
    if c.execute("SELECT count(*) FROM chat_requests WHERE status IN ('queued','running')").fetchone()[0]>=3:raise ValueError('Three conversations are already being answered. Wait for one to finish.')
   from research_tools import requested
   if not os.getenv('HF_INFERENCE_TOKEN') and not requested(payload):raise ValueError('AI writing is not connected. You can still save a note.')
   note=self.e.add_work_note(payload,role='user')['id']
   with self.e.connect() as c:c.execute('INSERT INTO chat_requests(id,workspace,opportunity_id,chat_id,fingerprint,payload,status,user_note_id,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)',(key,workspace,oid,chat,fingerprint,encoded,'queued',note,now(),now()))
   threading.Thread(target=self.run,args=(key,),daemon=True).start()
  return self.row(key)
 def run(self,key):
  row=self.row(key)
  with self.e.connect() as c:c.execute("UPDATE chat_requests SET status='running',updated=? WHERE id=?",(now(),key))
  try:
   def progress(receipt):
    with self.e.lock,self.e.connect() as c:c.execute('UPDATE chat_requests SET result=?,updated=? WHERE id=?',(json.dumps({'research':receipt}),now(),key))
   result=self.e.ask_workspace(row['payload'],user_note_id=row['user_note_id'],progress=progress)
   with self.e.lock,self.e.connect() as c:c.execute("UPDATE chat_requests SET status='complete',assistant_note_id=?,result=?,updated=? WHERE id=?",(result['note_id'],json.dumps(result),now(),key))
  except Exception as error:
   message=str(error) if isinstance(error,ValueError) else 'Isis could not finish this reply. Your message is saved. Check Connections before trying again.'
   with self.e.lock,self.e.connect() as c:c.execute("UPDATE chat_requests SET status='failed',error=?,updated=? WHERE id=?",(message[:500],now(),key))
