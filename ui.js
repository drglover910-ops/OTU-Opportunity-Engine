'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stages=['New','Researching','Ready to contact','Contacted','Interview / meeting','Offer / contract','Won','Parked'];
let leads=[],documents=[],drafts=[],history=[],messages=[],packages=[],careerUpdates=[],emailCases=[],workspaces=[],state={};
let contraSummary={},developerRequests=[],knowledge={},activeDocument=null,documentContext=null,proposalContext=null;
let platforms=[],activePlatform=null,browserRunning=false,lastBrowserPage=null,frameBusy=false;
let conversationLoad=0,chatListLoad=0,pdfPage=0;
let selectedWorkspace=null,selectedOpportunity=null,selectedChat=null,chatThreads=[],renameTarget=null,documentReturnFocus=null,developerKey=sessionStorage.getItem("otu-developer-key")||"";
let noticeTimer;function notice(message,error=false){clearTimeout(noticeTimer);$('status').textContent=message;$('status').classList.toggle('warning',error);if(!error)noticeTimer=setTimeout(()=>{if($('status').textContent===message)$('status').textContent=''},8000)}
async function api(path,data){const r=await fetch(path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(developerKey?{'X-Developer-Key':developerKey}:{})},body:data===undefined?undefined:JSON.stringify(data)});const value=await r.json();if(!r.ok){if(r.status===403&&value.error?.includes('developer tools')){developerKey='';sessionStorage.removeItem('otu-developer-key');$('developer-content').hidden=true;$('developer-gate').hidden=false;$('developer-lock').hidden=true}let error=value.error||'This request could not be completed.';if(!developerKey&&error.startsWith('Service returned HTTP'))error=/HTTP 402/.test(error)?'AI writing needs provider credits. Basic writing and saved notes still work.':/HTTP 429/.test(error)?'The service needs a short pause. Wait a minute and try again.':/HTTP (401|403)/.test(error)?'This connection needs attention. Open Connections to check it.':'The service could not complete this request. Your saved work is safe.';throw Error(error)}return value}
async function run(task,success){try{const r=await task();if(success)notice(typeof success==='function'?success(r):success);await refresh();return r}catch(e){notice(e.message,true)}}
let activePanel=null,browsingWorkspace=null,panelReturnFocus=null;
const panelNames={mail:'Mail','status-report':'Where we stand',today:'Overview',board:'Opportunities',drafts:'Ready to review',library:'Career library',discover:'Explore opportunities',connections:'Connections',help:'Help',workspaces:'Workspaces',developer:'Developer tools',platforms:'Platforms & profiles','platform-browser':'Platform browser','device-tools':'Safari tools','device-import':'Review opportunity',activity:'Activity','chat-settings':'Conversation tools',files:'Conversation files'};
// Retain each live section and its form state. Do not clone IDs or rebuild chat on navigation.
for(const section of [...document.querySelectorAll('main > .tab')])if(section.id!=='conversation')$('workspace-panel-content').append(section);
for(const [id,title,nodes] of [['chat-settings','Conversation tools',['application-shortcut','conversation-tools']],['files','Conversation files',['conversation-files']]]){
 const section=document.createElement('section');section.id=id;section.className='tab';section.hidden=true;for(const name of nodes){const node=$(name);section.append(node);if(node.tagName==='DETAILS')node.open=true}$('workspace-panel-content').append(section);
}
function tab(name){
 if(name==='document-reader'){openDocumentPane();return}
 if(name==='settings')name='connections';
 document.querySelector('.layout').classList.add('chat-mode');$('conversation').hidden=false;
 if(name==='conversation'){closeWorkspacePanel(false);return}
 if(name==='mail')loadMail().catch(()=>{});
 const section=$(name);if(!section)return;
 if(!$('document-reader').hidden)closeDocumentPane(false);
 panelReturnFocus=document.activeElement;activePanel=name;
 $('workspace-panel-content').querySelectorAll('.tab').forEach(el=>el.hidden=el.id!==name);
 $('workspace-panel-title').textContent=panelNames[name]||'Your workspace';$('workspace-panel').hidden=false;
 document.querySelector('.layout').classList.add('panel-open');$('workspace-menu').open=false;
 document.querySelectorAll('nav [data-tab]').forEach(el=>el.classList.toggle('active',el.dataset.tab===name));
 syncWorkspaceLayers();$('workspace-panel').focus({preventScroll:true});
}
function closeWorkspacePanel(restore=true){
 activePanel=null;document.querySelectorAll('nav [data-tab].active').forEach(el=>el.classList.remove('active'));$('workspace-panel').hidden=true;document.querySelector('.layout').classList.remove('panel-open');syncWorkspaceLayers();
 if(restore){const target=panelReturnFocus?.isConnected&&panelReturnFocus.getClientRects().length&&!panelReturnFocus.closest('#workspace-panel')?panelReturnFocus:$('workspace-menu').querySelector('summary');if(!target.matches('input,textarea,select'))target.focus({preventScroll:true})}
}
$('close-workspace-panel').onclick=()=>closeWorkspacePanel();$('panel-backdrop').onclick=()=>{if(!$('document-reader').hidden)closeDocumentPane();else closeWorkspacePanel()};

