"""Bounded owner-requested research. No model planner, writes or arbitrary browsing."""
import hashlib,json,re,time
from datetime import datetime,timezone
from urllib.parse import urlsplit
from knowledge_store import words,SECRET

NOISE=set('find search research check look latest new current saved available opportunities opportunity jobs job work contra please show for suited suitable best match matching experience qualifications skills help today now paid freelance available'.split())

def stamp():return datetime.now(timezone.utc).isoformat()

def requested(d):
 mode=d.get('mode') or 'advice'
 if mode=='research':return True
 if mode!='advice':return False
 text=str(d.get('text','')).strip().lower()
 text=re.sub(r'^(?:please\s+|(?:can|could|would) you\s+)+','',text)
 return bool(re.match(r'^(?:find|search|research|look up|check|refresh)\b',text) and re.search(r'\b(?:contra|jobs?|opportunit\w*|challenges?|contests?|applied|upwork|linkedin|indeed)\b',text))

def safe_contra_url(value):
 try:
  p=urlsplit(str(value));return p.scheme=='https' and p.hostname in ('contra.com','www.contra.com') and not p.username and not p.password and p.port in (None,443)
 except ValueError:return False

def nodes(value,depth=0):
 if depth>10:return
 if isinstance(value,dict):
  yield value
  for v in list(value.values())[:80]:yield from nodes(v,depth+1)
 elif isinstance(value,list):
  for v in value[:100]:yield from nodes(v,depth+1)

def text(value):
 if isinstance(value,str):return value[:4000]
 return ' '.join(n['text'] for n in nodes(value) if isinstance(n.get('text'),str))[:4000]

def extract(body,kind):
 if body.get('isError'):raise ValueError('Contra did not allow this read.')
 data=body.get('structuredContent');parsed=[]
 if data is not None:parsed=[data]
 else:
  for part in body.get('content',[])[:5]:
   if part.get('type')=='text':
    try:parsed.append(json.loads(part.get('text','')[:200000]))
    except (ValueError,TypeError):continue
 rows={};recognized=False
 for tree in parsed:
  for n in nodes(tree):
   if any(k in n for k in ('entries','jobs','challenges','jobId','job','hasNextPage')):recognized=True
   job=n.get('job') if isinstance(n.get('job'),dict) else n
   url=job.get('publicUrl') or job.get('challengeUrl') or job.get('url');title=job.get('title') or job.get('name')
   if not isinstance(title,str) or not safe_contra_url(url):continue
   item={'title':title[:180],'url':url,'kind':kind,'description':text(job.get('description') or job.get('blocknoteDescription') or ''),'pay':text(job.get('budget')) or json.dumps(job.get('budget') or job.get('prize') or {},ensure_ascii=False)[:300],'deadline':str(job.get('submissionsDeadline') or job.get('deadline') or '')[:100],'status':str(job.get('status') or 'not supplied')[:80],'location':str(job.get('location') or job.get('locationRequirement') or '')[:200],'posted_at':str(job.get('publishedAt') or job.get('createdAt') or '')[:100]}
   applied=n.get('visitorDidApply',job.get('visitorDidApply'))
   if isinstance(applied,bool):item['applied']=applied
   prior=rows.get(url)
   if not prior or len(item['description'])>len(prior['description']):rows[url]=item
   elif 'applied' in item:prior['applied']=item['applied']
 return list(rows.values())[:5],recognized

