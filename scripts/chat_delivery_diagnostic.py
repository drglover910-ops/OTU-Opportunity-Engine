"""Read recent delivery metadata; never retain prompts, answers, titles or credentials."""
import hashlib,re
from urllib.parse import urlencode

def diagnose(request,threads):
 result={'scope':'Recent Contra/My assistant conversation delivery metadata only; no messages sent or AI calls.','conversations':[]}
 for thread in [t for t in threads if t['workspace'] in ('contra','assistant')][:8]:
  scope={k:thread[k] for k in ('workspace','opportunity_id') if thread.get(k) is not None}
  if thread.get('id'):scope['chat_id']=thread['id']
  key=hashlib.sha256(repr(sorted(scope.items())).encode()).hexdigest()[:12]
  try:
   conversation=request('/api/conversation?'+urlencode(scope));notes=conversation.get('notes',[]);requests=conversation.get('requests',[])
   row={'scope_digest':key,'workspace':thread['workspace'],'note_count':len(notes),'requests':[]}
   for item in requests[:3]:
    payload=item.get('payload',{});answer=item.get('result',{}).get('answer','');research=item.get('result',{}).get('research') or {}
    prompt=re.sub(r'[^a-z0-9 ]','',str(payload.get('text','')).lower()).strip()
    row['requests'].append({'created':item.get('created'),'updated':item.get('updated'),'status':item.get('status'),'mode':payload.get('mode'),'ai_used':item.get('result',{}).get('ai_used'),'writing_status':{k:v for k,v in (item.get('result',{}).get('writing_status') or {}).items() if k in ('status','reason')},'matches_test_prompt':prompt in ('isis find contra gohighlevel jobs','find contra gohighlevel jobs'),'answer_format':'older_research_summary' if answer.startswith('Research results — direct summary') else 'research_check_summary' if answer.startswith('Research check:') else 'other','answer_note_present':any(n.get('id')==item.get('assistant_note_id') for n in notes) if item.get('assistant_note_id') else False,'research_checked_at':research.get('checked_at'),'checks':[{k:c[k] for k in ('tool','status','count','checked_at','broader_feed','accessLimitedFeed') if k in c} for c in research.get('checks',[])]})
   result['conversations'].append(row)
  except Exception:result['conversations'].append({'scope_digest':key,'workspace':thread['workspace'],'status':'read_unavailable'})
 return result