function formatDate(s){return s?new Date(s).toLocaleString():''}
function localDate(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
const progressLabels={'New':'Just found','Researching':'Looking into it','Ready to contact':'Ready to reach out','Contacted':'Message sent','Interview / meeting':'Interview or meeting','Offer / contract':'Offer or contract','Won':'Paid work secured','Parked':'Set aside'};
function option(value,current){return `<option value="${esc(value)}" ${value===current?'selected':''}>${esc(progressLabels[value]||value)}</option>`}
function jump(name){tab(name)}
function hasMaster(){return documents.some(d=>d.kind==='reference'&&d.name.includes('Master_Career_Resume'))}
function steps(){return [{done:hasMaster(),label:'Add your career files',text:'Add your master career ZIP. Earlier résumé designs are optional.',target:'library'},{done:!!state.last_ai_success,label:'Connect AI writing (optional)',text:state.ai_configured?'Connected settings saved. Try an AI draft to check it works.':'Start with basic drafts, or connect Hugging Face.',target:'settings'},{done:!!state.gmail,label:'Connect Gmail',text:'Sign in once after the app connection is registered.',target:'settings'}]}
function friendlyDocument(name){if(name.includes('Master_Career'))return 'Complete career record';if(name.includes('Master_Coaching'))return 'Master coaching résumé';if(name.includes('Kids_Choice'))return 'Kids Choice Sports résumé';return name.replace(/^Desmond_Glover_/, '').replace(/\.(pdf|docx|txt|md|json)$/i,'').replace(/_Designed_AI_Updated|_Designed|_CURRENT|_UPDATED/g,'').replace(/_/g,' ')}
function empty(text){return `<p class="small">${esc(text)}</p>`}
async function refresh(){
 [state,leads,documents,drafts,history,messages,packages,careerUpdates,emailCases,workspaces,platforms,contraSummary,developerRequests,knowledge,chatThreads]=await Promise.all(['/api/status','/api/opportunities','/api/documents','/api/drafts','/api/history','/api/messages','/api/packages','/api/career-updates','/api/email-cases','/api/workspaces','/api/platforms','/api/contra/summary','/api/developer/requests','/api/project-knowledge','/api/chat-threads'].map(p=>api(p)));
 $('version').textContent='v'+state.version;$('footer-version').textContent='v'+state.version;
 $('connection-summary').textContent=`${state.storage.restart_verified?'Your work is saved':state.storage.mount_detected?'Saving is connected':'Saving needs attention'} · Gmail ${state.gmail?'connected':'not connected'}`;
 await loadProjects();renderStatusReport();renderSidebar();renderContraResults();renderToday();renderBoard();renderDrafts();renderLibrary();renderActivity();if(developerKey)renderSettings();renderConnections();renderWorkspaces();renderHelp();renderPlatforms();
 if(!sessionStorage.getItem('otu-onboarding-seen')&&!documents.length){jump('library');sessionStorage.setItem('otu-onboarding-seen','yes')}
 const scan=state.last_discovery;$('scan-info').textContent=scan.finished?`Last check: ${formatDate(scan.finished)}. ${scan.added||0} added. ${(scan.errors||[]).length?'Some sources failed; live discovery is not fully verified.':''}`:'Your first search is ready. Click Find new opportunities.';
}
function renderToday(){
 const due=leads.filter(l=>l.followup&&l.followup<=localDate()&&!['Won','Parked'].includes(l.stage));
 const replies=messages.length;const approvals=drafts.filter(d=>d.status==='Draft').length;
 $('stats').innerHTML=[[leads.length,'Opportunities'],[due.length,'Follow-ups due'],[approvals,'Drafts to review'],[leads.filter(l=>l.stage==='Won').length,'Wins']].map(([n,label])=>`<div><strong>${n}</strong>${label}</div>`).join('');
 const setup=steps();$('welcome-setup').innerHTML=(!documents.length||!state.gmail)?`<article class="panel welcome"><h2>A few steps, then you’re ready.</h2><p>Your opportunities are already saved. Add your career files first; AI writing is optional.</p><button data-action="setup">Continue setup</button><button class="secondary" data-action="board">Browse opportunities now</button></article>`:'';
 const todos=[];
 if(!state.storage.mount_detected)todos.push('Connect storage or download a backup before restarting.');
 if(!documents.length)todos.push('Add your career ZIP and résumés in My profile.');
 if(!leads.length)todos.push('Open Contra and save your first project, or check the live feed.');
 if(due.length)todos.push(`${due.length} follow-ups need attention on My opportunities.`);
 if(approvals)todos.push(`${approvals} drafts are waiting for your review.`);
 if(replies)todos.push(`${replies} saved reply records are available in your opportunity conversations.`);
 $('todos').innerHTML=todos.map(t=>`<div class="row">${esc(t)}</div>`).join('')||empty('Choose a promising lead and prepare its next step.');
 $('best').innerHTML=leads.filter(l=>['New','Researching','Ready to contact'].includes(l.stage)).slice(0,4).map(l=>`<div class="row"><div><strong>${esc(l.title)}</strong><p class="small">${esc(l.company)} · Match ${l.fit.score}/100</p></div><button class="secondary" data-action="board">Review board</button></div>`).join('')||empty('Your best fits will appear here after you save leads.');
 $('storage-warning').hidden=state.storage.restart_verified;$('storage-warning').textContent=state.storage.mount_detected?'Saving is connected. We still need to check that your records survive a restart.':'Saving needs attention. Download a copy of your work before restarting the app.';
}
function renderBoard(){
 const query=$('search').value.toLowerCase();const workspace=$('workspace-filter').value;const stage=$('stage-filter').value;const category=$('category-filter').value;
 const rows=leads.filter(l=>(workspace==='all'||l.workspace===workspace)&&(stage==='All'||l.stage===stage)&&(category==='All'||l.category===category)&&`${l.title} ${l.company} ${l.description}`.toLowerCase().includes(query));
 $('board-items').innerHTML=rows.map(l=>`<article class="card"><span class="badge">Match ${l.fit.score}/100</span><span class="badge">${esc(l.source)}</span><h2>${esc(l.title)}</h2><button class="secondary" data-action="conversation" data-id="${l.id}">Open conversation</button><p>${esc(l.company)} · ${esc(l.category)}</p><p class="small">${esc(l.fit.reasons.join(' · '))}</p>${l.fit.warnings.map(w=>`<p class="small warning">${esc(w)}</p>`).join('')}<p>${esc(l.pay||'Pay unknown')}<br><span class="small">${esc(l.location||'Location not provided')}</span></p>${l.url?`<a href="${esc(l.url)}" target="_blank" rel="noopener">Read original listing</a>`:''}
 <details><summary>Update progress or contact details</summary><label>Workspace<select id="workspace-${l.id}">${workspaces.map(w=>`<option value="${esc(w.id)}" ${w.id===l.workspace?'selected':''}>${esc(w.name)}</option>`).join('')}</select></label><label>Progress<select id="stage-${l.id}">${stages.map(s=>option(s,l.stage)).join('')}</select></label><label>What do they need from you?<select id="relationship-${l.id}">${['New prospect','Requested paperwork','Follow-up'].map(s=>option(s,l.relationship||'New prospect')).join('')}</select></label><label>Contact email<input id="contact-${l.id}" type="email" value="${esc(l.contact)}"></label><div class="grid"><label>Follow-up<input id="followup-${l.id}" type="date" value="${esc(l.followup)}"></label><label>Application deadline<input id="deadline-${l.id}" type="date" value="${esc(l.deadline)}"></label></div><label>Requirements<textarea id="description-${l.id}" rows="5">${esc(l.description)}</textarea></label><label>Private notes<textarea id="notes-${l.id}">${esc(l.notes)}</textarea></label><label>Outcome / payment notes<input id="outcome-${l.id}" value="${esc(l.outcome)}" placeholder="Record only actual outcomes"></label><button data-action="update" data-id="${l.id}">Save changes</button></details>
 <button data-action="package" data-id="${l.id}">Generate résumé + cover letter</button><details><summary>Other writing options</summary><button class="secondary" data-action="draft" data-id="${l.id}">Write a basic message</button><button class="secondary" data-action="ai" data-id="${l.id}" > ${state.ai_configured?'Write with AI':'Set up AI writing'}</button><p class="small">Basic messages work without an AI connection. Check and edit every message before sending.</p></details></article>`).join('')||empty('No matching leads. Find opportunities to add one.');
}
function renderDrafts(){
 $('package-items').innerHTML=packages.map(p=>{const lead=leads.find(l=>l.id===p.opportunity_id);const files=JSON.parse(p.files),checks=JSON.parse(p.checks);return `<article class="panel"><details><summary>${esc(lead?.company||'Application')} · View finished documents</summary><span class="badge">${checks.owner_reviewed_revision?'Owner-reviewed revised documents':'Documents generated and checked'}</span><h2>${esc(lead?.company||'Application')} · ${esc(lead?.title||'')}</h2><p>Résumé: ${checks.resume_pages} page(s) · Cover letter: ${checks.cover_pages} page(s). Prepared from your master record. Nothing has been sent.</p><div>${Object.entries(files).map(([key,id])=>` ${key.endsWith('_pdf')?`<button class="secondary document-preview" data-action="preview-document" data-id="${id}">View ${esc(key.startsWith('resume')?'résumé':'cover letter')}</button>`:''}<a class="button secondary" href="/api/document?id=${id}">${esc({resume_pdf:'Résumé PDF',resume_docx:'Résumé Word',cover_pdf:'Cover letter PDF',cover_docx:'Cover letter Word'}[key])}</a>`).join('')}</div><p class="small">The email below has the PDF résumé and cover letter attached. Approving and sending are separate actions.</p></details></article>`}).join('');
 $('draft-items').innerHTML=drafts.map(d=>{const lead=leads.find(l=>l.id===d.opportunity_id);const ids=JSON.parse(d.attachments);const locked=['Sent','Sending','Delivery unknown'].includes(d.status);return `<article class="panel"><span class="badge">${esc({'Draft':'Needs your review','Approved':'Approved — ready to send','Sent':'Sent through Gmail','Sending':'Sending…','Delivery unknown':'Check Gmail before retrying'}[d.status]||d.status)}</span><h2>${esc(lead?.company||'Opportunity')} · ${esc(lead?.title||'')}</h2><button class="secondary" data-action="discuss-proposal" data-id="${d.id}">Discuss or revise this proposal</button><label>Recipient<input id="recipient-d${d.id}" type="email" value="${esc(d.recipient)}" ${locked?'disabled':''}></label><label>Subject<input id="subject-d${d.id}" value="${esc(d.subject)}" ${locked?'disabled':''}></label><label>Message<textarea id="body-d${d.id}" rows="9" ${locked?'disabled':''}>${esc(d.body)}</textarea></label><div class="checklist"><strong>Attached to this message</strong><p>${ids.map(id=>{const doc=documents.find(x=>x.id===id);return doc?`<a href="/api/document?id=${id}">${esc(friendlyDocument(doc.name))}</a>`:'Missing document'}).join(' · ')||'No attachments selected'}</p><details><summary>Change attachments</summary>${documents.filter(x=>x.kind==='portfolio'||packages.some(p=>p.opportunity_id===d.opportunity_id&&Object.values(JSON.parse(p.files)).includes(x.id))).map(x=>`<label><input type="checkbox" data-attachment="${d.id}" value="${x.id}" ${ids.includes(x.id)?'checked':''} ${locked?'disabled':''}>${esc(x.name)} <a href="/api/document?id=${x.id}">Download</a></label>`).join('')||empty('No employer-ready documents imported.')}<p class="small">Download and inspect selected originals. Background documents stay private and cannot be attached.</p></details></div>${!locked?`<button class="secondary" data-action="edit-draft" data-id="${d.id}">Save my edits</button><div class="checklist"><label><input type="checkbox" id="review-d${d.id}">I reviewed the recipient, exact message, attachments and prior outreach.</label><label><input type="checkbox" id="repeat-d${d.id}">This is an intentional follow-up to prior outreach.</label></div><button data-action="approve" data-id="${d.id}">Approve this message</button><button data-action="send" data-id="${d.id}" ${d.status!=='Approved'||!state.gmail?'disabled':''}>Send approved email</button><button class="secondary" data-action="copy" data-id="${d.id}">Copy message</button><p class="small">Gmail must be connected to send here. Contra proposals are copied and submitted on Contra manually. Editing resets approval.</p>`:`<p>${d.status==='Delivery unknown'?'Check Gmail Sent before any retry. Automatic resend is blocked.':d.status==='Sent'?'Gmail accepted this message. This is not independent proof of recipient delivery.':'A send attempt is in progress; check Gmail before retrying.'}</p>`}</article>`}).join('')||empty('Prepare a proposal from an opportunity on My opportunities.');
}
function renderLibrary(){ $('add-career-files').open=!documents.length;
 $('career-update-items').innerHTML=careerUpdates.slice(0,4).map(u=>`<p class="small">${esc(u.fact)} · ${esc(u.source)}</p>`).join('');
 $('library-summary').innerHTML=documents.length?`<div class="notice good">${documents.length} files added. Originals are kept intact. <button class="secondary" data-action="setup">Next: writing and Gmail</button></div>`:empty('ZIP files are welcome. You do not need to open them first.');
 $('document-items').innerHTML=documents.map(d=>`<article class="panel document"><span class="badge">${esc(d.kind==='reference'?'Background information':d.kind==='resume'?(packages.some(p=>Object.values(JSON.parse(p.files)).includes(d.id))?'Opportunity-specific résumé':'Past résumé example'):d.kind==='cover_letter'?'Opportunity document / past example':'Shareable portfolio')}</span><h2>${esc(friendlyDocument(d.name))}</h2><button class="secondary" data-action="preview-document" data-id="${d.id}">Read here</button><a href="/api/document?id=${d.id}">Download original</a><details><summary>File details</summary><p class="small">${esc(d.name)} · ${esc(d.category)} · Added ${formatDate(d.imported)}</p></details></article>`).join('')||empty('Add your archive and résumé files above. You can select several files at once.');
}
function renderActivity(){
 const study=state.history_study||{};$('study-status').textContent=study.status?`${study.status}: ${study.threads_reviewed||0} conversations reviewed. ${study.limited?'The query page limit was reached; more history may remain.':''}`:'No sent-history review completed yet.';
 $('email-case-items').innerHTML=emailCases.map(c=>`<details class="panel"><summary>${esc(c.company)} · ${esc(c.summary.status)}</summary><p>${esc(c.subject)}</p><p class="small">${c.summary.sent} sent · ${c.summary.human_replies} human replies · ${esc(c.summary.latest_date||'')}</p><p class="small">Conversation evidence is not proof of a hire or payment.</p><button class="secondary" data-action="load-case" data-case="${esc(c.thread_id)}">Read conversation</button><div id="case-${esc(c.thread_id)}"></div></details>`).join('');
 $('reply-items').innerHTML=messages.map(m=>`<article class="panel"><h2>${esc(m.subject)}</h2><p>${esc(m.sender)}</p><p>${esc(m.snippet)}</p><span class="small">Matched to opportunity #${m.opportunity_id}</span></article>`).join('');
 $('history-items').innerHTML=history.map(h=>`<div class="row"><div><strong>${esc(h.action)}</strong><p class="small">${esc(h.detail)}</p></div><span class="small">${formatDate(h.created)}</span></div>`).join('')||empty('Actions will be recorded here.');
}
function renderSettings(){
 const setup=steps();$('setup-progress').innerHTML=`<div class="setup-steps">${setup.map((s,i)=>`<div class="setup-step ${s.done?'complete':''}"><span>${s.done?'✓':i+1}</span><strong>${esc(s.label)}</strong><small>${s.done?'Ready':i===1?'Optional':'To do'}</small></div>`).join('')}</div>`;
 $('settings-items').innerHTML=`<article class="panel setup-card"><div class="step-heading"><span class="step-number">1</span><h2>Add your career files</h2><span class="badge">${documents.length?'Done':'Start here'}</span></div><p>${documents.length?`${documents.length} files are in your private library.`:'Choose your master career ZIP. We open it for you and use it to build finished applications.'}</p><button data-action="library">${documents.length?'View my career files':'Add my career files'}</button><p class="small">Your master record is the source. The bot generates the résumé and cover letter; earlier examples are optional.</p></article>
 <article class="panel setup-card"><div class="step-heading"><span class="step-number">2</span><h2>Choose how to write</h2><span class="badge">Optional</span></div><p>Basic messages are ready now, without a paid AI service. Hugging Face can help tailor proposals to your experience and the listing.</p><p class="${state.last_ai_success?'good':'small'}">${state.last_ai_success?'AI writing has passed a real request.':state.ai_configured?'Connection settings saved. Try an AI draft after adding your career files.':'Hugging Face writing is not connected yet.'}</p><button class="secondary" data-action="board">Use basic messages</button><details><summary>Connect Hugging Face writing</summary><ol><li><a href="https://huggingface.co/settings/tokens" target="_blank" rel="noopener">Create an access token</a> with <strong>Make calls to Inference Providers</strong> permission.</li><li>Open <a href="https://huggingface.co/spaces/Dezz-9-10/OTU-Opportunity-Engine/settings" target="_blank" rel="noopener">your app’s Hugging Face settings</a> → Variables and secrets → New secret.</li><li>Name the secret <code>HF_INFERENCE_TOKEN</code> and put your new token in its value. Save it there; don’t put it in chat.</li><li>Return here and click <strong>Check my connections</strong>.</li></ol><button data-action="refresh">Check my connections</button></details><p class="small">Finding opportunities does not use paid AI. AI drafts use provider credits and may cost money. We limit requests to 10 per day; this is a request limit, not a dollar cap. Your OpenAI balance is not used.</p><details class="advanced"><summary>Advanced writing settings</summary><p class="small">Default model: ${esc(state.ai_model)}. Optional HF_MODEL variable selects a supported model. Each request has a 700-output-token limit. Selected private career text is shared with the provider only when you request a draft.</p></details></article>
 <article class="panel setup-card"><div class="step-heading"><span class="step-number">3</span><h2>Connect Gmail</h2><span class="badge">${state.gmail?'Connected':state.gmail_configured?'Ready to sign in':'One-time setup needed'}</span></div><p>${state.gmail?'Your inbox is connected. You still approve each message before sending.':state.gmail_configured?'Click below, sign in with your intended Gmail account, and approve access.':'Google requires this app to be registered before the sign-in button can work. That setup happens once; you will not repeat it during daily use.'}</p>${state.gmail_configured?`<a class="button" href="/oauth/google/start" target="_blank" rel="noopener">${state.gmail?'Reconnect Gmail':'Sign in with Google'}</a>`:'<button data-action="gmail-guide">Show Gmail setup steps</button>'}${state.gmail?'<button class="secondary" data-action="gmail-disconnect">Disconnect Gmail</button>':''}<details id="gmail-guide"><summary>One-time Google setup</summary><ol><li>Open <a href="https://console.cloud.google.com/" target="_blank" rel="noopener">Google Cloud Console</a>. Choose or create a project and enable <strong>Gmail API</strong>.</li><li>Set up Google’s consent screen for your account. If the app is in Testing, add your own Gmail address as a test user.</li><li>Create an OAuth client of type <strong>Web application</strong>. Add this exact authorized redirect address:<div class="copy-line"><code>https://dezz-9-10-otu-opportunity-engine.hf.space/oauth/google/callback</code><button class="secondary" data-action="copy-redirect">Copy address</button></div></li><li>Allow the Gmail send and readonly scopes. Save the client ID and client secret in your private Space settings as <code>GOOGLE_CLIENT_ID</code> and <code>GOOGLE_CLIENT_SECRET</code>.</li><li>Add a regular variable: <code>PUBLIC_URL</code> = <code>https://dezz-9-10-otu-opportunity-engine.hf.space</code>.</li><li>Come back and click <strong>Check my connections</strong>, then <strong>Sign in with Google</strong>.</li></ol><p class="small">Your Gmail password never goes into this app. Google may require account or organization approval. Testing authorizations can expire.</p><button data-action="refresh">Check my connections</button></details><p class="small">You can prepare and copy proposals while Gmail setup is unfinished.</p></article>
 <details class="panel advanced"><summary>Advanced settings and saved records</summary><p class="${state.storage.restart_verified?'good':'warning'}">${state.storage.restart_verified?'Saving passed its restart check.':'Saving still needs a restart check.'}</p><p class="small">Storage address: ${esc(state.storage.path)}. ${state.storage.writable?'Writable.':'Not writable.'}</p><label><input id="scheduler" type="checkbox" ${state.scheduler_enabled?'checked':''}>Find new opportunities automatically while the app is awake</label><button class="secondary" data-action="scheduler">Save preference</button><p class="small">Public feeds are checked at most every 12 hours. Hugging Face may put the app to sleep; it cannot search while asleep. Messages are never sent automatically.</p></details><article class="panel setup-card"><h2>Contra account options</h2><p>Contra’s Co-Agent supports external tool connections. An official Contra MCP sign-in is available under Connections → Connect Contra. This version checks access and available tools; it does not perform account actions.</p><a class="button" href="https://contra.com/co-agent/connectors" target="_blank" rel="noopener">Open Contra connections</a><details><summary>Find my profile link</summary><p>In Contra, open Profile and click Share Profile. This copies your public profile link. Use Connections → Connect Contra to authorize this bot. Signing into Contra in a separate browser alone does not connect it.</p><a href="https://help.contra.com/en/articles/16275340-how-to-change-your-name-email-and-profile-information-on-contra" target="_blank" rel="noopener">Official profile instructions</a></details></article>`;
}
async function fileData(file){if(file.size>25*1024*1024)throw Error('Each upload must be under 25 MB');const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(binary)}
function draftFields(id){return {id,recipient:$('recipient-d'+id).value,subject:$('subject-d'+id).value,body:$('body-d'+id).value,attachments:[...document.querySelectorAll(`[data-attachment="${id}"]:checked`)].map(x=>Number(x.value))}}
document.addEventListener('click',async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(b.dataset.tab){if(b.dataset.tab==='workspaces'){browsingWorkspace=null;renderWorkspaces()}if(b.dataset.tab==='discover'&&selectedWorkspace)$('listing-workspace').value=selectedWorkspace;jump(b.dataset.tab);document.querySelector('.nav-tools').open=false;closeSidebar();return}
 const action=b.dataset.action,id=Number(b.dataset.id);if(!action)return;
 b.disabled=true;
 try{
  if(action==='check-replies'){await api('/api/gmail/sync',{});await refresh();jump('activity');notice('Replies checked. Open the matching opportunity conversation to continue.');return}
  if(action?.startsWith('browser-')||action?.startsWith('copy-')&&['copy-page-reader','copy-profile-filler'].includes(action)||action==='device-tools'||action==='platform-profile'||action==='platform-open'){await platformAction(action,b);return}
  if(action==='conversation'){await openConversation(leads.find(l=>l.id===id).workspace,id);return}
  if(action==='workspace-contra'){openWorkspace('contra');return}
  if(action==='open-workspace'){openWorkspace(b.dataset.workspace);return}
  if(action==='workspace-conversation'){await openConversation(browsingWorkspace||selectedWorkspace,null);return}
  if(action==='back-workspace'){openWorkspace(browsingWorkspace||selectedWorkspace);return}
  if(action==='new-chat'){const project=$('project-filter').value;const r=await api('/api/chat/new',{workspace:workspaces.some(w=>w.id===project)?project:'assistant'});if(project){await api('/api/chat/organize',{key:r.id,action:'move',project_id:project})}documentContext=null;proposalContext=null;await openConversation(r.workspace,r.opportunity_id,r.id);closeSidebar();return}
  if(action==='open-recent'){const r=chatThreads[Number(b.dataset.chatIndex)];if(r){documentContext=null;proposalContext=null;await openConversation(r.workspace,r.opportunity_id,r.id);closeSidebar()}return}
  if(action==='rename-chat'){renameTarget=b.dataset.chatId;$('rename-chat-title').value=chatThreads.find(t=>t.id===renameTarget)?.title||'';$('rename-chat-dialog').showModal();$('rename-chat-title').focus({preventScroll:true});return}
  if(action==='close-document'){closeDocumentPane();return}
  if(action==='read-answer'){readAnswer(b);return}
  if(action==='stop-answer'){stopAnswer();return}
  if(action==='copy-message'){await copyDeviceTool(b.closest('article').querySelector('.message-text').textContent);b.closest('details').open=false;return}
  if(action==='developer-from-answer'){tab('chat-settings');const text=b.closest('article').querySelector('.message-text').textContent;$('developer-request-text').value=text.slice(0,4000);$('developer-request-reviewed').checked=false;$('developer-request-panel').open=true;$('developer-request-text').focus({preventScroll:true});notice('Review this request before sharing it to the private repository.');return}
  if(action==='remember-conversation'){await api('/api/conversation/memory',{workspace:selectedWorkspace,opportunity_id:selectedOpportunity,chat_id:selectedChat,text:$('conversation-memory-text').value});await openConversation(selectedWorkspace,selectedOpportunity);$('conversation-memory-text').value='';notice('Remembered for this conversation. No AI used.');return}
  if(action==='forget-conversation'){await api('/api/conversation/memory',{workspace:selectedWorkspace,opportunity_id:selectedOpportunity,chat_id:selectedChat,remove_id:id});await openConversation(selectedWorkspace,selectedOpportunity);return}
  if(action==='discuss-proposal'){proposalContext=id;const draft=drafts.find(d=>d.id===id);const lead=leads.find(l=>l.id===draft.opportunity_id);documentContext=null;await openConversation(lead.workspace||'contra',lead.id);$('conversation-mode').value='revise_proposal';$('conversation-text').focus({preventScroll:true});return}
  if(action==='use-proposal-suggestion'){const text=$('proposal-suggestion').value;jump('drafts');const box=$('body-d'+id);if(!box||box.disabled){notice('This proposal is no longer editable. Refresh before revising it.',true);return}box.value=text;box.scrollIntoView({block:'center'});notice('Suggested proposal loaded. Review it and press Save my edits. Nothing is saved or sent yet.');return}
  if(action==='talk-assistant'){documentContext=null;proposalContext=null;await openConversation('assistant',null);return}
  if(action==='preview-document'){await viewDocument(id);return}
  if(action==='pdf-previous'||action==='pdf-next'){pdfPage=Math.max(0,Math.min((activeDocument?.pages||1)-1,pdfPage+(action==='pdf-next'?1:-1)));showPdfPage();return}
  if(action==='document-design'){if(!activeDocument?.pages){notice('Open a PDF version for the designed preview.',true);return}showPdfPage();return}
  if(action==='document-readable'){$('document-frame').hidden=true;$('document-edit-label').hidden=false;return}
  if(action==='document-chat'){if(!activeDocument)return;const pkg=packages.find(p=>Object.values(JSON.parse(p.files)).includes(activeDocument.id));if(!pkg){notice('You can read this original here. Prepare an application before requesting a revised version.',true);return}const lead=leads.find(l=>l.id===pkg.opportunity_id);documentContext=activeDocument.id;await openConversation(lead.workspace||'contra',lead.id);$('conversation-mode').value='revise_document';if(innerWidth<=1100)closeDocumentPane(false);$('conversation-text').focus({preventScroll:true});return}
  if(action==='use-document-suggestion'){const suggestion=document.getElementById('document-suggestion');if(suggestion){const text=suggestion.value;await viewDocument(id);$('document-editor').value=text;$('document-frame').hidden=true;$('document-edit-label').hidden=false;$('document-revision-reviewed').checked=false;jump('document-reader');notice('Suggested text loaded. Review it before saving a new version.')}return}
  if(action==='save-document-version'){if(!activeDocument)return;const r=await api('/api/document/revise',{document_id:activeDocument.id,text:$('document-editor').value,reviewed:$('document-revision-reviewed').checked});await refresh();documentContext=null;await viewDocument(r.document_id);notice(r.message);return}
  if(action==='queue-developer-request'){const r=await api('/api/developer/request',{workspace:selectedWorkspace,opportunity_id:selectedOpportunity,chat_id:selectedChat,text:$('developer-request-text').value,reviewed:$('developer-request-reviewed').checked});developerRequests=await api('/api/developer/requests');renderDeveloperRequests();notice(r.message||'Existing request retained.');return}
  if(action==='copy-developer-request'){const text=$('developer-request-text').value||'Please review the queued development requests in docs/assistant_bridge/requests.json, preserve existing work, and report which changes are complete.';await navigator.clipboard.writeText(text);notice('Handoff copied. Paste it into this developer chat.');return}
  if(action==='contra-save'){const item=(contraSummary.public_opportunities||[])[Number(b.dataset.index)];if(!item)throw Error('Refresh the Contra results first.');await api('/api/add',{company:'Contra client · verify on listing',title:item.title,url:item.url,source:'Contra',description:(item.description||item.kind)+'. Verify eligibility, costs, effort and submission requirements before pursuing.',pay:contraPay(item),workspace:'contra'});await refresh();notice('Saved to My opportunities. Verify the original requirements before preparing an application.');return}
  if(action==='ai-limits'){await api('/api/ai/limits',{daily_requests:Number($('ai-daily').value),daily_tokens:Number($('ai-tokens').value),paused:$('ai-paused').checked});await refresh();notice('AI allowance saved.');return}
  if(action==='contra-sync'){notice('Reading Contra account and earning opportunities. No paid AI requests…');const r=await api('/api/contra/sync',{});await refresh();notice(r.message);return}
  if(action==='contra-check'){notice('Checking Contra access and available tools…');const r=await api('/api/contra/check',{});await refresh();notice(`Contra access checked: ${r.tools} available tools. No account actions were run.`);return}
  if(action==='contra-disconnect'){if(!confirm('Remove the bot’s stored Contra sign-in?'))return;await api('/api/contra/disconnect',{});await refresh();notice('Contra sign-in removed locally.');return}
  if(action==='check-connections'){notice('Checking your inbox and saved connections…');state.connection_check=await api('/api/connections/check',{});renderConnections();notice('Connections checked. No paid AI request was made.');return}
  if(action==='unlock-developer'){if(!confirm('Open technical controls for this session? Everyday work does not need these settings.'))return;const r=await api('/api/developer/unlock',{confirmation:'OPEN DEVELOPER TOOLS'});developerKey=r.token;sessionStorage.setItem('otu-developer-key',developerKey);renderSettings();$('developer-content').hidden=false;$('developer-gate').hidden=true;$('developer-lock').hidden=false;document.querySelector('nav [data-tab="developer"]').textContent='Developer tools · open';return}
  if(action==='lock-developer'){await api('/api/developer/lock',{});developerKey='';sessionStorage.removeItem('otu-developer-key');$('developer-content').hidden=true;$('developer-gate').hidden=false;$('developer-lock').hidden=true;document.querySelector('nav [data-tab="developer"]').textContent='Developer tools · locked';return}
  if(action==='load-case'){const c=await api('/api/email-case?id='+encodeURIComponent(b.dataset.case));$('case-'+b.dataset.case).innerHTML=c.messages.map(m=>`<article class="panel"><strong>${m.direction==='sent'?'You sent':'Reply received'}</strong><p class="small">${esc(m.date)} · ${esc(m.subject)}</p><p style="white-space:pre-wrap">${esc(m.body)}</p></article>`).join('');return}
  if(action==='board'){jump('board');return}
  if(action==='setup'){jump('settings');return}
  if(action==='library'){jump('library');return}
  if(action==='refresh'){await refresh();notice('Connection status updated.');return}
  if(action==='gmail-guide'){$('gmail-guide').open=true;$('gmail-guide').scrollIntoView({block:'start'});return}
  if(action==='copy-redirect'){await navigator.clipboard.writeText('https://dezz-9-10-otu-opportunity-engine.hf.space/oauth/google/callback');notice('Google callback address copied.');return}
  if(action==='update'){const d={id};for(const f of ['stage','relationship','contact','followup','deadline','description','notes','outcome','workspace'])d[f]=$(f+'-'+id).value;await api('/api/update',d);notice('Changes saved.');}
  if(action==='ai'&&!state.ai_configured){jump('settings');notice('Basic messages already work. Open Connect Hugging Face writing to add AI.');return}
  if(action==='package'){notice('Preparing your résumé, cover letter and email…');const r=await api('/api/package',{id});notice(r.message);jump('drafts');}
  if(action==='draft'||action==='ai'){const r=await api('/api/draft',{id,mode:action==='ai'?'ai':'template'});notice('Message prepared. Read it, make any edits, then approve it.'+(r.evidence.length?' Your career files helped prepare it.':' Add your career files for a more complete foundation.'));jump('drafts');}
  if(action==='edit-draft'){await api('/api/draft/edit',draftFields(id));notice('Your edits are saved. Review this version before approving it.');}
  if(action==='approve'){
   if(!$('review-d'+id).checked)throw Error('Complete the review checkbox first.');
   const stored=drafts.find(x=>x.id===id),current=draftFields(id);
   if(stored.recipient!==current.recipient||stored.subject!==current.subject||stored.body!==current.body||JSON.stringify(JSON.parse(stored.attachments))!==JSON.stringify(current.attachments))throw Error('Save your draft edits before approving.');
   await api('/api/approve',{id,confirmation:'I reviewed recipient, content, attachments and history',repeat_confirmed:$('repeat-d'+id).checked});notice('Message approved. It has not been sent yet.');
  }
  if(action==='send'){
   const stored=drafts.find(x=>x.id===id),current=draftFields(id);
   if(stored.recipient!==current.recipient||stored.subject!==current.subject||stored.body!==current.body||JSON.stringify(JSON.parse(stored.attachments))!==JSON.stringify(current.attachments))throw Error('The message has unsaved changes. Save and reapprove first.');
   if(!confirm(`Send this approved email to ${stored.recipient}?`))return;
   const r=await api('/api/send',{id,digest:stored.digest});notice(r.message);
  }
  if(action==='copy'){const d=drafts.find(x=>x.id===id);await navigator.clipboard.writeText(d.subject+'\n\n'+d.body);notice('Saved message copied. Submit it on the platform yourself.');}

  if(action==='gmail-disconnect'){if(confirm('Remove this bot’s stored Gmail connection?')){await api('/api/gmail/disconnect',{});notice('Disconnected locally. You can also revoke access in Google account settings.');}}
  if(action==='scheduler'){await api('/api/settings',{scheduler_enabled:$('scheduler').checked});notice('Discovery setting saved.');}
  if(action==='storage-verified'){await api('/api/settings',{storage_verified:true});notice('Your restart check recorded.');}
  await refresh();
 }catch(e){notice(e.message,true)}finally{if(b.isConnected)b.disabled=false}
});
$('career-update-form').onsubmit=async e=>{e.preventDefault();await run(()=>api('/api/career-update',{...Object.fromEntries(new FormData(e.target)),confirmed:$('career-confirm').checked}),'Master record updated. Future applications will use the confirmed update.');};
$('lead-form').onsubmit=async e=>{e.preventDefault();await run(()=>api('/api/add',Object.fromEntries(new FormData(e.target))),r=>r.added?'Opportunity saved. Find it on My opportunities.':'This lead is already saved.');};
$('upload-form').onsubmit=async e=>{e.preventDefault();const button=e.target.querySelector('button');button.disabled=true;let imported=0;try{for(const file of $('upload-files').files){notice('Importing '+file.name+'…');const result=await api('/api/upload',{name:file.name,content:await fileData(file),kind:$('upload-kind').value});imported+=result.imported??Number(result.added||0);$('upload-progress').textContent=`${imported} new files added…`;}notice(`${imported} new files added. Your originals are kept intact.`);$('upload-progress').textContent='Upload complete';await refresh()}catch(e){notice(e.message,true)}finally{button.disabled=false}};
$('restore-form').onsubmit=async e=>{e.preventDefault();if(!confirm('Merge leads and documents from this backup? Existing records will remain.'))return;await run(async()=>api('/api/restore',{content:await fileData($('restore-file').files[0])}),r=>r.message);};
$('scan').onclick=async()=>{$('scan').disabled=true;notice('Checking public sources…');await run(()=>api('/api/discover',{}),r=>r.cached?r.message:`Added ${r.added} leads.${r.errors?.length?' Some feed checks failed: '+r.errors.join(' '):''}`);$('scan').disabled=false};
$('study-history').onclick=()=>run(()=>api('/api/gmail/history',{}),r=>r.message);
$('sync').onclick=()=>run(()=>api('/api/gmail/sync',{}),r=>`${r.linked} new replies linked. ${r.message}`);
for(const id of ['search','stage-filter','category-filter','workspace-filter'])$(id).addEventListener(id==='search'?'input':'change',renderBoard);
$('stage-filter').innerHTML+=stages.map(s=>option(s,'')).join('');
api('/api/playbooks').then(items=>{$('playbooks').innerHTML=items.map(p=>`<details><summary>${esc(p.platform)} guide · ${esc(p.status)}</summary><p class="small">${esc(p.summary)}</p><ul>${p.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>${p.sources.map(s=>`<p class="small"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.label)}</a> · ${esc(s.checked)}</p>`).join('')}</details>`).join('')}).catch(e=>notice(e.message,true));
refresh().then(async()=>{let saved;try{saved=JSON.parse(localStorage.getItem('otu-last-conversation')||'null')}catch{};if(saved&&chatThreads.some(t=>t.trashed&&t.workspace===saved.workspace&&t.opportunity_id===(saved.opportunity||null)&&t.id===(saved.chat_id||null))){const fresh=await api('/api/chat/new',{workspace:'assistant'});saved={workspace:fresh.workspace,opportunity:null,chat_id:fresh.id}};try{await openConversation(saved?.workspace||'assistant',saved?.opportunity||null,saved?.chat_id||null)}catch{await openConversation('assistant',null,null)};if(developerKey){$('developer-content').hidden=false;$('developer-gate').hidden=true;$('developer-lock').hidden=false}}).catch(e=>notice(e.message,true));