class Research:
 def __init__(self,e):self.e=e
 def run(self,d,progress=None):
  w,o=self.e.conversation_scope(d);chat=self.e.chat_key(d,w,o);question=str(d.get('text',''));terms=set(words(question))-NOISE
  if SECRET.search(question):raise ValueError('Remove credentials from the research request. No platform check was started.')
  explicit_contra=bool(re.search(r'\bcontra\b',question,re.I));other=None if explicit_contra else next((p for p in ('upwork','linkedin','indeed','peopleperhour','remotive','we work remotely') if p in question.lower()),None)
  report={'checked_at':stamp(),'phase':'saved','checks':[],'items':[],'limits':'At most five returned records; one Contra read; no submissions or account changes.'}
  def emit():
   if progress:progress({k:v for k,v in report.items() if k!='items'})
  emit();ranked=[]
  for row in self.e.list():
   if (w!='assistant' and self.e.workspace_key(row)!=w) or (o and row['id']!=o):continue
   if other and other.replace(' ','') not in str(row.get('source','')).lower().replace(' ',''):continue
   if explicit_contra and self.e.workspace_key(row)!='contra' and str(row.get('source','')).lower()!='contra':continue
   score=len(terms&set(words(row['title']+' '+row.get('company','')+' '+row.get('description',''))))
   if terms and not score and not o:continue
   ranked.append((score,row['id'],row))
  ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
  saved=[{'title':r['company']+' · '+r['title'],'url':r.get('url') or '','kind':'saved_opportunity','description':str(r.get('description') or '')[:1800],'pay':r.get('pay',''),'deadline':r.get('deadline',''),'status':r['stage'],'saved_at':r['created']} for _,_,r in ranked[:3]]
  report['items']=saved;report['checks'].append({'tool':'saved_opportunities','status':'complete','count':len(saved),'basis':'Saved records only; freshness and application outcome are not verified.'})
  lower=question.lower()
  contra=w=='contra' or bool(re.search(r'\bcontra\b',lower))
  if other:
   report['checks'].append({'tool':'live_platform','status':'unavailable','message':f'No live {other} research connector is available in chat. Saved records remain restricted to this conversation’s workspace.'})
  elif not contra:
   report['checks'].append({'tool':'live_platform','status':'saved_only','message':'Only saved opportunities were searched. Mention Contra or use its workspace for supported live reads.'})
  elif w not in ('assistant','contra'):
   report['checks'].append({'tool':'contra','status':'unavailable','message':'Open the Contra workspace or My assistant to run a Contra read; this workspace was not crossed.'})
  elif re.search(r'\b(profile|portfolio|services|inbox|messages)\b',lower) and not re.search(r'\b(jobs?|opportunit\w*|contests?|challenges?)\b',lower):
   report['checks'].append({'tool':'contra','status':'unsupported','message':'Chat research currently supports jobs and active challenge listings, not profile audits or private messages.'})
  elif not self.e.setting('contra_tokens'):
   report['checks'].append({'tool':'contra','status':'unavailable','message':'Contra is not connected. Connect it in Connections; saved results are still available.'})
  else:
   url=next((u.rstrip('.,);') for u in re.findall(r'https?://[^\s<>"\']+',question) if safe_contra_url(u.rstrip('.,);'))),None)
   if not url and o:
    candidate=self.e.get(o).get('url','');url=candidate if safe_contra_url(candidate) else None
   slug=urlsplit(url).path.split('/opportunity/',1)[1].rstrip('/') if url and '/opportunity/' in urlsplit(url).path else None
   challenge=bool(re.search(r'\b(challenges?|contests?|prizes?)\b',lower))
   query=' '.join(t for t in words(re.sub(r'https?://\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]+','',question)) if t not in NOISE and not t.isdigit())[:120]
   if slug and re.fullmatch(r'[A-Za-z0-9_-]{1,180}',slug):call=('get_job_by_slug',{'slug':slug});kind='contra_job'
   elif challenge:call=('list_active_challenges',{'limit':5});kind='contra_challenge'
   else:call=('list_job_feed',{'preset':'ALL','search':query,'first':5});kind='contra_job'
   key=hashlib.sha256(json.dumps([w,o,chat,call],sort_keys=True).encode()).hexdigest();cache=self.e.setting('chat_research_cache',{})
   cached=cache.get(key);report['phase']='contra';emit()
   if cached and cached.get('expires',0)>time.time() and not re.search(r'\brefresh\b|fresh check|check live|check again',question,re.I):
    report['checks'].append({**cached['check'],'status':'cached','message':'Reused a read less than ten minutes old; this was not a new platform check.'});report['items']=cached['items']+saved
   else:
    try:
     from contra_mcp import ContraConnection
     bodies=ContraConnection(self.e).read_tools([call]);body=next(iter(bodies.values()),{'isError':True})
     items,recognized=extract(body,kind)
     check={'tool':call[0],'status':'live' if items else 'empty' if recognized else 'unrecognized','count':len(items),'checked_at':stamp(),'message':'Read-only result; returned fields only. Full eligibility, rights and current terms may still require checking.'}
     if not items and not recognized:check['message']='Contra returned no usable listing structure. This does not establish that no opportunities exist.'
     report['checks'].append(check);report['items']=items+saved
     cache={k:v for k,v in cache.items() if v.get('expires',0)>time.time()};cache[key]={'expires':time.time()+600,'check':check,'items':items};self.e.set_setting('chat_research_cache',dict(list(cache.items())[-10:]))
    except Exception:
     report['checks'].append({'tool':call[0],'status':'unavailable','message':'Contra could not complete this read. Check Connections before retrying. Saved results do not become live results.'})
  unique={}
  for item in report['items']:unique.setdefault(item['url'] or item['title'],item)
  report['items']=list(unique.values())[:5];report['phase']='ready';emit();return report

 @staticmethod
 def sources(report,local):
  when=report['checked_at'];receipt='\n'.join(c['tool']+': '+c['status']+'. '+c.get('message',c.get('basis','')) for c in report['checks'])
  rows=[{'label':'Research checks','kind':'research_receipt','authority':'App execution receipt, not independent verification of listing claims','recorded_at':when,'excerpt':receipt[:900]}]
  for item in report['items'][:2]:
   excerpt=json.dumps({k:item[k] for k in ('pay','deadline','status','applied','location','posted_at') if k in item},ensure_ascii=False)+'\n'+item['description'][:550]
   rows.append({'label':item['title'],'kind':item['kind'],'authority':('Saved record; not a fresh platform check' if item['kind']=='saved_opportunity' else 'Contra returned fields; advertised terms are not agreements; full guidelines may be absent'),'recorded_at':item.get('saved_at') or next((c.get('checked_at') for c in reversed(report['checks']) if c.get('checked_at')),when),'url':item['url'],'excerpt':excerpt[:900]})
  rows+=local[:1];out=[]
  for row in rows:
   row=dict(row);row['digest']=row.get('digest') or hashlib.sha256(row['excerpt'].encode()).hexdigest();row['offset']=row.get('offset',0);row['citation']='S'+str(len(out)+1)
   if len(json.dumps(out+[row],ensure_ascii=False).encode())<=4800:out.append(row)
  return out

 @staticmethod
 def summary(report):
  lines=['Research results — direct summary of returned records.']
  if report.get('writing_status'):lines.append(report['writing_status']['message'])
  for c in report['checks']:lines.append(c['tool']+': '+c['status']+'. '+c.get('message',c.get('basis','')))
  for item in report['items'][:2]:lines.append(item['title']+'\n'+item['url']+'\nRecorded status: '+item['status']+'. '+item['description'][:250])
  if not report['items']:lines.append('No usable records were returned in these bounded checks; broader availability remains unknown.')
  return '\n\n'.join(lines)+'\n\nNothing was submitted or changed on the platform.'
