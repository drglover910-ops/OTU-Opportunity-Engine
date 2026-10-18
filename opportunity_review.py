"""Local opportunity selection and pre-draft review. No planner, submissions or purchases."""
import re
from knowledge_store import words
from research_tools import safe_contra_url

NOISE=set('prepare final review application proposal include slide count deadline editable source question questions submit yet draft write opportunity requirement guidelines know need check please isis want ready make send response scope approve approved for'.split())
GUIDE={'label':'Contra: Applying to jobs','kind':'official_platform_guide','authority':'Official Help Center reviewed October 18, 2026; not a live account eligibility check','recorded_at':'2026-10-18','url':'https://help.contra.com/en/articles/9322973-applying-to-jobs-on-contra','excerpt':'Contra’s official guide says to browse the job feed, filter by tools, skills and budgets, and use the listing’s Apply option. It does not establish that this account is eligible for a particular job or that an application was sent. Any form fields, fees or verification shown at submission still need checking.'}

def intended(d):
 if (d.get('mode') or 'advice')!='advice':return False
 t=re.sub(r'^(?:hey\s+|hi\s+)?isis\b[\s,:!—–-]*','',str(d.get('text','')).strip(),flags=re.I)
 t=re.sub(r'^(?:please\s+|(?:can|could|would) you\s+)+','',t,flags=re.I)
 return bool(re.match(r'^(?:prepare|draft|write|review|check|research|examine)\b',t,re.I) and re.search(r'\b(?:application|proposal|requirements?|guidelines?|eligibility|listing)\b',t,re.I))

def resolve(e,d,context):
 w,o=e.conversation_scope(d);question=str(d.get('text',''));candidates={}
 def add(row,kind):
  url=str(row.get('url') or '').split('?',1)[0].rstrip('/')
  if not safe_contra_url(url) or '/opportunity/' not in url:return
  item={'url':url,'title':str(row.get('title') or 'Linked opportunity')[:180],'company':str(row.get('company') or '')[:150],'basis':kind}
  if url not in candidates or kind=='selected':candidates[url]=item
 if w in ('assistant','contra'):
  from contra_mcp import ContraConnection
  for row in ContraConnection(e).inventory_details().get('public_opportunities',[]):add(row,'saved platform snapshot')
 for row in e.list():
  if w=='assistant' or e.workspace_key(row)==w:add(row,'saved opportunity')
 for request in reversed(context.get('requests',[])):
  if request.get('status')=='complete':
   for row in (request.get('result',{}).get('research') or {}).get('items',[]):add(row,'same-conversation research')
 selected=None
 if o:
  selected=e.get(o);add(selected,'selected')
 urls=[u.rstrip('.,);') for u in re.findall(r'https?://[^\s<>"\']+',question) if safe_contra_url(u.rstrip('.,);')) and '/opportunity/' in u]
 target=None
 if urls:
  url=urls[0].split('?',1)[0].rstrip('/');target=candidates.get(url,{'url':url,'title':'Linked opportunity','company':'','basis':'owner-provided URL'})
 else:
  terms=set(words(question))-NOISE
  ranked=[(len(terms & (set(words(c['title']+' '+c['company']))-NOISE)),c) for c in candidates.values()]
  ranked=sorted([r for r in ranked if r[0]],key=lambda r:r[0],reverse=True)
  if ranked and (len(ranked)==1 or ranked[0][0]>ranked[1][0]):target=ranked[0][1]
  elif ranked:return {'status':'ambiguous','message':'More than one listing matches. Paste the exact opportunity link so I review the right requirements before drafting.'}
  elif selected:target=candidates.get((selected.get('url') or '').split('?',1)[0].rstrip('/'))
  else:
   target=next((r['result']['focus'] for r in context.get('requests',[]) if r.get('status')=='complete' and (r.get('result',{}).get('focus') or {}).get('status')=='ready'),None)
 if not target:return {'status':'missing','message':'Paste the exact Contra opportunity link or open its opportunity conversation. I need its requirements before preparing an application.'}
 if selected and target['url']!=(selected.get('url') or '').split('?',1)[0].rstrip('/'):
  return {'status':'conflict','message':'This conversation belongs to '+selected['title']+'. The requested listing is '+target['title']+'. Open the matching opportunity conversation or the general Contra conversation before drafting; existing work stays in place.'}
 excluded=[]
 for c in candidates.values():
  if c['url']!=target['url']:
   for label in (c['title'],c['company']):
    if len(label)>=5 and label.lower() not in (target['title']+' '+target['company']).lower():excluded.append(label)
 return {**target,'status':'ready','excluded_labels':list(dict.fromkeys(excluded))[:100]}

def review(focus,report):
 items=[i for i in report['items'] if i['url'].split('?',1)[0].rstrip('/')==focus['url'] and i['kind']=='contra_job']
 item=items[0] if items else None
 if item:focus['title']=item['title'];focus['company']=item.get('company') or focus['company']
 return {'status':'listing_text_available' if item and item['description'].strip() else 'needs_source','title':focus['title'],'url':focus['url'],'listing_text':item['description'] if item else '', 'text_scope':'Returned listing excerpt, limited to 4,000 characters. Linked pages and files have not been read by this tool.','checklist':['Exact deliverable and file format','Application instructions and requested portfolio/evidence','Named tools, accounts and access permissions','Fees, subscriptions or purchases explicitly required','Deadline, timezone, eligibility and availability','Rights, confidentiality, revisions and acceptance criteria','Missing details and the next owner-approved step'],'platform_guide':GUIDE,'rule':'Separate listing facts, platform guidance, your recommended workflow and unknowns. Do not invent requirements, claim unread linked pages were reviewed, or register/buy/submit anything. An application draft may ask about missing scope; do not promise delivery or proven skills absent evidence.'}

def wrong_identity(answer,focus):
 return any(label.lower() in answer.lower() for label in focus.get('excluded_labels',[]))
