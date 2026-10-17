import os,sys,tempfile,subprocess,time,urllib.request,json,re,socket
# Only a trusted local fixture is opened; inference and speech recognition are mocked.
with socket.socket() as listener:
 listener.bind(('127.0.0.1',0));fixture_port=listener.getsockname()[1]
sys.path[:0]=[os.getcwd(),os.path.join(os.getcwd(),'tests')]
from engine import Engine
from test_applications import MASTER
from playwright.sync_api import sync_playwright,expect
folder=tempfile.mkdtemp();engine=Engine(folder);engine.import_file('Master_Career_Resume_Fixture.txt',MASTER.replace('DESMOND L. GLOVER','EXAMPLE OWNER').encode());oid=engine.add({'company':'Example client','title':'CRM workflow','description':'CRM workflow setup','source':'Contra','workspace':'contra'})['id'];package=engine.create_package({'id':oid});did=package['files']['resume_pdf'];engine.add_work_note({'workspace':'contra','opportunity_id':oid,'text':'Original opportunity history retained.'})
wrapper='''import os,sys
sys.path.insert(0,os.getcwd())
import app
app.engine.ai_request=lambda payload:{'choices':[{'message':{'content':'EXAMPLE OWNER\\nA complete reviewed fixture document.\\nLocal test only.'}}]}
from http.server import ThreadingHTTPServer
ThreadingHTTPServer(('127.0.0.1',18874),app.Handler).serve_forever()
''';wrapper=wrapper.replace('18874',str(fixture_port));open('/tmp/otu_matrix_fixture.py','w').write(wrapper)
server=subprocess.Popen(['.venv/bin/python','/tmp/otu_matrix_fixture.py'],env={'PATH':os.environ['PATH'],'OTU_DATA_DIR':folder,'HF_INFERENCE_TOKEN':'fixture-only'})
base='http://127.0.0.1:'+str(fixture_port)
try:
 for _ in range(40):
  try:urllib.request.urlopen(base+'/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();errors=[];downloads=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('download',lambda d:downloads.append(d));context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
  page.add_init_script("""window.SpeechRecognition=class {start(){window.testSpeech=this;this.onstart()}stop(){this.onend()}}""")
  page.goto(base);expect(page.locator('#version')).to_have_text('v'+open('VERSION').read().strip());expect(page.locator('#conversation')).to_be_visible();expect(page.locator('#app-sidebar')).to_be_visible()
  page.locator('#conversation-text').fill('Existing text.');page.locator('#dictate-message').click();expect(page.locator('#dictate-message')).to_have_attribute('aria-pressed','true');expect(page.locator('#ask-workspace')).to_be_disabled()
  page.evaluate("testSpeech.onresult({resultIndex:0,results:[Object.assign([{transcript:'Please prepare my application.'}],{isFinal:true})]})")
  expect(page.locator('#conversation-text')).to_have_value('Existing text. Please prepare my application. ')
  page.locator('#dictate-message').click();expect(page.locator('#conversation-text')).not_to_have_attribute('readonly','');expect(page.locator('#dictation-status')).to_contain_text('Review or edit')
  page.locator('#dictate-message').click();page.locator('[data-action=new-chat]').click();page.wait_for_function('()=>selectedChat!==null');page.evaluate("testSpeech.onresult({resultIndex:0,results:[Object.assign([{transcript:'Late words must not appear'}],{isFinal:true})]})");expect(page.locator('#conversation-text')).to_have_value('')
  # Simulate a keyboard-shrunken visible viewport with Safari's pan offset.
  page.evaluate("Object.defineProperty(window.visualViewport,'height',{configurable:true,value:420});Object.defineProperty(window.visualViewport,'offsetTop',{configurable:true,value:80});window.visualViewport.dispatchEvent(new Event('resize'))")
  page.wait_for_timeout(100);assert page.evaluate("getComputedStyle(document.body).transform").endswith('80)');assert page.locator('#ask-workspace').bounding_box()['y']<500
  page.locator('#workspace-menu > summary').click();menu_bounds=page.locator('.header-menu-content').bounding_box();assert menu_bounds['y']+menu_bounds['height']<=500;page.locator('#workspace-menu').evaluate('(el)=>el.open=false')
  page.evaluate("delete window.visualViewport.height;delete window.visualViewport.offsetTop;window.visualViewport.dispatchEvent(new Event('resize'))");page.wait_for_timeout(100)
  from PIL import Image
  photo='/tmp/otu-upload-fixture.png';Image.new('RGB',(100,80),'green').save(photo)
  page.locator('#chat-files').set_input_files(photo);expect(page.locator('#status')).to_contain_text('Files saved privately');expect(page.locator('#conversation-file-list')).to_contain_text('otu-upload-fixture.png')
  page.locator('[data-action=view-photo]').click();expect(page.locator('#photo-dialog')).to_be_visible();page.wait_for_function('()=>document.getElementById("photo-preview").naturalWidth===100');page.locator('#close-photo').click();page.locator('#close-workspace-panel').click()
  large='/tmp/otu-upload-large.zip';open(large,'wb').write(b'x'*(9*1024*1024));page.locator('#chat-files').set_input_files(large);expect(page.locator('#attach-file')).to_be_enabled(timeout=20000);expect(page.locator('#conversation-file-list')).to_contain_text('otu-upload-large.zip')
  assert page.evaluate("document.getElementById('file-storage-meter').textContent.includes('5.00 GiB')");page.locator('#close-workspace-panel').click()
  page.locator('[data-action=new-chat]').click();page.wait_for_function('()=>selectedChat!==null');expect(page.locator('[data-action=new-chat]')).to_be_enabled();first=page.evaluate('selectedChat');assert first
  page.locator('#conversation-text').fill('Keep this first planning thread separate.');page.locator('.composer-options').evaluate('(el)=>el.open=true');page.locator('#save-work-note').click();expect(page.locator('#conversation-feed')).to_contain_text('first planning thread')
  page.locator('[data-action=new-chat]').click();page.wait_for_function('(first)=>selectedChat!==first',arg=first);expect(page.locator('[data-action=new-chat]')).to_be_enabled();second=page.evaluate('selectedChat');assert first!=second;expect(page.locator('#conversation-feed')).not_to_contain_text('first planning thread')
  page.locator('#sidebar-search').click();page.locator('#chat-search').fill('first planning');expect(page.locator('.recent-chat')).to_have_count(1);page.locator('.recent-rename').click();page.locator('[data-ops=chat-rename]').click();page.locator('#organize-text').fill('My income plan');page.locator('#organize-form button').first.click();expect(page.locator('#organize-dialog')).not_to_be_visible();page.locator('#chat-search').fill('My income plan');page.locator('.recent-open').click();expect(page.locator('#conversation-title')).to_have_text('My income plan')
  page.reload();expect(page.locator('#conversation-title')).to_have_text('My income plan');expect(page.locator('#conversation-feed')).to_contain_text('first planning thread')
  assert page.locator('.layout').bounding_box()['x']==0;assert round(page.locator('.layout').bounding_box()['width'])==1440
  page.wait_for_timeout(300);assert page.evaluate('otuMatrixStatus().frames')>0
  assert page.evaluate("(()=>{let a=document.getElementById('matrix-rain').getContext('2d').getImageData(0,0,400,400).data;for(let i=0;i<a.length;i+=4){if(a[i+1]>a[i]+30&&a[i+1]>60)return true}return false})()")
  page.locator('#workspace-menu > summary').click();page.locator('#matrix-toggle').click();page.locator('#workspace-menu').evaluate('(el)=>el.open=false');expect(page.locator('#matrix-rain')).to_have_attribute('data-mode','paused');frames=page.evaluate('otuMatrixStatus().frames');page.wait_for_timeout(200);assert page.evaluate('otuMatrixStatus().frames')==frames
  page.reload();expect(page.locator('#matrix-rain')).to_have_attribute('data-mode','paused');expect(page.locator('#conversation-title')).to_have_text('My income plan')
  page.locator('#workspace-menu > summary').click();page.locator('#matrix-toggle').click();page.locator('#workspace-menu').evaluate('(el)=>el.open=false');page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))");assert not page.evaluate('otuMatrixStatus().running');page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'))")
  page.evaluate("window.SpeechSynthesisUtterance=class {constructor(text){this.text=text}};Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{paused:false,getVoices:()=>[{name:'Alex',voiceURI:'fixture-alex',localService:true,lang:'en-US'},{name:'Samantha',voiceURI:'fixture-samantha',localService:true,lang:'en-US'}],speak(u){window.testUtterance=u},cancel(){this.paused=false},pause(){this.paused=true},resume(){this.paused=false}}})")
  page.evaluate("tab('status-report')");expect(page.locator('#status-report-items')).to_contain_text('GeekyAnts');expect(page.locator('#status-report-items')).to_contain_text('not sent');page.locator('#close-workspace-panel').click()
  page.locator('#conversation-text').fill('Keep this unfinished message.');chat_before=page.evaluate('[selectedWorkspace,selectedOpportunity,selectedChat]')
  page.locator('#sidebar-toggle').click();assert page.evaluate('document.body.classList.contains("sidebar-collapsed")');assert page.locator('#app-sidebar').bounding_box()['width']==64
  page.locator('#app-sidebar [data-tab=board]').click();expect(page.locator('#workspace-panel')).to_be_visible();expect(page.locator('#conversation')).to_be_visible();expect(page.locator('#conversation-text')).to_have_value('Keep this unfinished message.')
  page.evaluate("openWorkspace('contra')");assert page.evaluate('[selectedWorkspace,selectedOpportunity,selectedChat]')==chat_before
  page.keyboard.press('Escape');expect(page.locator('#workspace-panel')).to_be_hidden();expect(page.locator('#conversation-text')).to_have_value('Keep this unfinished message.')
  page.locator('#app-sidebar .nav-tools > summary').click();expect(page.locator('#app-sidebar .nav-tools')).to_contain_text('Ready to review');page.locator('#workspace-menu > summary').click();page.locator('#workspace-menu').evaluate('(el)=>el.open=false')
  page.locator('#sidebar-toggle').click();page.locator('#conversation-text').fill('')
  page.evaluate('id=>viewDocument(id)',did);expect(page.locator('#document-reader')).to_be_visible();expect(page.locator('#conversation')).to_be_visible();assert not page.locator('#main-content').evaluate('(el)=>el.inert')
  page.locator('[data-action=document-design]').click();page.wait_for_function("()=>document.getElementById('pdf-page-image').naturalWidth>0");page.screenshot(path='/tmp/otu-matrix-pdf.png');page.locator('[data-action=document-readable]').click()
  page.screenshot(path='/tmp/otu-matrix-desktop.png')
  page.locator('[data-action=document-chat]').click();expect(page.locator('#conversation-mode')).to_have_value('revise_document');page.locator('#conversation-text').fill('Make this clearer.');page.locator('#ask-workspace').click();page.locator('[data-action=use-document-suggestion]').click();expect(page.locator('#document-editor')).to_have_value('EXAMPLE OWNER\nA complete reviewed fixture document.\nLocal test only.')
  page.locator('#document-revision-reviewed').check();page.locator('[data-action=save-document-version]').click();expect(page.locator('#status')).to_contain_text('New PDF and Word versions saved')
  audio=page.locator('[data-action=read-answer]').last;page.locator('#dictate-message').click();audio.click();expect(page.locator('#dictate-message')).to_have_attribute('aria-pressed','false');expect(audio).to_have_text('⏸ Pause');assert page.evaluate('testUtterance.text').startswith('EXAMPLE OWNER');assert page.evaluate('testUtterance.voice.name')=='Samantha';audio.click();expect(audio).to_have_text('▶ Resume');audio.click();expect(audio).to_have_text('⏸ Pause');page.locator('[data-action=stop-answer]').last.click();expect(audio).to_have_text('🔊 Read aloud');audio.click();page.locator('#dictate-message').click();expect(audio).to_have_text('🔊 Read aloud');expect(page.locator('#dictate-message')).to_have_attribute('aria-pressed','true');page.locator('#dictate-message').click()
  page.set_viewport_size({'width':820,'height':1180});assert page.locator('#conversation').is_visible();assert page.locator('#main-content').evaluate('(el)=>el.inert');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.wait_for_timeout(250);assert page.locator('.layout').bounding_box()['x']==0;assert page.locator('#document-reader').bounding_box()['x']>=0;assert round(page.locator('#document-reader').bounding_box()['x']+page.locator('#document-reader').bounding_box()['width'])==820;page.screenshot(path='/tmp/otu-matrix-tablet.png')
  page.locator('[data-action=document-chat]').click();expect(page.locator('#document-reader')).to_be_hidden();assert not page.locator('#main-content').evaluate('(el)=>el.inert');page.evaluate('id=>viewDocument(id)',did);expect(page.locator('#document-reader')).to_be_visible()
  page.set_viewport_size({'width':390,'height':844});expect(page.locator('#document-reader')).to_have_attribute('aria-modal','true');assert page.locator('#main-content').evaluate('(el)=>el.inert');page.keyboard.press('Escape');expect(page.locator('#document-reader')).to_be_hidden();assert not page.locator('#main-content').evaluate('(el)=>el.inert')
  page.locator('#sidebar-toggle').click();expect(page.locator('#sidebar-toggle')).to_have_attribute('aria-expanded','true');page.locator('#sidebar-search').click();page.locator('#chat-search').fill('Example client');page.locator('.recent-open').click();expect(page.locator('#conversation-feed')).to_contain_text('Original opportunity history retained.')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert page.locator('#ask-workspace').bounding_box()['y']<844
  page.wait_for_timeout(250);page.screenshot(path='/tmp/otu-matrix-phone.png')
  # Organization controls work with touch and preserve original opportunity scope.
  page.set_viewport_size({'width':1440,'height':1000});page.locator('#sidebar-search').click() if not page.locator('#chat-search').is_visible() else None
  page.locator('#chat-search').fill('Example client');original_scope=page.evaluate('[selectedWorkspace,selectedOpportunity,selectedChat]');page.locator('#conversation-text').fill('Keep my unfinished reply.')
  page.locator('.recent-rename').click();page.locator('[data-ops=chat-pin]').click();expect(page.locator('.recent-open')).to_contain_text('★')
  page.locator('[data-ops=new-project]').click();page.locator('#organize-text').fill('Client projects');page.locator('#organize-form button').first.click();expect(page.locator('#organize-dialog')).not_to_be_visible();page.locator('#project-filter').select_option('')
  page.locator('.recent-rename').click();page.locator('[data-ops=chat-move]').click();page.locator('#organize-project').select_option(label='Client projects');page.locator('#organize-form button').first.click();expect(page.locator('.recent-open')).to_contain_text('Client projects');assert page.evaluate('[selectedWorkspace,selectedOpportunity,selectedChat]')==original_scope;expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished reply.')
  row=page.locator('.recent-open');row.dispatch_event('pointerdown',{'button':0,'clientX':20,'clientY':20});expect(page.locator('#chat-actions-dialog')).to_be_visible();row.dispatch_event('pointerup',{'button':0});page.locator('[data-ops=close-chat-menu]').click()
  page.wait_for_timeout(950);page.locator('.recent-rename').click();page.locator('[data-ops=chat-archive]').click();expect(page.locator('.recent-chat')).to_have_count(0);page.locator('#chat-view').select_option('archived');expect(page.locator('.recent-chat')).to_have_count(1)
  page.once('dialog',lambda d:d.accept());page.locator('.recent-rename').click();page.locator('[data-ops=chat-trash]').click();expect(page.locator('.recent-chat')).to_have_count(0);page.locator('#chat-view').select_option('trash');expect(page.locator('.recent-chat')).to_have_count(1);page.locator('.recent-rename').click();page.locator('[data-ops=chat-restore]').click();page.locator('#chat-view').select_option('active');expect(page.locator('.recent-chat')).to_have_count(1);expect(page.locator('#conversation-feed')).to_contain_text('Original opportunity history retained.');expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished reply.')
  # The Mail panel uses the existing draft flow and does not interrupt the chat.
  page.locator('#app-sidebar [data-tab=mail]').click();page.locator('#mail-box').select_option('drafts');expect(page.locator('#mail-status')).to_contain_text('Unsent drafts');expect(page.locator('#mail-items')).to_contain_text('Review draft');expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished reply.');page.locator('[data-ops=mail-folder]').click();page.locator('#organize-text').fill('Important follow-ups');page.locator('#organize-form button').first.click();expect(page.locator('#mail-box option[data-custom-folder]')).to_have_text('Important follow-ups');page.locator('#close-workspace-panel').click();expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished reply.')
  page.evaluate("tab('chat-settings');renderIsisVoices()");expect(page.locator('#isis-voice-status')).to_contain_text('Samantha');page.locator('#isis-voice-preview').click();assert page.evaluate('testUtterance.text').startswith('Hi Desmond, I’m Isis');assert page.evaluate('testUtterance.voice.name')=='Samantha';page.locator('#isis-voice').select_option('fixture-alex');page.locator('#isis-voice-preview').click();assert page.evaluate('testUtterance.voice.name')=='Alex';page.locator('#isis-voice').select_option('');page.locator('#isis-voice-stop').click();page.locator('#close-workspace-panel').click()
  page.locator('#conversation-text').fill('Message OTU…');page.locator('#status').evaluate('(el)=>el.textContent=""');page.screenshot(path='/tmp/otu-proportions-after.png')
  for width,height in [(1366,1024),(1024,768),(320,640),(1440,420)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,height,'horizontal overflow')
   for selector in ['#conversation-text','#ask-workspace','#attach-file','#dictate-message']:
    bounds=page.locator(selector).bounding_box();assert bounds and bounds['x']>=0 and bounds['x']+bounds['width']<=width+1 and bounds['y']+bounds['height']<=height+1,(selector,width,height,bounds)
   assert page.locator('#conversation-feed').bounding_box()['height']>=120,(width,height,'reading space')
   if width>1100:
    page.locator('#app-sidebar .sidebar-help').scroll_into_view_if_needed();expect(page.locator('#app-sidebar .sidebar-help')).to_be_in_viewport()
  # Short multitasking windows must expose chats without scrolling the entire sidebar.
  page.evaluate("""()=>{window.sidebarFixtureOriginal=chatThreads;const sample=chatThreads[0];chatThreads=Array.from({length:24},(_,i)=>({...sample,id:'sidebar-fixture-'+i,key:'chat:sidebar-fixture-'+i,title:'Planning conversation '+i,archived:false,trashed:false,project_id:''})).concat(chatThreads);document.body.classList.remove('search-open','sidebar-collapsed','sidebar-open');$('chat-search').value='';$('project-filter').value='';$('chat-view').value='active';renderSidebar()}""")
  for width,height in [(1440,420),(1180,600),(820,520),(600,420),(390,640)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(120)
   if width<=1100:page.locator('#sidebar-toggle').click()
   page.evaluate("$('recent-chats').dataset.active='';renderSidebar()")
   sidebar=page.locator('#app-sidebar');listing=page.locator('#recent-chats');bounds=listing.bounding_box()
   page.screenshot(path=f'/tmp/otu-sidebar-{width}x{height}.png')
   assert bounds['height']>=125,(width,height,'conversation list squeezed',bounds,page.locator('#app-sidebar').evaluate('(el)=>[...el.children].map(x=>[x.id||x.className,x.getBoundingClientRect().height,getComputedStyle(x).margin])'))
   assert sidebar.evaluate('(el)=>el.scrollHeight<=el.clientHeight+1'),(width,height,'whole sidebar scrolls')
   expect(page.locator('.recent-chat.selected')).to_be_in_viewport()
   expect(page.locator('[data-action=new-chat]')).to_be_in_viewport();expect(page.locator('#project-filter')).to_be_in_viewport();expect(page.locator('.sidebar-help')).to_be_in_viewport()
   listing.evaluate('(el)=>el.scrollTop=0');expect(page.locator('.recent-open').first).to_be_in_viewport()
   listing.evaluate('(el)=>el.scrollTop=el.scrollHeight');expect(page.locator('.recent-open').last).to_be_in_viewport()
   page.locator('#workspace-tools-toggle').click();expect(page.locator('#workspace-links [data-tab=mail]')).to_be_in_viewport();expect(page.locator('#chat-view')).to_be_in_viewport()
   page.locator('#chat-view').select_option('archived');expect(page.locator('#conversation-count')).to_have_text('0');page.locator('#chat-view').select_option('active');page.locator('#workspace-tools-toggle').click()
   page.evaluate('renderSidebar()');page.screenshot(path=f'/tmp/otu-sidebar-{width}x{height}.png')
   if width<=1100:page.locator('#sidebar-toggle').click()
  page.evaluate('chatThreads=window.sidebarFixtureOriginal;renderSidebar()')
  page.set_viewport_size({'width':1440,'height':600});page.wait_for_timeout(120)
  page.evaluate("$('chat-search').value='no-matching-conversation';$('chat-view').value='archived';renderSidebar()")
  expect(page.locator('.recent-chat')).to_have_count(0);page.locator('[data-action=new-chat]').click();expect(page.locator('.recent-chat.selected')).to_be_in_viewport();expect(page.locator('#chat-search')).to_have_value('');expect(page.locator('#chat-view')).to_have_value('active')

  page.set_viewport_size({'width':820,'height':1180});page.locator('#sidebar-toggle').click();page.locator('#project-filter').focus();assert float(page.locator('#project-filter').evaluate('(el)=>getComputedStyle(el).fontSize').replace('px',''))>=16;expect(page.locator('#project-filter')).to_be_in_viewport();page.locator('#sidebar-toggle').click()
  reduced=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');reduced.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());static=reduced.new_page();static.goto(base);expect(static.locator('#matrix-rain')).to_have_attribute('data-mode','reduced');assert not static.evaluate('otuMatrixStatus().running');reduced.close()
  assert not errors,errors;assert not downloads;browser.close();print('Workspace shell passed: desktop/tablet/phone, rail, independent panels, preserved chat/draft scope, bounds, short-window conversation space and new-chat visibility, keyboard viewport simulation, uploads/photos, mocked dictation/read-aloud controls, status report, reviewed documents, projects, long-press menus, Trash recovery and Mail drafts/folders. No paid inference or client messages.')
finally:server.terminate();server.wait(timeout=10)