setInterval(async()=>{if(document.hidden||state.history_study?.status!=='running')return;try{const updated=await api('/api/status');state=updated;const study=state.history_study||{};$('study-status').textContent=`${study.status}: ${study.threads_reviewed||0} conversations reviewed.`;if(['complete','partial'].includes(study.status)){emailCases=await api('/api/email-cases');renderActivity();notice(study.status==='partial'?'Review saved. Some threads could not be read; you can resume the review.':'Sent outreach studied. Your conversations are ready in your opportunity conversations.')}}catch(e){notice('History progress is temporarily unavailable. Refresh to check again.',true)}},5000);

function renderConnections(){
 const budget=state.ai_budget||{};
 $('ai-usage-panel').innerHTML=`<h2>AI usage · this bot</h2><p>${budget.count||0} of ${budget.daily_requests||0} requests used today. ${budget.paused?'AI is paused.':'AI is available within your allowance.'}</p><p class="small">Provider-reported tokens: ${budget.actual_tokens||0}. Conservative token reservations: ${budget.reserved_tokens||0} / ${budget.daily_tokens||0}. Resets at midnight UTC. Failed attempts keep their reservation.</p><p class="small">Other projects share your account. Their usage, your balance, and dollar costs are not available here. Check Hugging Face billing for the account total.</p><label>Maximum AI requests per day<input id="ai-daily" type="number" min="0" max="100" value="${budget.daily_requests??5}"></label><label>Daily token allowance<input id="ai-tokens" type="number" min="0" max="1000000" value="${budget.daily_tokens??60000}"></label><label><input id="ai-paused" type="checkbox" ${budget.paused?'checked':''}>Pause paid AI writing</label><button data-action="ai-limits">Save my allowance</button><p class="small">Notes, basic drafts, and read-only Contra checks do not use paid inference.</p>`;

 const checked=state.connection_check||{};
 const label={connected:'Connected',configured:'Settings saved',needs_attention:'Needs your attention',not_connected:'Not connected yet'};
 const gmail=checked.gmail||{status:state.gmail?'configured':'not_connected',message:state.gmail?'Your sign-in is saved. Check connections to confirm inbox access.':'Sign in once to connect your inbox.'};
 const writing=checked.writing||{status:state.ai_configured?'configured':'not_connected',message:'Basic writing is always available. AI writing uses provider credits.'};
 if(state.ai_configured&&state.last_ai_success){writing.status='connected';writing.message='AI writing passed a real request. Last successful answer: '+formatDate(state.last_ai_success)+'.'}
 const saving=checked.saving||{status:state.storage.restart_verified?'connected':'needs_attention'};
 $('connection-cards').innerHTML=[['Gmail',gmail,`${state.gmail_configured?'<a class="button secondary" href="/oauth/google/start" target="_blank" rel="noopener">'+(state.gmail?'Reconnect Gmail':'Sign in with Google')+'</a>':'<button data-tab="help">See setup help</button>'}`],['AI writing',writing,'<button data-tab="board">Prepare an application</button>'],['Saved work',saving,'<a class="button secondary" href="/api/export">Download a private backup</a>'],['Contra',{status:state.contra_connected?(state.contra_check?.checked_at?'connected':'configured'):'not_connected',message:state.contra_connected?(state.contra_check?.checked_at?`Connection checked. ${state.contra_check.tools} available tools found. No account actions were run.`:'Your sign-in is saved. Check access to verify the connection.'):'Sign in on Contra’s own page to authorize the bot. No passwords or tokens go into chat.'},`<a class="button" href="/oauth/contra/start" target="_blank" rel="noopener">${state.contra_connected?'Reconnect Contra':'Connect Contra'}</a>${state.contra_connected?'<button data-action="contra-sync">Check my Contra work & opportunities</button><button class="secondary" data-action="contra-check">Check Contra access</button><button class="secondary" data-action="contra-disconnect">Disconnect Contra</button>':''}<p class="small">Read-only checks can save your profile, published services, portfolio, applications, feeds and challenges. No sending, publishing, applying, or Co-Agent AI history access. Review Contra’s permissions before approving.</p>`]].map(([name,connection,action])=>`<article class="panel"><h2>${name}</h2><span class="badge ${connection.status==='needs_attention'?'warning':''}">${label[connection.status]}</span><p>${esc(connection.message||'Your saved records passed their storage check.')}</p>${action}</article>`).join('');
 if(contraSummary.checked_at){const services=contraSummary.read_shapes?.['list_services:1']?.returned;const projects=contraSummary.read_shapes?.['list_portfolio_projects:2'];$('connection-cards').insertAdjacentHTML('beforeend',`<article class="panel"><h2>Your Contra work</h2><p>${services??'?'} published services · ${projects?.projects_returned??'?'} portfolio projects (${projects?.drafts_returned??'?'} draft).</p><p>${contraSummary.geekyants_application_recorded?'Contra records your GeekyAnts application as applied. No duplicate submission is needed. Attachment contents and client receipt are not verified here.':'GeekyAnts submission is not confirmed by the saved check. Do not submit a duplicate without reviewing Contra.'}</p><p class="small">Last account read: ${formatDate(contraSummary.checked_at)}. Private service drafts and payout readiness may require a website check.</p></article>`)}
 if(writing.last_success)$('connection-cards').insertAdjacentHTML('beforeend',`<p class="small">Last successful AI answer: ${formatDate(writing.last_success)}</p>`);
}
function renderWorkspaces(){
 const selected=$('workspace-filter').value;const listing=$('listing-workspace').value;
 $('listing-workspace').innerHTML='<option value="">Choose automatically</option>'+workspaces.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}</option>`).join('');$('listing-workspace').value=listing;
 $('workspace-filter').innerHTML='<option value="all">All workspaces</option>'+workspaces.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}</option>`).join('');
 $('workspace-filter').value=workspaces.some(w=>w.id===selected)?selected:'all';
 if(browsingWorkspace&&!workspaces.some(w=>w.id===browsingWorkspace))browsingWorkspace=null;
 if(browsingWorkspace){renderWorkspaceDetail();return}
 $('workspace-cards').innerHTML=workspaces.map(w=>`<article class="panel"><h2>${esc(w.name)}</h2><p>${w.opportunities} saved opportunities</p><button data-action="open-workspace" data-workspace="${esc(w.id)}">Open workspace</button></article>`).join('');
}
function openWorkspace(key){browsingWorkspace=key;renderWorkspaceDetail();jump('workspaces')}
function renderWorkspaceDetail(){
 const workspace=workspaces.find(w=>w.id===browsingWorkspace);if(!workspace)return;
 const items=leads.filter(l=>l.workspace===workspace.id);
 $('workspace-cards').innerHTML=`<article class="panel"><h2>${esc(workspace.name)}</h2><p>Planning stays here. Each opportunity below has its own separate conversation.</p><button data-action="workspace-conversation">Open workspace notes</button>${workspace.id==='contra'?'<button class="secondary" data-tab="platforms">Profiles &amp; assisted browsing</button><a class="button secondary" href="https://contra.com/opportunities" target="_blank" rel="noopener">Browse Contra</a><p class="small">Sign in on Contra to browse. Proposals are submitted there manually until account access is verified.</p>':''}<button class="secondary" data-tab="discover">Add an opportunity</button></article>`+items.map(l=>`<article class="panel"><span class="badge">${esc(progressLabels[l.stage]||l.stage)}</span><h2>${esc(l.company)}</h2><p>${esc(l.title)}</p><button data-action="conversation" data-id="${l.id}">Open conversation</button></article>`).join('')+(items.length?'':empty('No opportunities saved here yet. Find a listing, then save it to this workspace.'));
}
async function openConversation(workspace,opportunity,chatId=undefined){
 stopAnswer();
 const load=++conversationLoad;
 if(chatId===undefined)chatId=selectedWorkspace===workspace&&selectedOpportunity===opportunity?selectedChat:null;
 selectedChat=chatId||null;
 if(documentContext&&!packages.some(p=>p.opportunity_id===opportunity&&Object.values(JSON.parse(p.files)).includes(documentContext)))documentContext=null;
 if(proposalContext&&!drafts.some(d=>d.id===proposalContext&&d.opportunity_id===opportunity))proposalContext=null;
 selectedWorkspace=workspace;selectedOpportunity=opportunity;
 const data=await api('/api/conversation?workspace='+encodeURIComponent(workspace)+(opportunity?'&opportunity_id='+opportunity:'')+(selectedChat?'&chat_id='+encodeURIComponent(selectedChat):''));
 if(load!==conversationLoad)return;const listLoad=++chatListLoad;const latestThreads=await api('/api/chat-threads');if(load!==conversationLoad)return;if(listLoad===chatListLoad)chatThreads=latestThreads;renderSidebar();
 const name=workspaces.find(w=>w.id===workspace)?.name||'Workspace',lead=leads.find(l=>l.id===opportunity),thread=chatThreads.find(t=>t.id===selectedChat&&t.workspace===workspace&&t.opportunity_id===opportunity);
 $('conversation-title').textContent=thread?thread.title:lead?lead.company+' · '+lead.title:workspace==='assistant'?'Talk to OTU':name+' · Conversation';
 $('pane-title').textContent=$('conversation-title').textContent;
 localStorage.setItem('otu-last-conversation',JSON.stringify({workspace,opportunity,chat_id:selectedChat}));
 $('conversation-description').textContent=lead?name+' · Opportunity conversation':'';
 await loadConversationFiles();if(load!==conversationLoad)return;
 $('application-shortcut').innerHTML=lead?`<button data-action="package" data-id="${lead.id}">Generate résumé + cover letter</button><button class="secondary" data-tab="drafts">Review documents</button>`:'';
 $('conversation-actions').innerHTML=lead?`<button data-action="package" data-id="${lead.id}">Generate résumé + cover letter</button><button class="secondary" data-action="ai" data-id="${lead.id}">${state.ai_configured?'Prepare an AI message':'Prepare a basic message'}</button><button class="secondary" data-tab="drafts">Review prepared messages</button>${lead.url?`<a class="button secondary" href="${esc(lead.url)}" target="_blank" rel="noopener">Open original opportunity</a>`:''}`:'';
 if(lead&&!state.ai_configured)$('conversation-actions').querySelector('[data-action="ai"]').dataset.action='draft';
 $('conversation-memory-list').innerHTML=(data.memory||[]).map(m=>`<p>${esc(m.text)} <button class="secondary" data-action="forget-conversation" data-id="${m.id}">Forget</button></p>`).join('');
 const emails=data.email_threads.flatMap(t=>t.messages.map(m=>({type:m.direction==='sent'?'Your email':'Incoming email',text:m.body,date:m.date,subject:m.subject})));
 const notes=data.notes.map(n=>({role:n.role,type:n.role==='assistant'?'OTU assistant':n.role==='user'?'You':'Your private note',text:n.text,date:n.created}));
 $('conversation-feed').innerHTML=[...emails,...notes].sort((a,b)=>a.date.localeCompare(b.date)).map(m=>`<article class="panel ${m.role==='user'?'user-message':'assistant-message'}"><strong>${esc(m.type)}</strong><p class="small">${formatDate(m.date)}${m.subject?' · '+esc(m.subject):''}</p><p class="message-text">${esc(m.text)}</p>${m.type==='OTU assistant'?'<div class="answer-audio"><button type="button" class="secondary" data-action="read-answer" aria-pressed="false">🔊 Read aloud</button><button type="button" class="secondary" data-action="stop-answer" hidden>Stop</button></div><details class="message-menu"><summary aria-label="Message actions">•••</summary><div><button class="secondary" data-action="copy-message">Copy answer</button><button class="secondary" data-action="developer-from-answer">Request a development change</button></div></details>':''}</article>`).join('')||'<div class="chat-welcome"><h1>What shall we work on?</h1><p>Find an opportunity, prepare an application, or ask me a question.</p></div>';
 if(!documentContext)$('conversation-mode').value='advice';
 renderDeveloperRequests();$('chat-document-context').hidden=!documentContext;$('chat-document-context').textContent=documentContext?'Editing context: '+(documents.find(d=>d.id===documentContext)?.name||'prepared document')+'. Suggestions do not change the file until you review and save.':'';
 $('conversation-text').value='';$('ask-workspace').disabled=!state.ai_configured;jump('conversation');
}
$('conversation-form').onsubmit=e=>{e.preventDefault();$('ask-workspace').click()};
$('save-work-note').onclick=async()=>{const b=$('save-work-note');b.disabled=true;try{await api('/api/conversation/note',{workspace:selectedWorkspace,opportunity_id:selectedOpportunity,chat_id:selectedChat,text:$('conversation-text').value});await openConversation(selectedWorkspace,selectedOpportunity);notice('Private note saved. No AI used.')}catch(err){notice(err.message,true)}finally{b.disabled=false}};
$('workspace-form').onsubmit=async e=>{e.preventDefault();try{const r=await api('/api/workspaces',Object.fromEntries(new FormData(e.target)));await refresh();openWorkspace(r.id);e.target.reset();notice('Workspace ready.')}catch(err){notice(err.message,true)}};
function renderHelp(){
 const topics=[['Find paid opportunities','Open Find opportunities. Browse Contra or check public listings. Save a listing with its requirements. Opening a platform does not give this bot access to your account.','discover'],['Prepare the right application','Open My opportunities, choose an opportunity, and press Generate résumé + cover letter. The bot uses your career record to prepare a résumé, cover letter, and email. Nothing is sent.','board'],['Understand a conversation','Open Workspaces, choose a platform, then open an opportunity. Its emails and work notes are kept together. Save free notes, or press Ask the bot for AI guidance. AI answers use provider credits and do not send messages or submit applications.','workspaces'],['Approve and send','Open Ready to send. Read the message and its attached documents. Save any edits, check the review box, then approve. Press Send approved email only when you want it sent. For Contra, copy your message and submit it on Contra.','drafts'],['Check replies and older outreach','Use Check for replies on Home. Open the matching opportunity conversation to read the email. Older or unanswered messages are a secondary follow-up queue. Buffalo Stallions does not need outreach right now.','activity'],['Update my career information','Open My profile and add an accurate career update. Your original master record is preserved. Existing files do not need to be uploaded again.','library'],['What costs money?','Finding public listings, saving notes, creating document packages, and basic messages do not use paid AI. Write with AI uses Hugging Face provider credits. The app limits AI drafts and chat answers together to 10 requests a day; that is not a dollar cap. Your OpenAI balance is not used.','connections'],['What happens while the app is closed?','While the Space is awake, it checks public feeds at most every 12 hours and checks for replies about once an hour after a history review. A sleeping Space cannot search or check replies. It never sends messages automatically.','connections'],['Set up or fix a connection','Open Connections and press Check my connections. A saved AI token means settings are configured; a real AI draft is needed to verify writing. For technical setup, deliberately unlock Developer tools. Never paste passwords or tokens into a conversation.','connections']];
 $('help-items').innerHTML=topics.map(([title,text,target])=>`<details class="panel"><summary>${title}</summary><p>${text}</p><button class="secondary" data-tab="${target}">Take me there</button></details>`).join('');
}

