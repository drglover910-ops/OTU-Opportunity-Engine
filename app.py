"""OTU Opportunity Engine: private, dependency-free Hugging Face Docker app."""
import json, os, sqlite3, urllib.request, urllib.parse, html, re
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import date
VERSION = '0.1.1'
DATA = Path(os.getenv('OTU_DATA_DIR', '/tmp/otu-data')); DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / 'opportunities.sqlite3'
STAGES = ['New', 'Researching', 'Ready to contact', 'Contacted', 'Interview / meeting', 'Offer / contract', 'Won', 'Parked']
def connect():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS opportunities (id INTEGER PRIMARY KEY, company TEXT, title TEXT, url TEXT UNIQUE, category TEXT, stage TEXT DEFAULT "New", contact TEXT DEFAULT "", notes TEXT DEFAULT "", followup TEXT DEFAULT "", created TEXT)')
 return c
connect().close()
def save(d):
 url=d.get('url','').strip()
 if url and urllib.parse.urlparse(url).scheme not in ('https','http'): raise ValueError('Use an https or http opportunity link.')
 title=d.get('title','').strip(); company=d.get('company','').strip()
 if not title or not company: raise ValueError('Add both a company and an opportunity title.')
 with connect() as c:
  c.execute('INSERT OR IGNORE INTO opportunities(company,title,url,category,created) VALUES(?,?,?,?,?)',(company,title,url or None,d.get('category','Contract'),date.today().isoformat()))
def discover():
 request=urllib.request.Request('https://remotive.com/api/remote-jobs?category=sales-business',headers={'User-Agent':'OTUOpportunityEngine/0.1'})
 with urllib.request.urlopen(request,timeout=25) as r: jobs=json.load(r).get('jobs',[])
 count=0
 with connect() as c:
  for j in jobs[:50]:
   cursor=c.execute('INSERT OR IGNORE INTO opportunities(company,title,url,category,created) VALUES(?,?,?,?,?)',(j['company_name'],j['title'],j['url'],'Sales / operations',date.today().isoformat())); count+=cursor.rowcount
 return count
PAGE=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OTU Opportunity Engine</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#07110d;color:#edf9f1;font:16px system-ui}header,main{max-width:1180px;margin:auto;padding:24px}header{border-bottom:1px solid #265c3b}h1{font-size:28px;color:#7fffaa}h2{font-size:20px}p{line-height:1.6;color:#b8d1c1}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px}.panel,.card{background:#102019;border:1px solid #306047;border-radius:12px;padding:20px;margin-bottom:18px}button,.link{display:inline-block;background:#83ffaa;color:#082014;border:0;border-radius:6px;padding:11px 16px;font:inherit;cursor:pointer;text-decoration:none;margin:4px 4px 4px 0}a{color:#8effbb}label{display:block;margin-top:12px}input,select,textarea{width:100%;padding:10px;background:#08150e;color:#edf9f1;border:1px solid #578367;border-radius:6px;font:inherit}textarea{min-height:90px}.muted{color:#b8d1c1;font-size:14px}#status{padding:12px;color:#b2ffce;min-height:44px} .stats{display:flex;flex-wrap:wrap;gap:20px}.stat{font-size:22px}summary{cursor:pointer;color:#9dffc1}footer{padding:20px;text-align:center;color:#b8d1c1}</style>
<header><div class="muted">OTU / OPPORTUNITY ENGINE</div><h1>Your next paid opportunity starts here.</h1><p>Find a good fit. Prepare your approach. Keep the next step visible.</p><div class="stats" id="stats"></div></header><main>
<div id="status" role="status" aria-live="polite"></div><div class="grid"><section class="panel"><h2>1 · Find opportunities</h2><p>Start with Contra contracts. Save promising projects to your board. The live feed adds remote sales and business jobs.</p><a class="link" href="https://contra.com/opportunities" target="_blank" rel="noopener">Open Contra</a><a href="https://www.peopleperhour.com/freelance-jobs" target="_blank" rel="noopener">PeoplePerHour</a><button onclick="discover()">Check live job feed</button><p class="muted">Contra is a manual connection today. This app cannot submit proposals or access your account yet. Remotive listings may have location restrictions; check each listing.</p></section>
<section class="panel"><h2>2 · Save a lead</h2><form id="add"><label>Company or client<input name="company" required maxlength="200"></label><label>Opportunity title<input name="title" required maxlength="250"></label><label>Listing link<input name="url" type="url"></label><label>Best fit<select name="category"><option>CRM / GoHighLevel</option><option>AI / business automation</option><option>Sales / operations</option><option>Coaching</option><option>Contract</option></select></label><button>Save opportunity</button></form></section></div>
<section class="panel"><h2>3 · Work your board</h2><label>Filter by stage<select id="filter" onchange="render()"><option>All</option></select></label><p class="muted">A draft is not a sent message. Update the stage after you complete the action.</p></section><div id="board" class="grid"></div>
<section class="panel"><h2>Connections & résumé library</h2><p>Use a private Hugging Face Space. Put career files in private storage, outside the source repository. Match CRM projects to the GHL résumé, sales to the AI-updated sales résumé, and coaching to the coaching library.</p><p class="muted">Email: not connected · Contra account: not connected · AI writing: not connected. Drafts below use a professional template. No applications or messages are sent automatically.</p></section></main><footer>OTU Opportunity Engine · v0.1.1 · Small steps. Clear records. Real outcomes.</footer>
<script>
let rows=[];const stages=STAGES_JSON;const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path,data){let r=await fetch(path,{method:data?'POST':'GET',headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});let result=await r.json();if(!r.ok)throw Error(result.error);return result}
function status(s){document.getElementById('status').textContent=s}
async function load(){try{rows=await api('/api/opportunities');render()}catch(e){status(e.message)}}
function render(){let f=document.getElementById('filter').value;let today=new Date().toLocaleDateString('en-CA');document.getElementById('stats').innerHTML=`<span class="stat">${rows.length} opportunities</span><span class="stat">${rows.filter(r=>r.followup&&r.followup<=today&&!['Won','Parked'].includes(r.stage)).length} follow-ups due</span><span class="stat">${rows.filter(r=>r.stage==='Won').length} wins</span>`;
 document.getElementById('board').innerHTML=rows.filter(r=>f==='All'||r.stage===f).map(r=>`<article class="card"><div class="muted">${esc(r.category)}</div><h2>${esc(r.title)}</h2><p>${esc(r.company)}</p>${r.url?`<a href="${esc(r.url)}" target="_blank" rel="noopener">Read original listing</a>`:''}<label>Stage<select id="stage-${r.id}">${stages.map(s=>`<option ${s===r.stage?'selected':''}>${esc(s)}</option>`).join('')}</select></label><label>Contact email<input id="contact-${r.id}" type="email" value="${esc(r.contact)}"></label><label>Follow-up date<input id="followup-${r.id}" type="date" value="${esc(r.followup)}"></label><label>Private notes<textarea id="notes-${r.id}">${esc(r.notes)}</textarea></label><button onclick="update(${r.id})">Save changes</button><button onclick="draft(${r.id})">Prepare outreach</button><details id="draftbox-${r.id}" hidden><summary>Review your draft</summary><pre id="draft-${r.id}" style="white-space:pre-wrap"></pre><p class="muted">Attach the correct résumé, verify the recipient, and check previous outreach before sending.</p><a id="mail-${r.id}">Open email app</a></details></article>`).join('')||'<p>No opportunities here yet. Open Contra or check the live feed to get started.</p>'}
