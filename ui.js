'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stages=['New','Researching','Ready to contact','Contacted','Interview / meeting','Offer / contract','Won','Parked'];
let leads=[],documents=[],drafts=[],history=[],messages=[],state={};
function notice(message,error=false){$('status').textContent=message;$('status').classList.toggle('warning',error)}
async function api(path,data){const r=await fetch(path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:data===undefined?undefined:JSON.stringify(data)});const value=await r.json();if(!r.ok)throw Error(value.error||'Request failed');return value}
async function run(task,success){try{const r=await task();if(success)notice(typeof success==='function'?success(r):success);await refresh();return r}catch(e){notice(e.message,true)}}
function tab(name){document.querySelectorAll('.tab').forEach(s=>s.hidden=s.id!==name);document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name))}
function formatDate(s){return s?new Date(s).toLocaleString():''}
function localDate(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function option(value,current){return `<option ${value===current?'selected':''}>${esc(value)}</option>`}
function empty(text){return `<p class="small">${esc(text)}</p>`}
async function refresh(){
 [state,leads,documents,drafts,history,messages]=await Promise.all(['/api/status','/api/opportunities','/api/documents','/api/drafts','/api/history','/api/messages'].map(p=>api(p)));
 $('version').textContent='v'+state.version;$('footer-version').textContent='v'+state.version;
 $('connection-summary').textContent=`Storage: ${state.storage.mount_detected?'mounted':'check needed'} · Gmail: ${state.gmail?'connected':'not connected'} · AI: ${state.ai_configured?'configured':'not connected'}`;
 renderToday();renderBoard();renderDrafts();renderLibrary();renderActivity();renderSettings();
 const scan=state.last_discovery;$('scan-info').textContent=scan.finished?`Last check: ${formatDate(scan.finished)}. ${scan.added||0} added. ${(scan.errors||[]).length?'Some sources failed; live discovery is not fully verified.':''}`:'No live-source check completed yet.';
}
function renderToday(){
 const due=leads.filter(l=>l.followup&&l.followup<=localDate()&&!['Won','Parked'].includes(l.stage));
 const replies=messages.length;const approvals=drafts.filter(d=>d.status==='Draft').length;
 $('stats').innerHTML=[[leads.length,'Opportunities'],[due.length,'Follow-ups due'],[approvals,'Drafts to review'],[leads.filter(l=>l.stage==='Won').length,'Wins']].map(([n,label])=>`<div><strong>${n}</strong>${label}</div>`).join('');
 const todos=[];
 if(!state.storage.mount_detected)todos.push('Connect storage or download a backup before restarting.');
 if(!documents.length)todos.push('Import your master archive and designed résumés in Career library.');
 if(!leads.length)todos.push('Open Contra and save your first project, or check the live feed.');
 if(due.length)todos.push(`${due.length} follow-ups need attention on your board.`);
 if(approvals)todos.push(`${approvals} drafts are waiting for your review.`);
 if(replies)todos.push(`${replies} saved reply records are available under Activity & replies.`);
 $('todos').innerHTML=todos.map(t=>`<div class="row">${esc(t)}</div>`).join('')||empty('Choose a promising lead and prepare its next step.');
 $('best').innerHTML=leads.filter(l=>['New','Researching','Ready to contact'].includes(l.stage)).slice(0,4).map(l=>`<div class="row"><div><strong>${esc(l.title)}</strong><p class="small">${esc(l.company)} · Fit ${l.fit.score}/100</p></div><button class="secondary" data-action="board">Review board</button></div>`).join('')||empty('Your best fits will appear here after you save leads.');
 $('storage-warning').textContent=state.storage.restart_verified?'Restart verification has been recorded. Keep a private backup before major changes.':state.storage.message;
}
function renderBoard(){
 const query=$('search').value.toLowerCase();const stage=$('stage-filter').value;const category=$('category-filter').value;
 const rows=leads.filter(l=>(stage==='All'||l.stage===stage)&&(category==='All'||l.category===category)&&`${l.title} ${l.company} ${l.description}`.toLowerCase().includes(query));
 $('board-items').innerHTML=rows.map(l=>`<article class="card"><span class="badge">Fit ${l.fit.score}/100</span><span class="badge">${esc(l.source)}</span><h2>${esc(l.title)}</h2><p>${esc(l.company)} · ${esc(l.category)}</p><p class="small">${esc(l.fit.reasons.join(' · '))}</p>${l.fit.warnings.map(w=>`<p class="small warning">${esc(w)}</p>`).join('')}<p>${esc(l.pay||'Pay unknown')}<br><span class="small">${esc(l.location||'Location not provided')}</span></p>${l.url?`<a href="${esc(l.url)}" target="_blank" rel="noopener">Read original listing</a>`:''}
 <details><summary>Details and next step</summary><label>Stage<select id="stage-${l.id}">${stages.map(s=>option(s,l.stage)).join('')}</select></label><label>Relationship<select id="relationship-${l.id}">${['New prospect','Requested paperwork','Follow-up'].map(s=>option(s,l.relationship||'New prospect')).join('')}</select></label><label>Contact email<input id="contact-${l.id}" type="email" value="${esc(l.contact)}"></label><div class="grid"><label>Follow-up<input id="followup-${l.id}" type="date" value="${esc(l.followup)}"></label><label>Application deadline<input id="deadline-${l.id}" type="date" value="${esc(l.deadline)}"></label></div><label>Requirements<textarea id="description-${l.id}" rows="5">${esc(l.description)}</textarea></label><label>Private notes<textarea id="notes-${l.id}">${esc(l.notes)}</textarea></label><label>Outcome / payment notes<input id="outcome-${l.id}" value="${esc(l.outcome)}" placeholder="Record only actual outcomes"></label><button data-action="update" data-id="${l.id}">Save changes</button></details>
 <button data-action="draft" data-id="${l.id}">Prepare template</button><button class="secondary" data-action="ai" data-id="${l.id}" ${!state.ai_configured?'disabled':''}>Tailor with AI</button><p class="small">Prepare a draft from saved details. Save edits first. AI uses selected private career text.</p></article>`).join('')||empty('No matching leads. Find opportunities to add one.');
}
function renderDrafts(){
 $('draft-items').innerHTML=drafts.map(d=>{const lead=leads.find(l=>l.id===d.opportunity_id);const ids=JSON.parse(d.attachments);const locked=['Sent','Sending','Delivery unknown'].includes(d.status);return `<article class="panel"><span class="badge">${esc(d.status)}</span><h2>${esc(lead?.company||'Opportunity')} · ${esc(lead?.title||'')}</h2><label>Recipient<input id="recipient-d${d.id}" type="email" value="${esc(d.recipient)}" ${locked?'disabled':''}></label><label>Subject<input id="subject-d${d.id}" value="${esc(d.subject)}" ${locked?'disabled':''}></label><label>Message<textarea id="body-d${d.id}" rows="9" ${locked?'disabled':''}>${esc(d.body)}</textarea></label><div class="checklist"><strong>Attachments</strong>${documents.filter(x=>['resume','portfolio'].includes(x.kind)).map(x=>`<label><input type="checkbox" data-attachment="${d.id}" value="${x.id}" ${ids.includes(x.id)?'checked':''} ${locked?'disabled':''}>${esc(x.name)} <a href="/api/document?id=${x.id}">Download</a></label>`).join('')||empty('No employer-ready documents imported.')}<p class="small">Download and inspect selected originals. Internal references cannot be sent.</p></div>${!locked?`<button class="secondary" data-action="edit-draft" data-id="${d.id}">Save draft edits</button><div class="checklist"><label><input type="checkbox" id="review-d${d.id}">I reviewed the recipient, exact message, attachments and prior outreach.</label><label><input type="checkbox" id="repeat-d${d.id}">This is an intentional follow-up to prior outreach.</label></div><button data-action="approve" data-id="${d.id}">Approve saved draft</button><button data-action="send" data-id="${d.id}" ${d.status!=='Approved'||!state.gmail?'disabled':''}>Send approved email</button><button class="secondary" data-action="copy" data-id="${d.id}">Copy saved message</button><p class="small">Gmail must be connected to send here. Contra proposals are copied and submitted on Contra manually. Editing resets approval.</p>`:`<p>${d.status==='Delivery unknown'?'Check Gmail Sent before any retry. Automatic resend is blocked.':d.status==='Sent'?'Gmail accepted this message. This is not independent proof of recipient delivery.':'A send attempt is in progress; check Gmail before retrying.'}</p>`}</article>`}).join('')||empty('Prepare a proposal from an opportunity on your board.');
}
function renderLibrary(){
 $('document-items').innerHTML=documents.map(d=>`<article class="panel document"><span class="badge">${esc(d.kind==='reference'?'Internal reference':d.kind)}</span><h2>${esc(d.name)}</h2><p class="small">${esc(d.category)} · ${d.text_length} characters indexed · ${formatDate(d.imported)}</p><a href="/api/document?id=${d.id}">Download original</a></article>`).join('')||empty('Your library is empty. Import the career archive and résumé files you supplied earlier.');
}
function renderActivity(){
 $('reply-items').innerHTML=messages.map(m=>`<article class="panel"><h2>${esc(m.subject)}</h2><p>${esc(m.sender)}</p><p>${esc(m.snippet)}</p><span class="small">Matched to opportunity #${m.opportunity_id}</span></article>`).join('');
 $('history-items').innerHTML=history.map(h=>`<div class="row"><div><strong>${esc(h.action)}</strong><p class="small">${esc(h.detail)}</p></div><span class="small">${formatDate(h.created)}</span></div>`).join('')||empty('Actions will be recorded here.');
}
function renderSettings(){
 $('settings-items').innerHTML=`<div class="grid"><article class="panel"><h2>Saved records</h2><p>${esc(state.storage.path)}</p><p>${state.storage.writable?'Writable':'Not writable'} · ${state.storage.mount_detected?'Mount detected':'Mount not detected'}</p><p class="small">Save a test lead, restart the Space, then confirm it is still on the board.</p><button class="secondary" data-action="storage-verified">I checked: my lead survived restart</button></article><article class="panel"><h2>Gmail / Google Workspace</h2><p>${state.gmail?'Connected':'Not connected'}</p><button data-action="gmail-connect" ${!state.gmail_configured?'disabled':''}>Connect your inbox</button><button class="secondary" data-action="gmail-disconnect">Disconnect</button><details><summary>One-time Google setup</summary><p class="small">Enable Gmail API in Google Cloud. Create an OAuth Web application. Add your Space’s direct app URL plus /oauth/google/callback as the authorized redirect URI. Add yourself as a test user when required. Store GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET as private Space secrets; set PUBLIC_URL to the direct https app address. Restricted Gmail scopes may require Google verification for wider use. See the deployment guide for steps.</p></details></article><article class="panel"><h2>Hugging Face AI writing</h2><p>${state.ai_configured?'Token configured; a successful proposal request still needs verification':'Not configured'} ${esc(state.ai_model)}</p><p class="small">In Space settings add a separate HF_INFERENCE_TOKEN secret with inference-provider permission. Set HF_MODEL to a supported chat model from Hugging Face’s current provider list. Deployment tokens are not reused. Requests can incur provider costs; each draft is limited to 700 output tokens, with 10 AI attempts per day. Default model: Qwen/Qwen3-235B-A22B-Instruct-2507:scaleway.</p></article><article class="panel"><h2>Background discovery</h2><label><input id="scheduler" type="checkbox" ${state.scheduler_enabled?'checked':''}>Check public sources every 12 hours while this Space is awake</label><button class="secondary" data-action="scheduler">Save discovery setting</button><p class="small">Free Spaces can sleep. This is not an always-on guarantee. No background sending or applications.</p></article></div>`;
}
async function fileData(file){if(file.size>25*1024*1024)throw Error('Each upload must be under 25 MB');const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(binary)}
function draftFields(id){return {id,recipient:$('recipient-d'+id).value,subject:$('subject-d'+id).value,body:$('body-d'+id).value,attachments:[...document.querySelectorAll(`[data-attachment="${id}"]:checked`)].map(x=>Number(x.value))}}
document.addEventListener('click',async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(b.dataset.tab){tab(b.dataset.tab);return}
 const action=b.dataset.action,id=Number(b.dataset.id);if(!action)return;
 b.disabled=true;
 try{
  if(action==='board'){tab('board');return}
  if(action==='update'){const d={id};for(const f of ['stage','relationship','contact','followup','deadline','description','notes','outcome'])d[f]=$(f+'-'+id).value;await api('/api/update',d);notice('Changes saved.');}
  if(action==='draft'||action==='ai'){const r=await api('/api/draft',{id,mode:action==='ai'?'ai':'template'});notice('Draft prepared. Review and edit it before approval. Sources: '+(r.evidence.join(', ')||'No career documents imported; template only.'));tab('drafts');}
  if(action==='edit-draft'){await api('/api/draft/edit',draftFields(id));notice('Draft saved. Approval reset; review the saved version.');}
  if(action==='approve'){
   if(!$('review-d'+id).checked)throw Error('Complete the review checkbox first.');
   const stored=drafts.find(x=>x.id===id),current=draftFields(id);
   if(stored.recipient!==current.recipient||stored.subject!==current.subject||stored.body!==current.body||JSON.stringify(JSON.parse(stored.attachments))!==JSON.stringify(current.attachments))throw Error('Save your draft edits before approving.');
   await api('/api/approve',{id,confirmation:'I reviewed recipient, content, attachments and history',repeat_confirmed:$('repeat-d'+id).checked});notice('Saved draft approved. Sending is a separate action.');
  }
  if(action==='send'){
   const stored=drafts.find(x=>x.id===id),current=draftFields(id);
   if(stored.recipient!==current.recipient||stored.subject!==current.subject||stored.body!==current.body||JSON.stringify(JSON.parse(stored.attachments))!==JSON.stringify(current.attachments))throw Error('The message has unsaved changes. Save and reapprove first.');
   if(!confirm(`Send this approved email to ${stored.recipient}?`))return;
   const r=await api('/api/send',{id,digest:stored.digest});notice(r.message);
  }
  if(action==='copy'){const d=drafts.find(x=>x.id===id);await navigator.clipboard.writeText(d.subject+'\n\n'+d.body);notice('Saved message copied. Submit it on the platform yourself.');}
  if(action==='gmail-connect'){const popup=window.open('about:blank','_blank');try{const r=await api('/api/gmail/connect',{});if(!popup)throw Error('Allow pop-ups for this app, then connect again.');popup.opener=null;popup.location=r.url;notice('Complete Google authorization in the new window.');}catch(e){if(popup)popup.close();throw e;}}
  if(action==='gmail-disconnect'){if(confirm('Remove this bot’s stored Gmail connection?')){await api('/api/gmail/disconnect',{});notice('Disconnected locally. You can also revoke access in Google account settings.');}}
  if(action==='scheduler'){await api('/api/settings',{scheduler_enabled:$('scheduler').checked});notice('Discovery setting saved.');}
  if(action==='storage-verified'){await api('/api/settings',{storage_verified:true});notice('Your restart check recorded.');}
  await refresh();
 }catch(e){notice(e.message,true)}finally{if(b.isConnected)b.disabled=false}
});
$('lead-form').onsubmit=async e=>{e.preventDefault();await run(()=>api('/api/add',Object.fromEntries(new FormData(e.target))),r=>r.added?'Opportunity saved and evaluated.':'This lead is already saved.');};
$('upload-form').onsubmit=async e=>{e.preventDefault();const button=e.target.querySelector('button');button.disabled=true;try{for(const file of $('upload-files').files){notice('Importing '+file.name+'…');await api('/api/upload',{name:file.name,content:await fileData(file),kind:$('upload-kind').value})}notice('Career documents imported privately. Originals preserved.');await refresh()}catch(e){notice(e.message,true)}finally{button.disabled=false}};
$('restore-form').onsubmit=async e=>{e.preventDefault();if(!confirm('Merge leads and documents from this backup? Existing records will remain.'))return;await run(async()=>api('/api/restore',{content:await fileData($('restore-file').files[0])}),r=>r.message);};
$('scan').onclick=async()=>{$('scan').disabled=true;notice('Checking public sources…');await run(()=>api('/api/discover',{}),r=>r.cached?r.message:`Added ${r.added} leads.${r.errors?.length?' Some feed checks failed: '+r.errors.join(' '):''}`);$('scan').disabled=false};
$('sync').onclick=()=>run(()=>api('/api/gmail/sync',{}),r=>`${r.linked} new replies linked. ${r.message}`);
for(const id of ['search','stage-filter','category-filter'])$(id).addEventListener(id==='search'?'input':'change',renderBoard);
$('stage-filter').innerHTML+=stages.map(s=>option(s,'')).join('');
api('/api/playbooks').then(items=>{$('playbooks').innerHTML=items.map(p=>`<details><summary>${esc(p.platform)} guide · ${esc(p.status)}</summary><p class="small">${esc(p.summary)}</p><ul>${p.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>${p.sources.map(s=>`<p class="small"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.label)}</a> · ${esc(s.checked)}</p>`).join('')}</details>`).join('')}).catch(e=>notice(e.message,true));
refresh().catch(e=>notice(e.message,true));