$('ask-workspace').onclick=async()=>{const b=$('ask-workspace');if(!$('conversation-text').value.trim()){notice('Write your question first.',true);return}b.disabled=true;const payload={workspace:selectedWorkspace,opportunity_id:selectedOpportunity,chat_id:selectedChat,text:$('conversation-text').value,mode:$('conversation-mode').value,document_id:$('conversation-mode').value==='revise_document'?documentContext:null,draft_id:$('conversation-mode').value==='revise_proposal'?proposalContext:null};notice('Preparing an answer for this conversation…');try{const result=await api('/api/conversation/ask',payload);await openConversation(payload.workspace,payload.opportunity_id,payload.chat_id);if(result.document_id&&payload.mode==='revise_document'){const area=document.createElement('textarea');area.id='document-suggestion';area.hidden=true;area.value=result.answer;$('conversation-feed').append(area);const use=document.createElement('button');use.dataset.action='use-document-suggestion';use.dataset.id=result.document_id;use.textContent='Review suggested document changes';$('conversation-feed').append(use)}if(result.draft_id&&payload.mode==='revise_proposal'){const area=document.createElement('textarea');area.id='proposal-suggestion';area.hidden=true;area.value=result.answer;$('conversation-feed').append(area);const use=document.createElement('button');use.dataset.action='use-proposal-suggestion';use.dataset.id=result.draft_id;use.textContent='Review revised proposal';$('conversation-feed').append(use)}$('conversation-feed').scrollTop=$('conversation-feed').scrollHeight;notice('Answer saved. Nothing was sent to a client.')}catch(e){notice(e.message,true)}finally{b.disabled=false}};