async function update(id){try{await api('/api/update',{id,stage:document.getElementById('stage-'+id).value,contact:document.getElementById('contact-'+id).value,followup:document.getElementById('followup-'+id).value,notes:document.getElementById('notes-'+id).value});status('Changes saved.');await load()}catch(e){status(e.message)}}
function draft(id){let r=rows.find(x=>x.id===id);let subject='Interest in '+r.title;let body=`Hello,\n\nI’m interested in your ${r.title} opportunity. My background includes ${r.category==='Coaching'?'coaching and youth program leadership':r.category.includes('CRM')?'GoHighLevel, CRM workflows, and customer follow-up':r.category.includes('AI')?'AI-assisted development and business workflow design':'sales, customer operations, and organized follow-up'}. I’d welcome a conversation about what you need and how I can contribute.\n\nBest,\nDesmond Glover`;document.getElementById('draft-'+id).textContent=subject+'\n\n'+body;let box=document.getElementById('draftbox-'+id);box.hidden=false;box.open=true;document.getElementById('mail-'+id).href='mailto:'+encodeURIComponent(document.getElementById('contact-'+id).value)+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body)}
async function discover(){status('Checking the live feed…');try{let r=await api('/api/discover',{});status(`Added ${r.added} new opportunities. Existing links were skipped.`);await load()}catch(e){status('Live feed unavailable: '+e.message+' You can still save Contra leads manually.')}}
document.getElementById('add').onsubmit=async e=>{e.preventDefault();try{await api('/api/add',Object.fromEntries(new FormData(e.target)));e.target.reset();status('Lead saved. Duplicate listing links are skipped.');await load()}catch(e){status(e.message)}};document.getElementById('filter').innerHTML+ ='';
load();</script></html>'''.replace('STAGES_JSON',json.dumps(STAGES)).replace("document.getElementById('filter').innerHTML+ ='';", "document.getElementById('filter').innerHTML+=stages.map(s=>'<option>'+esc(s)+'</option>').join('');")
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def reply(self,value,code=200):
  payload=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
 def do_GET(self):
  if self.path=='/health': return self.reply({'status':'ok', 'version': VERSION})
  if self.path=='/api/opportunities':
   with connect() as c: return self.reply([dict(r) for r in c.execute('SELECT * FROM opportunities ORDER BY id DESC')])
  if self.path!='/':return self.reply({'error':'Not found'},404)
  body=PAGE.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(body)
 def do_POST(self):
  try:
   if self.headers.get('Origin') and urllib.parse.urlparse(self.headers['Origin']).netloc!=self.headers.get('Host'):return self.reply({'error':'Cross-origin request refused'},403)
   length=int(self.headers.get('Content-Length',0))
   if length>20000:raise ValueError('Request too large')
   d=json.loads(self.rfile.read(length))
   if self.path=='/api/add':save(d);return self.reply({'saved':True})
   if self.path=='/api/discover':return self.reply({'added':discover()})
   if self.path=='/api/update':
    if d['stage'] not in STAGES:raise ValueError('Unknown stage')
    with connect() as c:c.execute('UPDATE opportunities SET stage=?,contact=?,notes=?,followup=? WHERE id=?',(d['stage'],d['contact'],d['notes'],d['followup'],int(d['id'])))
    return self.reply({'saved':True})
   return self.reply({'error':'Not found'},404)
  except Exception as e:self.reply({'error':str(e)},400)
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',int(os.getenv('PORT','7860'))),Handler).serve_forever()
