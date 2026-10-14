"""Run owner-authorized history review. Commit only redacted analytical summaries."""
import os,json,time,re,urllib.request
from pathlib import Path
BASE='https://dezz-9-10-otu-opportunity-engine.hf.space'
def request(path,data=None):
 req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+os.environ['HF_TOKEN'],'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def redact(text):
 if re.search(r'password|secret|api.?key|token',text,re.I):return '[sensitive technical line omitted]'
 text=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[email omitted]',text)
 text=re.sub(r'\+?\d[\d ().-]{7,}\d','[phone omitted]',text)
 text=re.sub(r'\$[\d,.]+','[amount]',text)
 return text[:400]
report={'sent_messages':0,'paid_ai_calls':0,'private_message_storage':'Hugging Face private database only'}
try:
 expected=Path('VERSION').read_text().strip()
 for _ in range(30):
  try:
   if request('/health').get('version')==expected:break
  except Exception:pass
  time.sleep(10)
 else:raise RuntimeError('Deployment not ready')
 request('/api/gmail/history',{})
 for _ in range(180):
  status=request('/api/status');study=status.get('history_study',{})
  if study.get('status') in ('complete','failed'):break
  time.sleep(10)
 report['study']=study
 style=status.get('outreach_style',{});report['style']={k:v for k,v in style.items() if k!='examples'};report['professional_outreach_examples']=[redact(x) for x in style.get('examples',[])[:8]]
 cases=request('/api/email-cases');report['cases_imported']=len(cases)
 report['case_overview']=[{'company':c['company'],'status':c['summary']['status'],'sent':c['summary']['sent'],'human_replies':c['summary']['human_replies'],'latest_date':c['summary']['latest_date'],'next_context':c['summary']['relationship'],'paid_outcome_verified':False} for c in cases[:25]]
 report['buffalo_stallions']=[{'status':c['summary']['status'],'sent':c['summary']['sent'],'human_replies':c['summary']['human_replies'],'evidence':[redact(x) for x in c['summary'].get('evidence',[])[:4]]} for c in cases if c['company']=='Buffalo Stallions']
except Exception as e:report['error']=type(e).__name__
Path('docs/MAIL_STUDY_SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
