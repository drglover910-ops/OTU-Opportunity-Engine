"""Owner-requested launch check: read connections and prepare one unsent template."""
import json,os,re,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
BASE='https://dezz-9-10-otu-opportunity-engine.hf.space'
def request(path,data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+os.environ['HF_TOKEN'],'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
report={'checked_at':datetime.now(timezone.utc).isoformat(),'sent_messages':0,'paid_ai_calls':0}
try:
    status=request('/api/status');docs=request('/api/documents');leads=request('/api/opportunities');drafts=request('/api/drafts')
    report.update({'version':status['version'],'gmail_connected':status['gmail'],'ai_configured':status['ai_configured'],'career_documents':len(docs),'application_documents':sum(d['kind']=='resume' for d in docs),'opportunities':len(leads)})
    if status['gmail']:
        try:
            result=request('/api/gmail/sync',{});report['gmail_read_check']='passed';report['new_replies_linked']=result['linked']
        except Exception as e:report['gmail_read_check']='failed: '+type(e).__name__
    candidates=[r for r in leads if r['stage'] in ('New','Researching','Ready to contact')]
    role_terms=r'crm|gohighlevel|highlevel|automation|customer success|customer support|sales|account executive|business development|marketing|customer operations'
    excluded=r'finance|erp|accountant|controller|principal|software engineer|data scientist|architect'
    candidates=[r for r in candidates if re.search(role_terms,r['title'],re.I) and not re.search(excluded,r['title'],re.I)]
    preferred=[r for r in candidates if re.search(r'crm|gohighlevel|highlevel|automation|marketing',r['title'],re.I)]
    report['shortlist']=[{'title':r['title'],'company':r['company'],'url':r['url']} for r in candidates[:5] if r['source'] in ('We Work Remotely','Remotive')]
    if preferred or candidates:
        row=(preferred or candidates)[0]
        existing=next((d for d in drafts if d['opportunity_id']==row['id'] and d['status'] in ('Draft','Approved')),None)
        result=existing or request('/api/draft',{'id':row['id'],'mode':'template'})
        report['review_draft']={'id':result['id'],'opportunity_id':row['id'],'title':row['title'],'company':row['company'],'source':row['source'],'url':row['url'],'mode':'basic template','existing_draft_reused':bool(existing)}
except Exception as e:report['check_error']=type(e).__name__
Path('docs/LAUNCH_CHECK.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