function renderPlatforms(){
 $('platform-cards').innerHTML=platforms.map(p=>`<article class="panel"><h2>${esc(p.name)}</h2><span class="badge">${p.automatic_discovery?'Public feed available':'Assisted page reading'}</span><p class="small">${p.id==='contra'?'Use Connections to check native Contra access.':'Account access: not verified. Use your device account when needed.'}</p><button data-action="platform-profile" data-platform="${esc(p.id)}">Prepare my profile</button><button class="secondary" data-action="device-tools" data-platform="${esc(p.id)}">Set up Safari tools</button><details><summary>Hosted browser · hosting not verified</summary><p class="small">The current Hugging Face host cannot provide the required browser sandbox. Use Safari tools or your own browser.</p><button class="secondary" data-action="platform-open" data-platform="${esc(p.id)}">Check hosted browser</button></details><a href="${esc(p.url)}" target="_blank" rel="noopener">Open on my device instead</a></article>`).join('');
}
async function browserCommand(action,extra={}){const r=await api('/api/browser',{action,platform:activePlatform,...extra});if(r.message)$('browser-status').textContent=r.message;return r}
function updateBrowserFrame(){if(!browserRunning||document.hidden||frameBusy)return;frameBusy=true;$('browser-screen').src='/api/browser/frame?t='+Date.now()}
$('browser-screen').onload=()=>{frameBusy=false;$('browser-screen').hidden=false};
$('browser-screen').onerror=()=>{frameBusy=false;browserRunning=false;$('browser-status').textContent='The browser screen is unavailable. Open the platform browser again, or use the platform on your own device.'};
$('browser-screen').onclick=async e=>{const bounds=e.target.getBoundingClientRect();try{const approved=$('browser-approve').checked;$('browser-approve').checked=false;await browserCommand('click',{x:Math.round((e.clientX-bounds.left)*1024/bounds.width),y:Math.round((e.clientY-bounds.top)*768/bounds.height),approved});updateBrowserFrame()}catch(err){notice(err.message,true)}};
setInterval(updateBrowserFrame,2000);
$('browser-sensitive').onchange=()=>{$('browser-text').type=$('browser-sensitive').checked?'password':'text'};
async function platformAction(action,b){
 if(action==='device-tools'){activePlatform=b.dataset.platform;try{deviceProfiles[activePlatform]=await api('/api/platform-profile?id='+encodeURIComponent(activePlatform))}catch(e){deviceProfiles[activePlatform]=null}$('device-profile-name').textContent=platforms.find(p=>p.id===activePlatform).name;$('device-profile-reviewed').checked=false;jump('device-tools');return}
 if(action==='copy-page-reader'){const copied=await copyDeviceTool(readerBookmarklet());notice(copied?'Page reader copied. Follow the bookmark steps below.':'Select and copy the tool text in the window, then follow the bookmark steps.');return}
 if(action==='copy-profile-filler'){if(!$('device-profile-reviewed').checked)throw Error('Review and confirm your saved platform profile first.');const fields=deviceProfiles[activePlatform];if(!fields)throw Error('Prepare and save your platform profile first.');const copied=await copyDeviceTool(profileBookmarklet(fields));notice(copied?'Profile filler copied. Keep this personal bookmark private.':'Select and copy the tool text in the window. Keep this personal bookmark private.');return}

 if(action==='platform-profile'){
  activePlatform=b.dataset.platform;const p=platforms.find(p=>p.id===activePlatform);const fields=await api('/api/platform-profile?id='+encodeURIComponent(activePlatform));
  $('profile-title').textContent=p.name+' · Your prepared profile';$('profile-fields').innerHTML=Object.entries(fields).map(([key,value])=>`<label>${esc({full_name:'Full name',first_name:'First name',last_name:'Last name',email:'Contact email',headline:'Profile headline',bio:'About you',skills:'Skills'}[key]||key)}${key==='bio'?`<textarea name="${key}" rows="5">${esc(value)}</textarea>`:`<input name="${key}" value="${esc(value)}">`}</label>`).join('');$('profile-builder').hidden=false;$('profile-builder').scrollIntoView({block:'start'});return;
 }
 if(action==='platform-open'){
  activePlatform=b.dataset.platform;$('browser-approve').checked=false;$('browser-reviewed').checked=false;const p=platforms.find(p=>p.id===activePlatform);notice('Opening your private browser…');await browserCommand('start');browserRunning=true;lastBrowserPage=null;$('browser-capture').hidden=true;$('browser-platform-name').textContent=p.name+' · sign in or open the signup page here';$('browser-draft').innerHTML=drafts.map(d=>`<option value="${d.id}">${esc(leads.find(l=>l.id===d.opportunity_id)?.company||'Message')} · ${esc(d.subject)}</option>`).join('');$('browser-document').innerHTML=documents.filter(d=>['resume','cover_letter','portfolio'].includes(d.kind)).map(d=>`<option value="${d.id}">${esc(friendlyDocument(d.name))}</option>`).join('');jump('platform-browser');updateBrowserFrame();notice('Browser ready. Tap a field on the page, then use Type on the page.');return;
 }
 if(action==='browser-stop'){await browserCommand('stop');browserRunning=false;$('browser-screen').hidden=true;jump('platforms');notice('Browser closed. Its login session was cleared.');return}
 if(action==='browser-type'){await browserCommand('type',{text:$('browser-text').value});$('browser-text').value='';updateBrowserFrame();return}
 if(action==='browser-back'){await browserCommand('back');updateBrowserFrame();return}
 if(action==='browser-tab'){await browserCommand('key',{key:'Tab'});updateBrowserFrame();return}
 if(action==='browser-scroll-up'||action==='browser-scroll-down'){await browserCommand('scroll',{direction:action.endsWith('up')?'up':'down'});updateBrowserFrame();return}
 if(action==='browser-fill-profile'){await browserCommand('fill',{confirmed:$('browser-reviewed').checked});updateBrowserFrame();return}
 if(action==='browser-fill-message'){await browserCommand('fill_message',{draft_id:Number($('browser-draft').value),confirmed:$('browser-reviewed').checked});updateBrowserFrame();return}
 if(action==='browser-upload'){await browserCommand('upload',{document_id:Number($('browser-document').value),index:Number($('browser-upload-index').value)-1,confirmed:$('browser-reviewed').checked});updateBrowserFrame();return}
 if(action==='browser-read'){
  lastBrowserPage=await browserCommand('read');const p=platforms.find(p=>new URL(lastBrowserPage.url).hostname===new URL(p.url).hostname||new URL(lastBrowserPage.url).hostname.endsWith('.'+new URL(p.url).hostname.replace(/^www\./,'')));
  if(!p)throw Error('Open an opportunity on a registered platform before saving it.');activePlatform=p.id;
  $('browser-page-url').textContent=lastBrowserPage.url;$('capture-title').value=lastBrowserPage.title;$('capture-description').value=lastBrowserPage.text;$('capture-company').value='';$('browser-capture').hidden=false;
  $('browser-candidates').innerHTML=lastBrowserPage.candidates.map((c,i)=>`<p><button class="secondary" data-action="browser-candidate" data-candidate="${i}">${esc(c.title)}</button></p>`).join('')||'No candidate listing links found. You can still save the current opportunity.';notice('Page read. Review the title, company, and requirements before saving.');return;
 }
 if(action==='browser-candidate'){const candidate=lastBrowserPage.candidates[Number(b.dataset.candidate)];await browserCommand('start',{url:candidate.url});$('browser-capture').hidden=true;updateBrowserFrame();return}
}
$('platform-profile-form').onsubmit=async e=>{e.preventDefault();try{await api('/api/platform-profile',{platform:activePlatform,fields:Object.fromEntries(new FormData(e.target))});notice('Profile saved. Open the platform browser to fill supported signup fields.')}catch(err){notice(err.message,true)}};
$('platform-form').onsubmit=async e=>{e.preventDefault();await run(()=>api('/api/platforms',Object.fromEntries(new FormData(e.target))),'Platform and workspace added. Automatic scraping is not enabled.');};
$('browser-save-form').onsubmit=async e=>{e.preventDefault();try{const p=platforms.find(p=>p.id===activePlatform);if(!lastBrowserPage)throw Error('Read the opportunity page first.');const result=await api('/api/add',{company:$('capture-company').value,title:$('capture-title').value,description:$('capture-description').value,url:lastBrowserPage.url,source:p.name,workspace:p.workspace});await refresh();notice(result.added?'Opportunity saved with its requirements and source link.':'This opportunity is already saved.');}catch(err){notice(err.message,true)}};

