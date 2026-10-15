"""Prepare an owner-review draft on our private bot only. Never send, approve, or apply."""
import json,os,urllib.request
from pathlib import Path
BASE='https://dezz-9-10-otu-opportunity-engine.hf.space'
HEADERS={'Authorization':'Bearer '+os.environ['HF_TOKEN'],'Content-Type':'application/json'}
def request(path,data=None):
 req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
url='https://contra.com/opportunity/FOUsee7N-social-media-content-manager'
summary=request('/api/contra/summary');item=next((x for x in summary['public_opportunities'] if x['url']==url),None)
report={'version':'1.0','actions':'Private preparation only; no paid inference, approvals, messages or applications.'}
if not item or not item.get('description'):raise SystemExit('No source requirements found; do not fabricate an application.')
lead=request('/api/add',{'company':'VIS World','title':item['title'],'url':url,'source':'Contra','workspace':'contra','category':'Sales / operations','description':item['description'],'pay':'Listed USD $25/hour; estimated 2 hours. Confirm frequency, scope and terms.'})
packages=request('/api/packages');existing=next((p for p in packages if p['opportunity_id']==lead['id']),None)
if existing:report['review_package']='existing package preserved; no owner edits overwritten'
else:
 package=request('/api/package',{'id':lead['id']})
 drafts=request('/api/drafts');draft=next(d for d in drafts if d['id']==package['draft_id'])
 body='''Hi VIS World team,

Miami VIS brings together my background in sports coaching, program leadership, and digital marketing. I’ve coached since 2008 and also work with content planning, customer communication, CRM systems, and AI-assisted workflows.

I’d start by reviewing your brand guidelines and supplied assets, then propose a weekly calendar, captions, and approval process that keep the franchise’s voice consistent. I would research the relevant basketball and WNBA conversation rather than assume the tone you want.

Could you confirm the channels, weekly post volume, and whether the estimated two hours is weekly or a one-time allocation?

Best regards,
Desmond Glover'''
 request('/api/draft/edit',{'id':draft['id'],'recipient':draft['recipient'],'subject':'Social Media Content Manager — Desmond Glover','body':body,'attachments':json.loads(draft['attachments'])})
 request('/api/conversation/note',{'workspace':'contra','opportunity_id':lead['id'],'text':'Recommendation: Consider / strong adjacent fit. Source listing: VIS World supplies assets and wants weekly calendar, captions, scheduling and basketball/WNBA cultural fluency. Sports coaching is supported; basketball/WNBA specialist expertise is not claimed. Budget lists USD $25/hour and estimated 2 hours; frequency, total scope, deadline, eligibility, entry cost and application requirements still need confirmation. Proposal, master-based résumé and cover letter prepared for owner review. Nothing submitted. Next: review materials, then approve an inquiry/application only after checking those terms. Use original Contra URL → Apply, inspect required fields/attachments → review exact submission → submit only if approved → confirm Contra Applied status. Never mark Paid from the advertised budget.'})
 report['review_package']='resume, cover letter and tailored unsent proposal prepared';report['document_checks']=package['checks']
report['geekyants_application_recorded']=summary.get('geekyants_application_recorded',False)
Path('docs/CONTRA_REVIEW_PREPARATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
