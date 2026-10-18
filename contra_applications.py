"""Owner-reviewed native Contra applications; never dispatched by model prose."""
import hashlib,json,re,secrets,sqlite3,threading,time
from datetime import datetime,timezone
from urllib.parse import urlsplit
from contra_mcp import ContraConnection
from research_tools import parsed_content,nodes,safe_contra_url,text
from knowledge_store import SECRET
from engine import now
UUID=re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$')
class ContraApplications:
 def __init__(self,e):
  self.e=e;self.lock=threading.Lock()
  with e.connect() as c:
   c.execute("UPDATE contra_application_actions SET status='Prepare uncertain' WHERE status='Preparing'")
   c.execute("UPDATE contra_application_actions SET status='Submission uncertain' WHERE status='Submitting'")
 def scope(self,d):
  w,o=self.e.conversation_scope(d);chat=self.e.chat_key(d,w,o)
  if w not in ('contra','assistant'):raise ValueError('Open Contra or My assistant for this application.')
  return w,o,chat
 def record(self,d):
  w,o,chat=self.scope(d)
  with self.e.connect() as c:r=c.execute('SELECT * FROM contra_application_actions WHERE id=?',(str(d.get('id','')),)).fetchone()
  if not r or (r['workspace'],r['opportunity_id'],r['chat_id'])!=(w,o,chat):raise ValueError('Open the conversation that owns this application.')
  r=dict(r);r['data']=json.loads(r['data']);return r
 def save(self,r,status,expected=None):
  r['status']=status;r['updated']=now()
  try:
   with self.e.lock,self.e.connect() as c:
    sql='UPDATE contra_application_actions SET status=?,data=?,remote_draft_id=?,updated=? WHERE id=?';args=(status,json.dumps(r['data']),r.get('remote_draft_id',''),r['updated'],r['id'])
    if expected:sql+=' AND status=?';args+=(expected,)
    if c.execute(sql,args).rowcount!=1:raise ValueError('This application changed while the action was starting. Check its saved status before continuing.')
  except sqlite3.IntegrityError:raise ValueError('Another application preview or submission already exists for this listing. Review it first.') from None
 def view(self,r):
  return {'id':r['id'],'status':r['status'],**{k:v for k,v in r['data'].items() if k not in ('arguments',)},'updated':r['updated'],'scope':{'workspace':r['workspace'],'opportunity_id':r['opportunity_id'],'chat_id':r['chat_id']}}
 def body(self,result):
  body=next(iter(result.values()),{'isError':True})
  if body.get('isError'):raise ValueError('Contra did not complete this action. Check the original listing before trying again.')
  parsed=parsed_content(body)
  if not parsed or any(isinstance(x,dict) and x.get('ok') is False for x in parsed):raise ValueError('Contra returned no successful action result.')
  return parsed
 def options(self,d):
  w,o,chat=self.scope(d);url=str(d.get('url','')).split('?',1)[0].rstrip('/')
  if not safe_contra_url(url) or '/opportunity/' not in url:raise ValueError('Choose an exact Contra opportunity link first.')
  slug=urlsplit(url).path.split('/opportunity/',1)[1]
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,180}',slug):raise ValueError('This listing link is not supported.')
  if o and (self.e.get(o).get('url') or '').split('?',1)[0].rstrip('/')!=url:raise ValueError('This listing belongs in its own opportunity conversation.')
  with self.e.connect() as c:existing=c.execute("SELECT * FROM contra_application_actions WHERE workspace=? AND opportunity_id IS ? AND chat_id IS ? AND json_extract(data,'$.url')=? AND status IN ('Preview ready','Preparing','Prepare uncertain','Submitted','Submitting','Submission uncertain') ORDER BY created DESC LIMIT 1",(w,o,chat,url)).fetchone()
  if existing and d.get('inspect_only') is not True:
   existing=dict(existing);existing['data']=json.loads(existing['data']);return self.view(existing)
  connection=ContraConnection(self.e);result=connection.read_tools([('get_job_by_slug',{'slug':slug}),('list_portfolio_projects',{'username':'desmond_glover_59of9zq6','limit':25,'includeDrafts':False})])
  jobtrees=self.body({k:v for k,v in result.items() if k.startswith('get_job_by_slug:')});porttrees=self.body({k:v for k,v in result.items() if k.startswith('list_portfolio_projects:')})
  allnodes=[n for t in jobtrees for n in nodes(t)];job=next((n for n in allnodes if n.get('publicUrl','').split('?',1)[0].rstrip('/')==url and n.get('title')),None)
  if not job:raise ValueError('Contra did not return this exact listing. No application was prepared.')
  posting=(job.get('jobPosting') or {}).get('jobPostingId') or job.get('jobPostingId');blocked=[]
  if not isinstance(posting,str) or not posting:blocked.append('No public application posting ID was returned. Check the listing’s application route.')
  if job.get('status') not in ('POSTED','OPEN','PUBLISHED'):blocked.append('The listing is not confirmed open for applications.')
  if any(isinstance(n.get('viewerApplication'),dict) for n in allnodes):blocked.append('Contra returned an existing or pending application. Review it before preparing another.')
  with self.e.connect() as c:prior=c.execute("SELECT status FROM contra_application_actions WHERE json_extract(data,'$.url')=? AND status IN ('Submitted','Submitting','Submission uncertain','Preparing','Prepare uncertain','Preview ready')",(url,)).fetchone()
  if prior:blocked.append('An application action already exists: '+prior['status']+'. Open its saved preview or check Contra before creating another.')
  projects={}
  for tree in porttrees:
   for n in nodes(tree):
    if isinstance(n.get('projects'),list):
     for p in n['projects'][:25]:
      if isinstance(p,dict) and isinstance(p.get('id'),str) and not p.get('isDraft') and p.get('title'):
       projects[p['id']]={'id':p['id'],'title':str(p['title'])[:180],'url':str(p.get('projectUrl') or '')[:1000],'description':str(p.get('contentPlaintext') or p.get('description') or '')[:1200]}
  title=str(job['title'])[:180];company=str((job.get('organization') or {}).get('name') or 'hiring')[:150]
  message=('Hi '+company+' team,\n\nI’m interested in your Canva-to-Google-Slides reporting project. My proposed approach would be to preserve the deck’s layout and visual consistency, check which elements need to remain editable, and review the finished presentation for collaborative use.\n\nBefore confirming scope and turnaround, could you share the slide count, deadline, and how the editable Canva source would be provided? Please also confirm revision expectations and any elements that must remain individually editable.\n\nBest,\nDesmond Glover') if 'canva' in title.lower() else 'Hi '+company+' team,\n\nI’m interested in '+title+'.\n\n[Add your truthful, tailored proposal and any scope questions here.]\n\nBest,\nDesmond Glover'
  data={'url':url,'title':title,'listing_description':text(job.get('description') or job.get('blocknoteDescription') or ''),'jobPostingId':posting,'projects':list(projects.values()),'message':message,'blockers':blocked,'fit_warning':('This listing asks for proven Canva and Google Slides experience. An unrelated CRM or AI project does not establish that. ' if 'canva' in title.lower() else '')+'Check that your selected work actually demonstrates the required skills. Existing portfolio items are not automatically proof of fit.','expires':time.time()+1200,'requirements':'Your application can include a message, work samples and an optional scheduling link. We read these options through Contra’s connection; its website may show additional fields.'}
  if d.get('inspect_only') is True:return {'status':'Inspection only',**data}
  key=secrets.token_hex(16);r={'id':key,'workspace':w,'opportunity_id':o,'chat_id':chat,'status':'Options ready','data':data,'remote_draft_id':'','created':now(),'updated':now()}
  with self.e.connect() as c:c.execute('INSERT INTO contra_application_actions VALUES(?,?,?,?,?,?,?,?,?)',(key,w,o,chat,r['status'],json.dumps(data),'',r['created'],r['updated']))
  return self.view(r)
 def prepare(self,d):
  with self.lock:
   r=self.record(d);data=r['data'];message=str(d.get('message','')).strip();ids=d.get('project_ids',[]);optout=d.get('portfolio_opt_out') is True
   if r['status']=='Preview ready':
    if message!=data['message'] or ids!=data.get('arguments',{}).get('relatedPortfolioProjectIds',[]) or optout!=data.get('portfolio_opt_out',False) or str(d.get('calendar_link','')).strip()!=data.get('arguments',{}).get('calendarLink',''):raise ValueError('Use Edit before sending to prepare a changed version.')
    return self.view(r)
   if r['status']!='Options ready':raise ValueError('This preparation has already been attempted. Check its saved status; no automatic retry is allowed.')
   with self.e.connect() as c:other=c.execute("SELECT id FROM contra_application_actions WHERE id<>? AND json_extract(data,'$.url')=? AND status IN ('Preparing','Prepare uncertain','Preview ready','Submitting','Submission uncertain','Submitted')",(r['id'],data['url'])).fetchone()
   if other:raise ValueError('Another preview or application already exists for this listing. Review it before preparing another.')
   if data['blockers'] or data['expires']<time.time():raise ValueError('Resolve the listing blockers or reload its application details.')
   if d.get('fit_reviewed') is not True:raise ValueError('Review the skills and portfolio warning before preparing.')
   if not 1<=len(message)<=10000 or re.search(r'\[(?:Add|Your|Insert|Hiring|Client)[^\]]*\]',message,re.I) or SECRET.search(message):raise ValueError('Use a complete proposal without placeholders or credentials.')
   if not isinstance(ids,list) or len(ids)>10 or any(not isinstance(i,str) for i in ids):raise ValueError('Choose up to ten portfolio projects.')
   allowed={p['id'] for p in data['projects']}
   if set(ids)-allowed:raise ValueError('Choose only your returned portfolio projects.')
   if ids and optout:raise ValueError('Choose work samples or choose no attachments; do not select both.')
   if not ids and not optout:raise ValueError('Choose relevant portfolio work, or explicitly choose to apply without attachments.')
   args={'jobPostingId':data['jobPostingId'],'message':message}
   if ids:args['relatedPortfolioProjectIds']=list(dict.fromkeys(ids))
   else:args['portfolioAttachmentOptOutConfirmed']=True
   calendar=str(d.get('calendar_link','')).strip()
   data['calendar_link']=calendar
   if calendar:
    p=urlsplit(calendar)
    if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Use a public HTTPS scheduling link without credentials.')
    args['calendarLink']=calendar
   data['arguments']=args;data['message']=message;data['selected_projects']=[p for p in data['projects'] if p['id'] in ids];data['portfolio_opt_out']=not ids and optout;self.save(r,'Preparing',expected='Options ready')
   try:
    parsed=self.body(ContraConnection(self.e).application_tools([('apply_to_job_prepare',args)]));native=next((n for t in parsed for n in nodes(t) if UUID.fullmatch(str(n.get('draftId','')))),None)
    if not native:raise ValueError('Contra did not return a recognizable draft preview. Check Contra before trying preparation again.')
    r['remote_draft_id']=native['draftId'];data['preview']=parsed
    if len(json.dumps(parsed))>100000:raise ValueError('Preview too large for complete review.')
    if SECRET.search(json.dumps(parsed)):raise ValueError('The preview contained unexpected sensitive content and was not retained.')
    data['preview_digest']=hashlib.sha256(json.dumps(parsed,sort_keys=True).encode()).hexdigest();data['expires']=min(data['expires'],time.time()+600)
    for t in parsed:
     for n in nodes(t):
      if isinstance(n.get('expiresAt'),str):
       try:data['expires']=min(data['expires'],datetime.fromisoformat(n['expiresAt'].replace('Z','+00:00')).timestamp())
       except ValueError:pass
    self.save(r,'Preview ready')
   except Exception:
    data.pop('preview',None);self.save(r,'Prepare uncertain');raise ValueError('Preparation could not be confirmed. Nothing was submitted by this step. Check Contra before trying again.') from None
   return self.view(r)
 def current_job(self,r):
  slug=urlsplit(r['data']['url']).path.split('/opportunity/',1)[1]
  parsed=self.body(ContraConnection(self.e).read_tools([('get_job_by_slug',{'slug':slug})]))
  return [n for t in parsed for n in nodes(t)]
 def submit(self,d):
  with self.lock:
   r=self.record(d);data=r['data']
   if r['status']=='Submitted':return self.view(r)
   if r['status']!='Preview ready':raise ValueError('Only a confirmed, unsubmitted preview can be sent. Check existing delivery before any retry.')
   if d.get('approved') is not True or d.get('preview_digest')!=data.get('preview_digest'):raise ValueError('Read and explicitly approve this exact Contra preview first.')
   if data['expires']<time.time():self.save(r,'Expired');raise ValueError('This preview expired. Review Contra before preparing a fresh one.')
   fresh=self.current_job(r)
   if any(isinstance(n.get('viewerApplication'),dict) for n in fresh):
    self.save(r,'Existing application');raise ValueError('Contra already has an application or pending application. Review it before any new submission.')
   if not any(n.get('publicUrl','').split('?',1)[0].rstrip('/')==data['url'] and n.get('status') in ('POSTED','OPEN','PUBLISHED') and ((n.get('jobPosting') or {}).get('jobPostingId') or n.get('jobPostingId'))==data['jobPostingId'] for n in fresh):
    self.save(r,'Expired');raise ValueError('This listing is no longer confirmed open. Nothing was submitted.')
   self.save(r,'Submitting',expected='Preview ready')
   try:
    parsed=self.body(ContraConnection(self.e).application_tools([('apply_to_job_confirm',{'draftId':r['remote_draft_id'],'confirm':True})]))
    verified=self.current_job(r)
    if not any(isinstance(n.get('viewerApplication'),dict) and n['viewerApplication'].get('appliedAt') for n in verified):raise ValueError('Submission result unclear.')
    data['submitted_at']=now();self.save(r,'Submitted')
   except Exception:
    self.save(r,'Submission uncertain');raise ValueError('Submission could not be confirmed. It may have gone through. Check Contra before any new application; nothing will retry automatically.') from None
   return self.view(r)

 def discard(self,d):
  with self.lock:
   r=self.record(d)
   if r['status'] not in ('Options ready','Preview ready','Expired','Restored'):raise ValueError('Check the existing Contra application status before changing it.')
   self.save(r,'Expired');return {'saved':True,'message':'This local preview is retired. No application was withdrawn or submitted.'}