let deviceCapture=null;const deviceProfiles={};
function readerBookmarklet(){
 const origin=location.origin;
 return 'javascript:'+encodeURIComponent('('+function(app){
  if([...document.querySelectorAll('input[type=password]')].some(e=>e.getClientRects().length)){alert('Open an opportunity listing before using the page reader.');return}
  const source=new URL(location.href);for(const key of ['code','state','token','access_token','id_token','refresh_token','session','session_id','authorization'])source.searchParams.delete(key);
  const candidates=[...document.querySelectorAll('a[href]')].filter(e=>e.getClientRects().length&&/\/(?:jobs?|opportunities|projects?|viewjob)(?:\/|[?#])/.test(e.href)).map(e=>({title:e.innerText.trim().slice(0,200),url:e.href})).filter(e=>e.title).slice(0,60);
  const data={url:source.href,title:document.title,text:document.body.innerText.slice(0,24000),candidates};
  const w=window.open(app+'/#reader','otu-opportunity-reader');
  if(!w){alert('Allow Safari to open the OTU bot, then run this bookmark again.');return}
  let attempts=0;
  function receive(e){if(e.origin===app&&e.source===w&&e.data==='OTU_READER_READY'){w.postMessage({type:'OTU_PAGE_CAPTURE',page:data},app);clearInterval(timer);removeEventListener('message',receive)}}
  addEventListener('message',receive);
  const timer=setInterval(()=>{if(++attempts>120){clearInterval(timer);removeEventListener('message',receive);alert('The bot did not receive this page. Open Find opportunities in OTU and paste the listing link and requirements instead.');return}w.postMessage('OTU_READER_HELLO',app)},1000);
 }.toString()+')('+JSON.stringify(origin)+')');
}
function profileBookmarklet(fields){
 return 'javascript:'+encodeURIComponent('('+function(fields){
  if(!confirm('Fill your reviewed profile details on this page? Nothing will be submitted.'))return;
  const patterns={first_name:/first.?name|given.?name/i,last_name:/last.?name|family.?name|surname/i,full_name:/full.?name|display.?name|^name name/i,email:/\bemail\b/i,headline:/headline|professional.?title/i,bio:/\bbio\b|about.?me|professional.?summary/i,skills:/\bskills\b/i};let count=0;
  for(const e of document.querySelectorAll('input,textarea')){
   if(!e.getClientRects().length||e.disabled||e.readOnly||['password','hidden','checkbox','radio','file','submit','button'].includes(e.type))continue;
   const descriptor=[e.name,e.id,e.placeholder,e.getAttribute('aria-label'),e.autocomplete,e.id?document.querySelector('label[for="'+CSS.escape(e.id)+'"]')?.innerText:''].filter(Boolean).join(' ').toLowerCase();
   if(/password|verification|one-time|credit|card number|social security|birth|tax|rate|salary/.test(descriptor))continue;
   for(const key of Object.keys(patterns)){if(fields[key]&&patterns[key].test(descriptor)){const setter=Object.getOwnPropertyDescriptor(e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set;setter.call(e,fields[key]);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));count++;break}}
  }
  alert(count+' fields filled. Review the page. No account was created and nothing was submitted.');
 }.toString()+')('+JSON.stringify(fields)+')');
}
function registeredPage(origin){try{const u=new URL(origin);return u.protocol==='https:'&&platforms.find(p=>{const h=new URL(p.url).hostname.replace(/^www\./,'');return u.hostname===h||u.hostname.endsWith('.'+h)})}catch(e){return null}}
window.addEventListener('message',e=>{
 const platform=registeredPage(e.origin);if(!platform||!e.source)return;
 if(e.data==='OTU_READER_HELLO'){e.source.postMessage('OTU_READER_READY',e.origin);return}
 if(e.data?.type!=='OTU_PAGE_CAPTURE')return;
 const page=e.data.page;if(!page||typeof page.url!=='string'||typeof page.text!=='string'||typeof page.title!=='string')return;
 let url;try{url=new URL(page.url);if(url.origin!==e.origin)return}catch(err){return}
 deviceCapture={url:page.url,platform};$('device-import-candidates').innerHTML=(Array.isArray(page.candidates)?page.candidates:[]).slice(0,60).filter(c=>{try{return typeof c.title==='string'&&new URL(c.url).origin===e.origin}catch(err){return false}}).map(c=>`<p><a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title.slice(0,200))}</a></p>`).join('')||'No candidate links found. Review the current listing below.';$('device-import-title').value=page.title.slice(0,250);$('device-import-company').value='';$('device-import-text').value=page.text.slice(0,24000);$('device-import-source').textContent=platform.name+' · '+page.url;jump('device-import');notice('Page received. Review and save only the opportunity details you need.');
});
$('device-import-form').onsubmit=async e=>{e.preventDefault();if(!deviceCapture){notice('Use the page reader on a platform listing first.',true);return}try{const p=deviceCapture.platform;const result=await api('/api/add',{company:$('device-import-company').value,title:$('device-import-title').value,description:$('device-import-text').value,url:deviceCapture.url,source:p.name,workspace:p.workspace});await refresh();await openConversation(p.workspace,result.id);deviceCapture=null;notice(result.added?'Opportunity saved. Its documents and conversation stay here.':'This opportunity was already saved. Its conversation is open.')}catch(err){notice(err.message,true)}};

async function copyDeviceTool(text){
 try{await navigator.clipboard.writeText(text);return true}catch(e){}
 const dialog=document.createElement('dialog');dialog.className='copy-tool-dialog';const heading=document.createElement('h2');heading.textContent='Copy your Safari tool';const explanation=document.createElement('p');explanation.textContent='Tap the text, select all, and choose Copy. Then close this window and edit the bookmark address.';const area=document.createElement('textarea');area.readOnly=true;area.value=text;area.rows=8;const close=document.createElement('button');close.textContent='Close';close.onclick=()=>{dialog.close();dialog.remove()};dialog.append(heading,explanation,area,close);document.body.append(dialog);dialog.showModal();area.focus({preventScroll:true});area.select();area.setSelectionRange(0,text.length);try{if(document.execCommand('copy')){dialog.close();dialog.remove();return true}}catch(e){}return false;
}

function renderContraResults(){
 const results=contraSummary.public_opportunities||[];
 $('contra-results-status').textContent=contraSummary.checked_at?`Last read: ${formatDate(contraSummary.checked_at)}. Results may be limited by your account and the pages checked. Pay, eligibility and deadlines still need verification.`:'Connect Contra in Connections, then check for opportunities.';
 $('contra-results').innerHTML=results.map((x,i)=>`<article class="panel"><span class="badge">${esc(x.kind)} · Needs review</span><h3>${esc(x.title)}</h3><p>${esc(contraPay(x))}</p><p class="small">Deadline: ${esc(x.deadline?formatDate(x.deadline):'Not confirmed')}. Entry cost and eligibility need verification.</p><p>${esc((x.description||'Open the listing for requirements.').slice(0,400))}</p><a href="${esc(x.url)}" target="_blank" rel="noopener">Read original opportunity</a><button class="secondary" data-action="contra-save" data-index="${i}">Save to My opportunities</button></article>`).join('')||'<p class="small">No verified opportunity links extracted yet. This does not mean no work is available.</p>';
}

function contraAmount(value){const match=/^USD:(-?\d+(?:\.\d+)?)$/.exec(String(value??''));return match?'$'+Number(match[1]).toLocaleString(undefined,{maximumFractionDigits:2}):String(value??'?')}
function contraPay(item){
 if(item.prize)return `Prize · ${item.prize.formatted||'See original terms'} · winning is not guaranteed`;
 const b=item.budget;if(!b)return 'Compensation not confirmed';
 return `Listed budget: ${contraAmount(b.feeMin)}–${contraAmount(b.feeMax)} (${b.type==='HourlyRateJobBudget'?'per hour':b.type||'terms not confirmed'}). Verify currency and scope on the listing.`;
}

async function viewDocument(id){
 activeDocument=await api('/api/document-preview?id='+id);const fileMatch=/^(?:Desmond_Glover_)?(.+?)_(Resume|Cover_Letter)_v(\d+)/i.exec(activeDocument.name);$('document-reader-title').textContent=fileMatch?fileMatch[1].replace(/_/g,' ')+' · '+(fileMatch[2].toLowerCase()==='resume'?'Résumé':'Cover letter')+' · Version '+fileMatch[3]:friendlyDocument(activeDocument.name);const editable=packages.some(p=>Object.values(JSON.parse(p.files)).includes(activeDocument.id))&&['resume','cover_letter'].includes(activeDocument.kind);$('document-editor').readOnly=!editable;$('document-revision-reviewed').disabled=!editable;document.querySelector('[data-action=save-document-version]').disabled=!editable;document.querySelector('[data-action=document-chat]').disabled=!editable;$('document-editor').value=activeDocument.text;$('document-revision-reviewed').checked=false;$('document-frame').hidden=true;$('pdf-page-image').removeAttribute('src');pdfPage=0;$('document-edit-label').hidden=false;jump('document-reader');$('document-reader').scrollTop=0;if(activeDocument.pages)showPdfPage();
}
function renderDeveloperRequests(){
 const relevant=developerRequests.filter(r=>r.workspace===selectedWorkspace&&r.opportunity_id===selectedOpportunity&&(r.chat_id||null)===selectedChat);
 $('developer-request-list').innerHTML=`<p class="small">Shared project memory: ${esc(knowledge.version||'not loaded')}. This assistant cannot read or message the private ChatGPT thread.</p>`+relevant.map(r=>`<article class="panel"><strong>${esc(r.status)}</strong><p class="message-text">${esc(r.text)}</p>${r.reply?`<p class="message-text">Developer: ${esc(r.reply)}</p>`:''}</article>`).join('');
}

function renderSidebar(){
 const query=($('chat-search').value||'').toLowerCase(),project=$('project-filter').value,view=$('chat-view').value;
 $('recent-chats').innerHTML=chatThreads.map((t,index)=>({...t,index})).filter(t=>(t.title+' '+t.workspace).toLowerCase().includes(query)&&(!project||t.project_id===project)&&(view==='trash'?t.trashed:view==='archived'?t.archived&&!t.trashed:!t.archived&&!t.trashed)).map(t=>`<div class="recent-chat ${t.id===selectedChat&&t.workspace===selectedWorkspace&&t.opportunity_id===selectedOpportunity?'selected':''}" draggable="true" data-chat-key="${esc(t.key)}"><button class="recent-open" data-action="open-recent" data-chat-index="${t.index}">${t.pinned?'★ ':''}${esc(t.title)}<small>${esc(projects.find(p=>p.id===t.project_id)?.name||t.workspace)}${t.opportunity_id?' · Opportunity':''}</small></button><button class="recent-rename" data-ops="chat-menu" data-chat-key="${esc(t.key)}" aria-label="Options for ${esc(t.title)}">···</button></div>`).join('')||'<p class="small">No conversations here yet.</p>';
}
function updateSidebar(){
 const collapsed=document.body.classList.contains('sidebar-collapsed'),open=document.body.classList.contains('sidebar-open');
 $('sidebar-toggle').setAttribute('aria-expanded',String(innerWidth<=1100?open:!collapsed));
 $('sidebar-backdrop').hidden=!(open&&innerWidth<=1100);$('sidebar-toggle').setAttribute('aria-label',open||!collapsed?'Collapse navigation':'Expand navigation');
}
function closeSidebar(){document.body.classList.remove('sidebar-open');updateSidebar()}
$('sidebar-toggle').onclick=()=>{if(innerWidth<=1100)document.body.classList.toggle('sidebar-open');else{document.body.classList.toggle('sidebar-collapsed');localStorage.setItem('otu-sidebar-collapsed',String(document.body.classList.contains('sidebar-collapsed')))}updateSidebar()};
$('sidebar-backdrop').onclick=closeSidebar;
if(localStorage.getItem('otu-sidebar-collapsed')==='true')document.body.classList.add('sidebar-collapsed');
for(const button of $('app-sidebar').querySelectorAll('button[data-tab],button.new-chat')){const title=button.textContent.trim(),space=title.indexOf(' ');if(button.closest('.nav-tools')){button.setAttribute('aria-label',title);button.title=title;continue}button.setAttribute('aria-label',title.slice(space+1));button.title=title.slice(space+1);button.innerHTML='<span class="nav-icon" aria-hidden="true">'+esc(title.slice(0,space))+'</span><span class="nav-label">'+esc(title.slice(space+1))+'</span>'}
$('sidebar-search').onclick=()=>{document.body.classList.remove('sidebar-collapsed');if(innerWidth<=1100)document.body.classList.add('sidebar-open');document.body.classList.toggle('search-open');const open=document.body.classList.contains('search-open');$('sidebar-search').setAttribute('aria-expanded',String(open));updateSidebar();if(open)$('chat-search').focus({preventScroll:true});else{$('chat-search').value='';renderSidebar()}};
document.querySelector('header').prepend(document.querySelector('.sidebar-top'));
$('workspace-menu').querySelector('.header-menu-content').append($('version'));
updateSidebar();addEventListener('resize',updateSidebar);
$('chat-search').oninput=renderSidebar;
$('rename-chat-form').onsubmit=async e=>{e.preventDefault();try{await api('/api/chat/rename',{id:renameTarget,title:$('rename-chat-title').value});const listLoad=++chatListLoad;const rows=await api('/api/chat-threads');if(listLoad===chatListLoad)chatThreads=rows;renderSidebar();$('rename-chat-dialog').close();if(selectedChat===renameTarget){$('conversation-title').textContent=$('rename-chat-title').value;$('pane-title').textContent=$('rename-chat-title').value}}catch(err){notice(err.message,true)}};
$('cancel-rename').onclick=()=>$('rename-chat-dialog').close();
function openDocumentPane(){closeWorkspacePanel(false);documentReturnFocus=document.activeElement;$('document-reader').hidden=false;document.querySelector('.layout').classList.add('document-open');syncDocumentMode();if(innerWidth<=760)$('document-reader').focus()}
function closeDocumentPane(restore=true){$('document-reader').hidden=true;document.querySelector('.layout').classList.remove('document-open');syncDocumentMode();if(restore){const target=documentReturnFocus?.isConnected&&documentReturnFocus.getClientRects().length&&!documentReturnFocus.matches('input,textarea,select')?documentReturnFocus:$('workspace-menu').querySelector('summary');target.focus({preventScroll:true})}}
function syncWorkspaceLayers(){
 const doc=!$('document-reader').hidden,panel=!$('workspace-panel').hidden,modal=(doc||panel)&&innerWidth<=1100;
 for(const el of [document.querySelector('header'),$('main-content'),$('app-sidebar')])el.inert=modal;
 $('panel-backdrop').hidden=!modal;
 for(const [el,visible] of [[$('document-reader'),doc],[$('workspace-panel'),panel]]){el.setAttribute('role',modal&&visible?'dialog':'complementary');if(modal&&visible)el.setAttribute('aria-modal','true');else el.removeAttribute('aria-modal')}
}
function syncDocumentMode(){syncWorkspaceLayers()}
addEventListener('resize',syncWorkspaceLayers);
document.addEventListener('keydown',e=>{
 if(document.querySelector('dialog[open]'))return;
 if(e.key==='Escape'){closeSidebar();$('workspace-menu').open=false;document.querySelector('.composer-options').open=false;if(!$('document-reader').hidden){e.preventDefault();closeDocumentPane()}else if(activePanel){e.preventDefault();closeWorkspacePanel()}}
 const modal=document.querySelector('aside[aria-modal="true"]');if(e.key==='Tab'&&modal){const controls=[...modal.querySelectorAll('button,input,textarea,select,a[href],summary')].filter(el=>!el.disabled&&el.getClientRects().length),first=controls[0],last=controls.at(-1);if(e.shiftKey&&(document.activeElement===first||document.activeElement===modal)){e.preventDefault();last?.focus({preventScroll:true})}else if(!e.shiftKey&&(document.activeElement===last||document.activeElement===modal)){e.preventDefault();first?.focus({preventScroll:true})}}
});
document.addEventListener('click',e=>{if(!e.target.closest('#workspace-menu'))$('workspace-menu').open=false;if(!e.target.closest('.nav-tools'))document.querySelector('.nav-tools').open=false;if(!e.target.closest('.composer-options'))document.querySelector('.composer-options').open=false;document.querySelectorAll('.message-menu[open]').forEach(menu=>{if(!menu.contains(e.target))menu.open=false})});
$('conversation-text').addEventListener('input',()=>{const box=$('conversation-text');box.style.height='auto';box.style.height=Math.min(box.scrollHeight,112)+'px'});

// Anchor the shell to Safari's visible viewport, including its keyboard pan offset.
// Coalesce resize/scroll events so the browser and app do not repeatedly reflow each other.
let viewportFrame=0,viewportBaseline=innerHeight;
function fitAppHeight(){
 if(viewportFrame)return;
 viewportFrame=requestAnimationFrame(()=>{viewportFrame=0;const v=window.visualViewport;
 // Pinch zoom must remain controlled by the user.
 if(v&&Math.abs(v.scale-1)>.05)return;
 const feed=$('conversation-feed'),atBottom=feed.scrollHeight-feed.scrollTop-feed.clientHeight<50,oldTop=feed.scrollTop;
 const height=Math.round(v?.height||innerHeight),editable=document.activeElement?.matches('input,textarea,[contenteditable=true]');
 if(!editable)viewportBaseline=innerHeight;
 document.body.classList.toggle('keyboard-open',!!editable&&viewportBaseline-height>120);
 document.documentElement.style.setProperty('--app-height',height+'px');
 document.documentElement.style.setProperty('--app-top',Math.round(v?.offsetTop||0)+'px');
 feed.scrollTop=atBottom?feed.scrollHeight:oldTop;
 });
}
document.addEventListener('focusin',fitAppHeight);document.addEventListener('focusout',()=>requestAnimationFrame(fitAppHeight));
fitAppHeight();window.visualViewport?.addEventListener('resize',fitAppHeight);window.visualViewport?.addEventListener('scroll',fitAppHeight);addEventListener('resize',fitAppHeight);

// Dictation only fills editable text. It never sends messages or invokes AI.
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
let speech=null,speechActive=false,speechBase='',speechFinal='',speechAccept=false;
function stopDictation(){if(speechActive&&speech)speech.stop()}
function speechStatus(text){$('dictation-status').textContent=text}
$('dictate-message').onclick=()=>{
 stopAnswer();
 if(speechActive){stopDictation();return}
 if(!SpeechRecognition){speechStatus('Use the microphone on your iPad keyboard: tap the message box, then the keyboard microphone. Browser dictation is unavailable here.');$('conversation-text').focus({preventScroll:true});return}
 speechAccept=true;speechBase=$('conversation-text').value;speechFinal='';const scope=[selectedWorkspace,selectedOpportunity,selectedChat].join(':');speech=new SpeechRecognition();
 speech.lang=navigator.language||'en-US';speech.continuous=true;speech.interimResults=true;
 speech.onstart=()=>{speechActive=true;$('dictate-message').textContent='■ Stop';$('dictate-message').setAttribute('aria-pressed','true');speechStatus('Listening… Tap Stop when finished. Your browser may process speech online. Nothing is sent to OTU until you press Send.');$('ask-workspace').disabled=true;$('conversation-text').readOnly=true};
 speech.onresult=event=>{if(!speechAccept||scope!==[selectedWorkspace,selectedOpportunity,selectedChat].join(':'))return;let interim='';for(let i=event.resultIndex;i<event.results.length;i++){if(event.results[i].isFinal)speechFinal+=event.results[i][0].transcript+' ';else interim+=event.results[i][0].transcript}const box=$('conversation-text');box.value=(speechBase+(speechBase?' ':'')+speechFinal+interim).slice(0,4000);box.dispatchEvent(new Event('input'));};
 speech.onerror=event=>{speechStatus(event.error==='not-allowed'?'Microphone permission was denied. Allow it in Safari website settings, or use the keyboard microphone.':'Dictation could not continue. Your text is kept. Try the keyboard microphone.');};
 speech.onend=()=>{speechActive=false;$('dictate-message').textContent='🎙 Speak';$('dictate-message').setAttribute('aria-pressed','false');$('conversation-text').readOnly=false;$('ask-workspace').disabled=!state.ai_configured;if($('dictation-status').textContent.startsWith('Listening'))speechStatus('Dictation finished. Review or edit your words, then press Send.');};
 try{speech.start()}catch(e){speechStatus('Dictation could not start. Use the keyboard microphone instead.')}
};
// End capture before navigating away; recognition cannot carry text into another conversation.
document.addEventListener('click',e=>{if(e.target.closest('[data-tab],[data-action],.recent-open,#save-work-note')){speechAccept=false;stopDictation()}},true);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopDictation()});
document.addEventListener('click',e=>{if(document.body.classList.contains('sidebar-open')&&!e.target.closest('#app-sidebar')&&!e.target.closest('#sidebar-toggle')&&!e.target.closest('.sidebar-top')){closeSidebar()}},true);

