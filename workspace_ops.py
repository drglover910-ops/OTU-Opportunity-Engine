"""Organization only: source scopes, conversation contents and Gmail stay intact."""
import json,secrets,urllib.parse
from engine import now,fetch_json

class WorkspaceOps:
 def __init__(self,e):
  self.e=e
  with e.connect() as c:
   c.executescript('''CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS chat_organization(key TEXT PRIMARY KEY,project_id TEXT,title TEXT,pinned INTEGER DEFAULT 0,archived INTEGER DEFAULT 0,trashed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS mail_folders(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS mail_organization(thread_id TEXT PRIMARY KEY,folder_id TEXT,followup TEXT DEFAULT '',opportunity_id INTEGER);
CREATE TABLE IF NOT EXISTS mail_cache(thread_id TEXT PRIMARY KEY,payload TEXT,updated TEXT);''')
   for w in e.workspaces():c.execute('INSERT OR IGNORE INTO projects VALUES(?,?)',(w['id'],w['name']))
 def projects(self):
  with self.e.connect() as c:
   for w in self.e.workspaces():c.execute('INSERT OR IGNORE INTO projects VALUES(?,?)',(w['id'],w['name']))
   return [dict(r) for r in c.execute('SELECT * FROM projects ORDER BY name')]
 def create_project(self,d):
  name=str(d.get('name','')).strip()[:80]
  if not name:raise ValueError('Give your project a name.')
  with self.e.lock,self.e.connect() as c:
   existing=c.execute('SELECT id FROM projects WHERE name=?',(name,)).fetchone()
   if existing:return {'id':existing['id']}
   key=secrets.token_hex(12);c.execute('INSERT INTO projects VALUES(?,?)',(key,name))
  return {'id':key}
 @staticmethod
 def key(t):return t['id'] or 'legacy:'+t['workspace']+':'+str(t.get('opportunity_id') or '')
 def threads(self):
  with self.e.connect() as c:meta={r['key']:dict(r) for r in c.execute('SELECT * FROM chat_organization')}
  rows=[]
  for t in self.e.chat_threads():
   key=self.key(t);m=meta.get(key,{})
   rows.append({**t,'key':key,'project_id':m.get('project_id') or t['workspace'],'title':m.get('title') or t['title'],'pinned':bool(m.get('pinned')),'archived':bool(m.get('archived')),'trashed':bool(m.get('trashed'))})
  return sorted(rows,key=lambda r:r['pinned'],reverse=True)
 def change(self,d):
  key=str(d.get('key',''));t=next((r for r in self.threads() if r['key']==key),None)
  if not t:raise ValueError('Conversation not found.')
  action=d.get('action');updates={}
  if action=='rename':
   title=str(d.get('title','')).strip()[:100]
   if not title:raise ValueError('Give your conversation a name.')
   updates['title']=title
   if t['id']:self.e.rename_chat({'id':t['id'],'title':title})
  elif action=='move':
   if not any(p['id']==d.get('project_id') for p in self.projects()):raise ValueError('Project not found.')
   updates['project_id']=d['project_id']
  elif action=='pin':updates['pinned']=not t['pinned']
  elif action=='archive':updates['archived']=not t['archived']
  elif action=='trash':
   if d.get('confirmed') is not True:raise ValueError('Confirm moving this conversation to Trash.')
   updates['trashed']=1
  elif action=='restore':updates.update(trashed=0,archived=0)
  else:raise ValueError('Choose a conversation action.')
  with self.e.lock,self.e.connect() as c:
   c.execute('INSERT OR IGNORE INTO chat_organization(key) VALUES(?)',(key,))
   for field,value in updates.items():c.execute('UPDATE chat_organization SET '+field+'=? WHERE key=?',(value,key))
  return {'saved':True,'message':'Conversation updated. Its messages, files and original opportunity stay together.'}
 def folders(self):
  with self.e.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM mail_folders ORDER BY name')]
 def organize_mail(self,d):
  with self.e.lock,self.e.connect() as c:
   if d.get('action')=='folder':
    name=str(d.get('name','')).strip()[:80]
    if not name:raise ValueError('Give the folder a name.')
    key=secrets.token_hex(12);c.execute('INSERT OR IGNORE INTO mail_folders VALUES(?,?)',(key,name));return {'saved':True}
   key=str(d.get('thread_id',''))
   if not key or len(key)>100:raise ValueError('Choose a mail thread.')
   folder=d.get('folder_id') or None
   if folder and not c.execute('SELECT id FROM mail_folders WHERE id=?',(folder,)).fetchone():raise ValueError('Folder not found.')
   oid=int(d['opportunity_id']) if d.get('opportunity_id') else None
   lead=self.e.get(oid) if oid else None
   known=c.execute('SELECT opportunity_id FROM email_threads WHERE thread_id=?',(key,)).fetchone()
   if known and oid and known['opportunity_id']!=oid:raise ValueError('This thread already belongs to another opportunity. Keep its original link so conversations stay separate.')
   if known and not oid:oid=known['opportunity_id'];lead=self.e.get(oid)
   followup=str(d.get('followup',''))
   if followup:
    from datetime import date
    date.fromisoformat(followup)
   c.execute('INSERT OR REPLACE INTO mail_organization VALUES(?,?,?,?)',(key,folder,followup,oid))
   cached=c.execute('SELECT payload FROM mail_cache WHERE thread_id=?',(key,)).fetchone()
   if oid and cached:
    from mail_history import summarize
    thread=json.loads(cached['payload']);messages=thread.get('messages',[])
    c.execute('INSERT OR REPLACE INTO email_threads(thread_id,opportunity_id,company,subject,summary,messages,reviewed) VALUES(?,?,?,?,?,?,?)',(key,oid,lead['company'],thread['subject'],json.dumps(summarize(messages)),json.dumps(messages),now()))
  return {'saved':True}
 def mail_list(self,d):
  box=d.get('box','inbox');search=str(d.get('search',''))[:200];page=str(d.get('page',''))[:500]
  with self.e.connect() as c:metadata={r['thread_id']:dict(r) for r in c.execute('SELECT * FROM mail_organization')}
  if box in ('drafts','outbox'):
   rows=self.e.drafts();rows=[r for r in rows if (r['status']=='Draft' if box=='drafts' else r['status'] in ('Approved','Sending','Delivery unknown'))]
   return {'local':True,'items':[r for r in rows if search.lower() in (r['subject']+' '+r['body']+' '+r['recipient']).lower()],'folders':self.folders(),'next_page':None}
  token=self.e.gmail_token();headers={'Authorization':'Bearer '+token}
  params={'maxResults':max(1,min(20,int(d.get('limit',20))))}
  if box in ('inbox','sent'):params['labelIds']='INBOX' if box=='inbox' else 'SENT'
  elif box!='all' and not any(f['id']==box for f in self.folders()):raise ValueError('Mail folder not found.')
  if search:params['q']=search
  if page:params['pageToken']=page
  # Folder views are local cached membership, so Gmail requires no label-write scope.
  if box not in ('inbox','sent','all'):
   with self.e.connect() as c:items=[json.loads(r['payload']) for r in c.execute('SELECT payload FROM mail_cache JOIN mail_organization USING(thread_id) WHERE folder_id=? ORDER BY updated DESC',(box,))]
   items=[r for r in items if search.lower() in json.dumps(r).lower()];next_page=None
  else:
   raw=fetch_json('https://gmail.googleapis.com/gmail/v1/users/me/threads?'+urllib.parse.urlencode(params),headers=headers)
   items=raw.get('threads',[]);next_page=raw.get('nextPageToken')
   from concurrent.futures import ThreadPoolExecutor
   def headline(item):
    # Metadata only: bodies are fetched when the owner opens a thread.
    try:
     raw=fetch_json('https://gmail.googleapis.com/gmail/v1/users/me/threads/'+urllib.parse.quote(item['id'],safe='')+'?format=metadata&metadataHeaders=Subject&metadataHeaders=From&metadataHeaders=Date',headers=headers)
     last=(raw.get('messages') or [{}])[-1];h={x['name'].lower():x['value'] for x in last.get('payload',{}).get('headers',[])}
     return {**item,'subject':h.get('subject',''),'sender':h.get('from',''),'date':h.get('date','')}
    except ValueError:return item
   with ThreadPoolExecutor(max_workers=4) as pool:items=list(pool.map(headline,items))
  return {'items':[{**r,'organization':metadata.get(r['id'],{})} for r in items],'folders':self.folders(),'next_page':next_page,'checked':now(),'local':False}
 def mail_thread(self,key):
  import re
  if not re.fullmatch('[a-zA-Z0-9_-]{1,100}',key):raise ValueError('Invalid mail thread.')
  from mail_history import parse_messages
  raw=fetch_json('https://gmail.googleapis.com/gmail/v1/users/me/threads/'+key+'?format=full',headers={'Authorization':'Bearer '+self.e.gmail_token()})
  messages=parse_messages(raw,self.e.setting('gmail_owner',''))
  result={'id':key,'messages':messages,'snippet':raw.get('snippet',''),'subject':messages[-1]['subject'] if messages else 'Mail conversation'}
  with self.e.lock,self.e.connect() as c:
   c.execute('INSERT OR REPLACE INTO mail_cache VALUES(?,?,?)',(key,json.dumps(result),now()))
   meta=c.execute('SELECT * FROM mail_organization WHERE thread_id=?',(key,)).fetchone()
  result['organization']=dict(meta) if meta else {}
  if not result['organization'].get('opportunity_id'):
   with self.e.connect() as c:known=c.execute('SELECT opportunity_id FROM email_threads WHERE thread_id=?',(key,)).fetchone()
   if known:result['organization']['opportunity_id']=known['opportunity_id']
  return result
