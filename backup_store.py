"""Streaming private recovery archives. Credentials never enter an export."""
import hashlib,json,re,secrets,shutil,tempfile,zipfile
from pathlib import Path
from engine import VERSION,now
TABLES=('opportunities','documents','activity','drafts','messages','career_updates','packages','email_threads','workspaces','conversation_threads','work_notes','conversation_memory','platforms','platform_profiles','developer_requests','projects','chat_organization','mail_folders','mail_organization','attachment_uploads','response_feedback','chat_requests','file_knowledge','contra_application_actions')
UPLOAD_COLUMNS=('id','name','size','received','workspace','opportunity_id','chat_id','state','created','digest')
EXTRA=('projects','chat_organization','mail_folders','mail_organization','contra_application_actions')
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
class Backups:
 def __init__(self,e):self.e=e
 def export(self,target=None,exclude_upload_id=None):
  root=self.e.data/'backups';root.mkdir(exist_ok=True)
  target=Path(target) if target else root/('OTU-'+VERSION+'-'+secrets.token_hex(8)+'.zip')
  partial=target.with_suffix('.part')
  try:
   with self.e.lock,self.e.connect() as c:
    exists={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    data={t:[dict(r) for r in c.execute('SELECT * FROM '+t)] for t in TABLES if t in exists}
    data['attachment_uploads']=[r for r in data.get('attachment_uploads',[]) if r['state']=='complete' and r['id']!=exclude_upload_id]
    data['file_knowledge']=[r for r in data.get('file_knowledge',[]) if r['upload_id'] in {u['id'] for u in data['attachment_uploads']}]
    manifest={};files=[]
    for row in data.get('documents',[]):
     path=Path(row['path']);row['path']=path.name;files.append(('career/'+path.name,path,row['digest']))
    for row in data['attachment_uploads']:files.append(('attachments/'+row['id'],self.e.data/'attachments'/row['id'],row['digest']))
    with zipfile.ZipFile(partial,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
     for name,path,expected in files:
      if not path.is_file() or digest(path)!=expected:raise ValueError('A saved file is missing or damaged. Backup stopped; existing work is unchanged.')
      z.write(path,name);manifest[name]=expected
     data.update(version=VERSION,exported=now(),format='otu-complete-1')
     z.writestr('records.json',json.dumps(data));z.writestr('manifest.json',json.dumps(manifest))
   partial.replace(target);self.e.set_setting('last_backup',now());return target
  except Exception:
   partial.unlink(missing_ok=True);raise
 def checkpoint(self):
  target=self.e.data/'backups'/'before-v0.16.0.zip'
  if not target.exists():self.export(target)
  return target
 def status(self):
  checkpoint=self.e.data/'backups'/'before-v0.16.0.zip'
  if not checkpoint.is_file():return {'checkpoint':False,'preserved':False}
  with zipfile.ZipFile(checkpoint) as z:
   if z.getinfo('records.json').file_size>20*1024**2:raise ValueError('Recovery index too large.')
   baseline=json.loads(z.read('records.json'))
  checks={};counts={}
  with self.e.connect() as c:
   for table,fields in [('work_notes',('id','workspace','opportunity_id','chat_id','text')),('conversation_memory',('id','workspace','opportunity_id','chat_id','text')),('conversation_threads',('id','workspace','opportunity_id')),('documents',('id','digest')),('attachment_uploads',('id','digest'))]:
    current={tuple(r[k] for k in fields) for r in c.execute('SELECT * FROM '+table)}
    original={tuple(r.get(k) for k in fields) for r in baseline.get(table,[])}
    checks[table]=original.issubset(current);counts[table]={'before':len(original),'now':len(current)}
  return {'checkpoint':True,'bytes':checkpoint.stat().st_size,'preserved':all(checks.values()),'checks':checks,'counts':counts,'credentials_included':False}
 def restore(self,path,source_upload_id=None):
  # Verify every byte and relation before touching live records. Never extract arbitrary ZIP paths.
  with self.e.lock,zipfile.ZipFile(path) as z:
   infos=z.infolist();names=[i.filename for i in infos]
   if len(names)!=len(set(names)) or len(infos)>20000:raise ValueError('Invalid backup entries.')
   if z.getinfo('records.json').file_size>20*1024**2 or z.getinfo('manifest.json').file_size>4*1024**2:raise ValueError('Backup index too large.')
   data=json.loads(z.read('records.json'));manifest=json.loads(z.read('manifest.json'))
   if data.get('format')!='otu-complete-1':raise ValueError('Choose a complete OTU backup. Older backups use the legacy restore option.')
   if set(data)-set(TABLES)-{'format','version','exported'}:raise ValueError('Unknown backup records.')
   if set(names)!=set(manifest)|{'records.json','manifest.json'}:raise ValueError('Backup manifest does not match its files.')
   if sum(i.file_size for i in infos)>10*1024**3:raise ValueError('Expanded backup exceeds 10 GiB.')
   docs=data.get('documents',[]);uploads=data.get('attachment_uploads',[])
   expected={}
   for r in docs:
    if not re.fullmatch(r'[a-f0-9]{64}\.(pdf|docx|txt|md|json)',r['path']):raise ValueError('Invalid document path.')
    expected['career/'+r['path']]=r['digest']
   for r in uploads:
    if set(r)!=set(UPLOAD_COLUMNS):raise ValueError('Invalid upload fields.')
    if not re.fullmatch('[a-f0-9]{32}',r['id']) or r['state']!='complete' or not 0<r['size']<=1024**3 or r['received']!=r['size']:raise ValueError('Invalid saved upload.')
    if z.getinfo('attachments/'+r['id']).file_size!=r['size']:raise ValueError('Upload size mismatch.')
    expected['attachments/'+r['id']]=r['digest']
   if manifest!=expected:raise ValueError('Backup file references do not match.')
   for row in data.get('file_knowledge',[]):
    upload=next((u for u in uploads if u['id']==row.get('upload_id')),None)
    if not upload or row.get('digest')!=upload['digest'] or not isinstance(row.get('text'),str) or len(row['text'])>50000:raise ValueError('Invalid readable-file reference.')
   threads={r['id']:r for r in data.get('conversation_threads',[])};opps={r['id']:r for r in data.get('opportunities',[])}
   workspaces={r['id'] for r in data.get('workspaces',[])}
   for row in list(threads.values())+data.get('work_notes',[])+data.get('conversation_memory',[])+data.get('contra_application_actions',[])+uploads:
    if row['workspace'] not in workspaces:raise ValueError('Missing conversation workspace.')
    if row.get('opportunity_id') and row['opportunity_id'] not in opps:raise ValueError('Missing conversation opportunity.')
    if row.get('chat_id'):
     thread=threads.get(row['chat_id'])
     if not thread or thread['workspace']!=row['workspace'] or thread['opportunity_id']!=row.get('opportunity_id'):raise ValueError('Conversation scope mismatch.')
   for action in data.get('contra_application_actions',[]):
    if not re.fullmatch(r'[a-f0-9]{32}',str(action.get('id',''))) or not isinstance(json.loads(action.get('data','null')),dict):raise ValueError('Invalid saved Contra application receipt.')
    with self.e.connect() as c:old=c.execute('SELECT workspace,opportunity_id,chat_id FROM contra_application_actions WHERE id=?',(action['id'],)).fetchone()
    if old and (old['workspace'],old['chat_id'])!=(action['workspace'],action.get('chat_id')):raise ValueError('Application receipt identity collision.')
   notes={r['id']:r for r in data.get('work_notes',[])}
   for job in data.get('chat_requests',[]):
    if not re.fullmatch(r'[a-zA-Z0-9-]{24,64}',str(job.get('id',''))) or job.get('status') not in ('queued','running','complete','failed','interrupted'):raise ValueError('Invalid chat request receipt.')
    question=notes.get(job.get('user_note_id'))
    scope=lambda row:(row.get('workspace'),row.get('opportunity_id'),row.get('chat_id'))
    if not question or question.get('role')!='user' or scope(question)!=scope(job):raise ValueError('Backup request/question scope mismatch.')
    if job.get('assistant_note_id'):
     answer=notes.get(job['assistant_note_id'])
     if not answer or answer.get('role')!='assistant' or scope(answer)!=scope(job):raise ValueError('Backup request/answer scope mismatch.')
   for feedback in data.get('response_feedback',[]):
    answer=notes.get(feedback.get('note_id'))
    if not answer or answer.get('role')!='assistant' or type(feedback.get('rating')) is not int or feedback['rating'] not in (-1,1):raise ValueError('Invalid response rating in backup.')
   for r in uploads:
    if r.get('opportunity_id') and r['opportunity_id'] not in opps:raise ValueError('Missing upload opportunity.')
    if r.get('chat_id'):
     t=threads.get(r['chat_id'])
     if not t or t['workspace']!=r['workspace'] or t['opportunity_id']!=r['opportunity_id']:raise ValueError('Upload conversation mismatch.')
   with self.e.connect() as c:
    for key,t in threads.items():
     old=c.execute('SELECT * FROM conversation_threads WHERE id=?',(key,)).fetchone()
     oid=t.get('opportunity_id');oldurl=self.e.get(old['opportunity_id'])['url'] if old and old['opportunity_id'] else None
     if old and (old['workspace']!=t['workspace'] or oldurl!=(opps[oid]['url'] if oid else None)):raise ValueError('Conversation identity collision; restore into a separate private installation.')
    for r in uploads:
     old=c.execute('SELECT digest FROM attachment_uploads WHERE id=?',(r['id'],)).fetchone()
     if old and old['digest']!=r['digest']:raise ValueError('Upload identity collision.')
   for name,sha in manifest.items():
    h=hashlib.sha256()
    with z.open(name) as stream:
     for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    if h.hexdigest()!=sha:raise ValueError('Backup checksum mismatch.')
   if sum(z.getinfo('career/'+r['path']).file_size for r in docs)>95*1024**2:raise ValueError('Career documents exceed the current 95 MiB recovery limit. Conversation uploads support 1 GiB each.')
   # A complete checkpoint remains available even if a later merge encounters storage failure.
   self.export(self.e.data/'backups'/('before-restore-'+secrets.token_hex(8)+'.zip'),exclude_upload_id=source_upload_id)
   with tempfile.TemporaryDirectory(dir=self.e.data) as tmp:
    core=Path(tmp)/'core.zip'
    with zipfile.ZipFile(core,'w',zipfile.ZIP_DEFLATED) as out:
     out.writestr('records.json',json.dumps({k:v for k,v in data.items() if k not in EXTRA+('attachment_uploads','file_knowledge','format')}))
     for r in docs:out.writestr('career/'+r['path'],z.read('career/'+r['path']))
    result=self.e.restore(core.read_bytes(),complete=True)
    with self.e.connect() as c:
     leadmap={}
     for r in opps.values():
      found=c.execute('SELECT id FROM opportunities WHERE url=?',(r['url'],)).fetchone() if r.get('url') else c.execute('SELECT id FROM opportunities WHERE lower(company)=lower(?) AND lower(title)=lower(?) AND source=?',(r['company'],r['title'],r['source'])).fetchone()
      if not found:raise ValueError('Restored opportunity could not be linked.')
      leadmap[r['id']]=found[0]
     projectmap={};foldermap={}
     for table,mapping in [('projects',projectmap),('mail_folders',foldermap)]:
      for row in data.get(table,[]):
       old=c.execute('SELECT id FROM '+table+' WHERE name=?',(row['name'],)).fetchone()
       mapping[row['id']]=old['id'] if old else row['id']
     for table in EXTRA:
      columns=[r[1] for r in c.execute('PRAGMA table_info('+table+')')]
      for original in data.get(table,[]):
       row=dict(original)
       if table=='contra_application_actions':
        row['opportunity_id']=leadmap.get(row.get('opportunity_id'));row['remote_draft_id']='';row['status']='Restored'
        restored=json.loads(row['data']);restored.pop('arguments',None);restored.pop('preview_digest',None);row['data']=json.dumps(restored)
       if table=='projects':row['id']=projectmap[row['id']]
       if table=='mail_folders':row['id']=foldermap[row['id']]
       if table=='chat_organization' and row.get('project_id'):row['project_id']=projectmap.get(row['project_id'],row['project_id'])
       if table=='mail_organization' and row.get('folder_id'):row['folder_id']=foldermap.get(row['folder_id'],row['folder_id'])
       if table=='mail_organization' and row.get('opportunity_id'):row['opportunity_id']=leadmap.get(row['opportunity_id'])
       if table=='chat_organization' and row['key'].startswith('legacy:'):
        prefix,workspace,oid=row['key'].split(':');row['key']='legacy:'+workspace+':'+str(leadmap.get(int(oid)) if oid else '')
       c.execute('INSERT OR IGNORE INTO '+table+'('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',[row.get(k) for k in columns])
     for original in uploads:
      r=dict(original);r['opportunity_id']=leadmap.get(r.get('opportunity_id'));dest=self.e.data/'attachments'/r['id'];dest.parent.mkdir(exist_ok=True)
      if not dest.exists():
       partial=Path(tmp)/r['id']
       with z.open('attachments/'+r['id']) as source,partial.open('wb') as out:shutil.copyfileobj(source,out,1024**2)
       partial.replace(dest)
      columns=UPLOAD_COLUMNS;c.execute('INSERT OR IGNORE INTO attachment_uploads('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',[r[k] for k in columns])
     for r in data.get('file_knowledge',[]):c.execute('INSERT OR IGNORE INTO file_knowledge VALUES(?,?,?,?)',(r['upload_id'],r['digest'],r['text'],r['created']))
   result['message']='Saved work and conversation uploads merged. Existing work preserved; sending approvals reset. Reconnect accounts if needed.';return result