function showPdfPage(){
 if(!activeDocument)return;$('document-frame').hidden=false;$('document-edit-label').hidden=true;$('pdf-page-error').textContent='';$('pdf-page-status').textContent=`Page ${pdfPage+1} of ${activeDocument.pages}`;document.querySelector('[data-action=pdf-previous]').disabled=pdfPage<=0;document.querySelector('[data-action=pdf-next]').disabled=pdfPage+1>=activeDocument.pages;$('pdf-page-image').src='/api/document-page?id='+activeDocument.id+'&page='+pdfPage;
}
$('pdf-page-image').onerror=()=>{$('pdf-page-error').textContent='This page could not be displayed. Choose Read and edit text to continue.'};

function fileScope(){return {workspace:selectedWorkspace,opportunity_id:selectedOpportunity,chat_id:selectedChat}}
function bytesLabel(n){return n>=1024**3?(n/1024**3).toFixed(2)+' GiB':(n/1024**2).toFixed(1)+' MiB'}
async function updateFileStorage(){const s=await api('/api/files/storage');const meter=$('file-storage-meter');if(meter)meter.textContent=bytesLabel(s.used)+' saved · '+bytesLabel(s.reserved)+' uploading · '+bytesLabel(s.allowance)+' app allowance. Bucket capacity may differ.';return s}
async function loadConversationFiles(){
 const scope=fileScope(),stamp=JSON.stringify(scope);const params=new URLSearchParams(Object.entries(scope).filter(([k,v])=>v!==null));const rows=await api('/api/files/list?'+params);
 if(stamp!==JSON.stringify(fileScope()))return;
 $('conversation-files').hidden=!rows.length;
 $('conversation-file-list').innerHTML=rows.map(f=>`<div class="file-row"><span>${esc(f.name)} · ${bytesLabel(f.size)}</span>${f.state==='complete'?`<a href="/api/files/download?id=${f.id}">Open / save file</a>${/\.(png|jpe?g|webp|gif)$/i.test(f.name)?`<button type="button" class="secondary" data-action="view-photo" data-file="${f.id}">View photo</button>`:''}<details><summary>File options</summary><button type="button" class="secondary" data-action="remove-file" data-file="${f.id}">Remove this file</button></details>`:`<span>Paused at ${Math.floor(f.received/f.size*100)}% · Select this file again to resume</span><button type="button" class="secondary" data-action="cancel-file" data-file="${f.id}">Remove unfinished upload</button>`}</div>`).join('');
}
$('attach-file').onclick=()=>$('chat-files').click();
$('photo-preview').onerror=()=>{$('photo-caption').textContent='This image cannot be previewed here. Use Open / save file to view the original.'};
$('close-photo').onclick=()=>$('photo-dialog').close();
document.addEventListener('click',async event=>{const b=event.target.closest('[data-file]');if(!b)return;try{if(b.dataset.action==='view-photo'){$('photo-preview').src='/api/files/photo?id='+b.dataset.file;$('photo-caption').textContent='Private image preview';$('photo-dialog').showModal()}else if(b.dataset.action==='remove-file'){if(!confirm('Remove this file from OTU? Keep your own original if you need it. Your career master files are unaffected.'))return;await api('/api/files/remove',{id:b.dataset.file,confirmed:true});await loadConversationFiles();await updateFileStorage()}else if(b.dataset.action==='cancel-file'){await api('/api/files/cancel',{id:b.dataset.file});await loadConversationFiles();await updateFileStorage()}}catch(e){notice(e.message,true)}});
$('chat-files').onchange=async()=>{
 const files=Array.from($('chat-files').files),scope=fileScope();$('attach-file').disabled=true;
 try{for(const file of files){
 if(file.size>1024**3)throw Error('Each file can be up to 1 GiB.');
 const key='otu-upload:'+JSON.stringify(scope)+':'+file.name+':'+file.size+':'+file.lastModified;
 let saved=localStorage.getItem(key),session=null;
 if(saved){try{session=await api('/api/files/status?id='+saved)}catch(e){localStorage.removeItem(key)}}
 if(!session||session.name!==file.name||session.size!==file.size)session=await api('/api/files/start',{...scope,name:file.name,size:file.size});
 localStorage.setItem(key,session.id);let offset=session.received;
 while(offset<file.size){const end=Math.min(offset+4*1024**2,file.size),chunk=new Uint8Array(await file.slice(offset,end).arrayBuffer());let binary='';for(let i=0;i<chunk.length;i+=32768)binary+=String.fromCharCode(...chunk.subarray(i,i+32768));const result=await api('/api/files/chunk',{id:session.id,offset,content:btoa(binary)});offset=result.received;notice('Uploading '+file.name+' · '+Math.floor(offset/file.size*100)+'%');}
 await api('/api/files/finish',{id:session.id});localStorage.removeItem(key);
 }notice('Files saved privately. They have not been sent to AI or a client.');await loadConversationFiles();await updateFileStorage();$('conversation-files').open=true;tab('files');
 }catch(e){notice(e.message+' If interrupted, select the same file again to resume.',true);await loadConversationFiles()}finally{$('attach-file').disabled=false;$('chat-files').value=''}
};
updateFileStorage().catch(()=>{});

function renderStatusReport(){
 const report=knowledge.status_report||{};
 $('status-report-basis').textContent='Updated '+(report.as_of||'not recorded')+' · '+(report.basis||'No report yet.');
 $('status-report-overview').textContent=report.overview||'';
 $('status-report-items').innerHTML=(report.opportunities||[]).map(item=>`<article class="panel"><span class="badge">${esc(item.status)}</span><h2>${esc(item.name)}</h2><p>${esc(item.evidence)}</p><p><strong>Next:</strong> ${esc(item.next)}</p><details><summary>What supports this status?</summary><p>${esc(item.verification)}</p></details></article>`).join('');
 $('status-report-foundation').innerHTML=`<article class="panel"><h2>Keep the progress already made</h2><p>${esc(report.services)}</p><p>${esc(report.portfolio)}</p><p>${esc(report.continuity)}</p><p>${esc(report.next_focus)}</p></article>`;
}

let audioAnswer=null,audioUtterance=null;
function stopAnswer(){
 const old=audioAnswer;audioAnswer=null;audioUtterance=null;window.speechSynthesis?.cancel();
 if(old){old.textContent='🔊 Read aloud';old.setAttribute('aria-pressed','false');const stop=old.parentElement?.querySelector('[data-action=stop-answer]');if(stop)stop.hidden=true}
}
function readAnswer(button){
 if(!window.speechSynthesis||!window.SpeechSynthesisUtterance){notice('Read aloud is unavailable in this browser. Use your device’s spoken-content accessibility controls.',true);return}
 speechAccept=false;stopDictation();
 const synth=window.speechSynthesis;
 if(audioAnswer===button&&audioUtterance){if(synth.paused){synth.resume();button.textContent='⏸ Pause'}else{synth.pause();button.textContent='▶ Resume'}return}
 stopAnswer();audioAnswer=button;const utterance=new SpeechSynthesisUtterance(button.closest('article').querySelector('.message-text').textContent);audioUtterance=utterance;
 const language=navigator.language||'en-US',voices=synth.getVoices(),voice=voices.find(v=>v.localService&&v.lang===language)||voices.find(v=>v.localService&&v.lang.startsWith(language.split('-')[0]));if(voice)utterance.voice=voice;utterance.lang=language;utterance.rate=1;
 button.textContent='⏸ Pause';button.setAttribute('aria-pressed','true');button.parentElement.querySelector('[data-action=stop-answer]').hidden=false;
 utterance.onend=()=>{if(audioUtterance===utterance)stopAnswer()};utterance.onerror=event=>{if(audioUtterance===utterance){stopAnswer();if(!['canceled','interrupted'].includes(event.error))notice('Your browser could not read this answer aloud. Try its spoken-content accessibility controls.',true)}};
 try{synth.speak(utterance)}catch(error){stopAnswer();notice('Read aloud could not start in this browser. Try your device’s spoken-content controls.',true)}
}
document.addEventListener('click',event=>{if(event.target.closest('[data-action=new-chat],[data-action=open-recent],[data-action=conversation],[data-action=workspace-conversation]'))stopAnswer()},true);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAnswer()});
addEventListener('pagehide',stopAnswer);

// Projects organize chats without changing their original source or context.
let projects=[],menuChat=null,organizeMode=null,mailRows=[],mailNext=null,mailCurrent=null,mailGeneration=0,mailReadGeneration=0;
async function loadProjects(){projects=await api('/api/projects');const saved=$('project-filter').value;$('project-filter').innerHTML='<option value="">All projects</option>'+projects.map(p=>`<option value="${esc(p.id)}" ${p.id===saved?'selected':''}>${esc(p.name)}</option>`).join('');$('project-filter').value=projects.some(p=>p.id===saved)?saved:'';}
$('project-filter').onchange=renderSidebar;$('chat-view').onchange=renderSidebar;
function showChatMenu(key){menuChat=chatThreads.find(t=>t.key===key);if(!menuChat)return;$('chat-actions-title').textContent=menuChat.title;const actions=menuChat.trashed?[['restore','Restore conversation']]:[['rename','Rename'],['pin',menuChat.pinned?'Unpin':'Pin'],['move','Move to project'],['archive',menuChat.archived?'Unarchive':'Archive'],['trash','Delete · move to Trash']];$('chat-actions-buttons').innerHTML=actions.map(([a,label])=>`<button data-ops="chat-${a}">${label}</button>`).join('');$('chat-actions-dialog').showModal();}
function showOrganize(mode){organizeMode=mode;$('organize-title').textContent={rename:'Rename conversation',move:'Move to project','new-project':'Create project','mail-folder':'Create mail folder'}[mode];$('organize-text-label').hidden=mode==='move';$('organize-project-label').hidden=mode!=='move';$('organize-text').required=mode!=='move';$('organize-text').value=mode==='rename'?menuChat.title:'';$('organize-project').innerHTML=projects.map(p=>`<option value="${esc(p.id)}" ${menuChat?.project_id===p.id?'selected':''}>${esc(p.name)}</option>`).join('');$('organize-dialog').showModal();}
async function updateChat(action,extra={}){await api('/api/chat/organize',{key:menuChat.key,action,...extra});chatThreads=await api('/api/chat-threads');renderSidebar();if(action==='rename'&&menuChat.id===selectedChat&&menuChat.workspace===selectedWorkspace&&menuChat.opportunity_id===selectedOpportunity){$('conversation-title').textContent=extra.title;$('pane-title').textContent=extra.title}notice(action==='trash'?'Moved to Trash. Restore it from the conversation list whenever you need it.':'Conversation updated. Messages and files are kept.');}
$('organize-form').onsubmit=async event=>{event.preventDefault();try{const name=$('organize-text').value.trim();if(organizeMode==='new-project'){const r=await api('/api/projects',{name});await loadProjects();$('project-filter').value=r.id;renderSidebar()}else if(organizeMode==='mail-folder'){await api('/api/mail/organize',{action:'folder',name});await loadMail()}else await updateChat(organizeMode,organizeMode==='move'?{project_id:$('organize-project').value}:{title:name});$('organize-dialog').close()}catch(e){notice(e.message,true)}};
document.addEventListener('click',async event=>{const b=event.target.closest('[data-ops]');if(!b)return;const op=b.dataset.ops;b.disabled=true;try{
 if(op==='chat-menu')showChatMenu(b.dataset.chatKey);
 else if(op==='close-chat-menu')$('chat-actions-dialog').close();
 else if(op==='cancel-organize')$('organize-dialog').close();
 else if(['new-project','mail-folder'].includes(op))showOrganize(op);
 else if(op.startsWith('chat-')){const action=op.slice(5);$('chat-actions-dialog').close();if(['rename','move'].includes(action))showOrganize(action);else if(action!=='trash'||confirm('Move this conversation to Trash? Its messages, files and opportunity will be kept.'))await updateChat(action,{confirmed:true});}
 else if(op==='mail-open')await openMail(b.dataset.threadId);
 else if(op==='mail-more')await loadMail(true);
 else if(op==='mail-save')await saveMailOrganization();
 else if(op==='mail-reply'){const lead=leads.find(l=>l.id===Number($('mail-opportunity').value));if(!lead)throw Error('Link this mail to an opportunity first.');await api('/api/draft',{id:lead.id});await refresh();tab('drafts');notice('An unsent draft is ready to edit and review. Check the recipient and subject before sending.');}
 }catch(e){notice(e.message,true)}finally{b.disabled=false}});
let holdTimer=null,holdStart=null,heldKey=null,suppressClickUntil=0;
function cancelHold(){clearTimeout(holdTimer);holdTimer=null;holdStart=null;}
$('recent-chats').addEventListener('pointerdown',e=>{if(e.target.closest('.recent-rename')||e.button!==0)return;const row=e.target.closest('[data-chat-key]');if(!row)return;holdStart={x:e.clientX,y:e.clientY};heldKey=row.dataset.chatKey;holdTimer=setTimeout(()=>{suppressClickUntil=Date.now()+900;showChatMenu(heldKey);cancelHold()},600)});
$('recent-chats').addEventListener('pointermove',e=>{if(holdStart&&Math.hypot(e.clientX-holdStart.x,e.clientY-holdStart.y)>10)cancelHold()});
for(const event of ['pointerup','pointercancel','scroll','dragstart'])$('recent-chats').addEventListener(event,cancelHold);
$('recent-chats').addEventListener('click',e=>{if(Date.now()<suppressClickUntil){e.preventDefault();e.stopImmediatePropagation()}},true);
$('recent-chats').addEventListener('contextmenu',e=>{const row=e.target.closest('[data-chat-key]');if(row){e.preventDefault();cancelHold();showChatMenu(row.dataset.chatKey)}});
$('recent-chats').addEventListener('dragstart',e=>{const row=e.target.closest('[data-chat-key]');if(row)e.dataTransfer.setData('text/otu-chat',row.dataset.chatKey)});
$('project-filter').addEventListener('dragover',e=>e.preventDefault());
$('project-filter').addEventListener('drop',async e=>{e.preventDefault();const key=e.dataTransfer.getData('text/otu-chat');if(!key)return;menuChat=chatThreads.find(t=>t.key===key);if(menuChat)showOrganize('move')});
async function loadMail(more=false){
 const generation=++mailGeneration,box=$('mail-box').value,search=$('mail-search').value;const previous=mailRows; $('mail-status').textContent='Loading mail…';
 try{const r=await api('/api/mail?'+new URLSearchParams({box,search,...(more&&mailNext?{page:mailNext}:{})}));if(generation!==mailGeneration)return;mailNext=r.next_page;mailRows=more?[...previous,...r.items]:r.items;const selected=$('mail-box').value;$('mail-box').querySelectorAll('[data-custom-folder]').forEach(el=>el.remove());for(const f of r.folders){const o=document.createElement('option');o.value=f.id;o.textContent=f.name;o.dataset.customFolder='true';$('mail-box').append(o)}$('mail-box').value=selected;$('mail-more').hidden=!mailNext;
 $('mail-status').textContent=r.local?(box==='outbox'?'Approved messages wait for you to press Send. Delivery unknown needs a Gmail check before any retry.':'Unsent drafts created in OTU. Gmail-only drafts are available through Open Gmail.'):'Checked '+formatDate(r.checked)+'. Opening a thread does not mark it read in Gmail.';
 $('mail-items').innerHTML=mailRows.map(r=>r.opportunity_id!==undefined&&r.status?`<article class="panel"><strong>${esc(r.subject)}</strong><p>${esc(r.recipient)} · ${esc(r.status)}</p><button data-tab="drafts">Review draft &amp; attachments</button></article>`:`<button class="mail-item secondary" data-ops="mail-open" data-thread-id="${esc(r.id)}"><strong>${esc(r.subject||r.snippet||'Open mail conversation')}</strong><small>${esc(r.sender||'')}</small>${r.organization?.followup?'<small>Follow up '+esc(r.organization.followup)+'</small>':''}</button>`).join('')||empty('No mail here.');
 }catch(e){if(generation===mailGeneration)$('mail-status').textContent=e.message;throw e}
}
$('mail-box').onchange=()=>{mailCurrent=null;$('mail-reader').innerHTML='';loadMail().catch(()=>{})};$('mail-search-form').onsubmit=e=>{e.preventDefault();loadMail().catch(()=>{})};
async function openMail(id){const generation=mailGeneration,reading=++mailReadGeneration;const r=await api('/api/mail/thread?id='+encodeURIComponent(id));if(generation!==mailGeneration||reading!==mailReadGeneration)return;mailCurrent=r;const m=r.organization||{};$('mail-reader').innerHTML=`<h2>${esc(r.subject)}</h2><a href="https://mail.google.com/mail/u/0/#all/${encodeURIComponent(r.id)}" target="_blank" rel="noopener">Open this thread in Gmail</a><label>OTU folder<select id="mail-folder"><option value="">No folder</option>${[...$('mail-box').options].filter(o=>o.dataset.customFolder).map(o=>`<option value="${esc(o.value)}" ${m.folder_id===o.value?'selected':''}>${esc(o.textContent)}</option>`).join('')}</select></label><label>Related opportunity<select id="mail-opportunity"><option value="">None yet</option>${leads.map(l=>`<option value="${l.id}" ${m.opportunity_id===l.id?'selected':''}>${esc(l.company+' · '+l.title)}</option>`).join('')}</select></label><label>Follow up on<input id="mail-followup" type="date" value="${esc(m.followup||'')}"></label><button data-ops="mail-save">Save organization</button><button data-ops="mail-reply" class="secondary">Prepare an outreach draft</button>`+r.messages.map(m=>`<article class="panel"><strong>${esc(m.sender)}</strong><p>${esc(m.recipient)} · ${formatDate(m.date)}</p><p class="message-text">${esc(m.body)}</p>${m.attachments?.length?'<p>Attachments: '+esc(m.attachments.join(', '))+'. Open Gmail to download.</p>':''}</article>`).join('');$('mail-reader').scrollIntoView({block:'start',behavior:'smooth'});}
async function saveMailOrganization(){await api('/api/mail/organize',{thread_id:mailCurrent.id,folder_id:$('mail-folder').value,opportunity_id:$('mail-opportunity').value,followup:$('mail-followup').value});notice('Mail organization saved in OTU. Gmail unchanged.');}
$('complete-restore-form').onsubmit=async event=>{event.preventDefault();if(!confirm('Merge this complete backup? Existing work stays. A checkpoint will be saved and sending approvals reset.'))return;const button=event.submitter;button.disabled=true;let session;try{const file=$('complete-restore-file').files[0];if(file.size>1024**3)throw Error('This restore uploader supports ZIPs up to 1 GiB. Ask the developer to recover a larger backup.');session=await api('/api/files/start',{...fileScope(),name:file.name,size:file.size});let offset=0;while(offset<file.size){const bytes=new Uint8Array(await file.slice(offset,offset+4*1024**2).arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));offset=(await api('/api/files/chunk',{id:session.id,offset,content:btoa(binary)})).received;notice('Loading recovery copy · '+Math.floor(offset/file.size*100)+'%')}await api('/api/files/finish',{id:session.id});const r=await api('/api/restore-complete',{id:session.id,confirmed:true});notice(r.message);await refresh()}catch(e){notice(e.message,true)}finally{button.disabled=false;if(session)await api('/api/files/remove',{id:session.id,confirmed:true}).catch(()=>{})}};
