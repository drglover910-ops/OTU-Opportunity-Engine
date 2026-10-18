"""Trusted localhost native-application fixture. No external submissions or paid AI."""
import json,os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='otu-native-ui-') as folder:
 fixture=Path(folder)/'fixture.py';fixture.write_text('''import sys,json
sys.path.insert(0,'''+repr(str(root))+''')
import app
from contra_mcp import ContraConnection
stats={'reads':0,'prepares':0,'submits':0,'applied':False}
url='https://contra.com/opportunity/canva-browser-fixture'
def job(slug='canva-browser-fixture'):return {'structuredContent':{'ok':True,'job':{'title':'Social Media Content Manager' if slug=='vis-browser-fixture' else 'Canva to Google Slides Conversion Specialist','publicUrl':'https://contra.com/opportunity/'+slug,'description':'Canva and Google Slides experience required. Preserve formatting.','status':'POSTED','jobPosting':{'jobPostingId':'posting-fixture'},'organization':{'name':'Fixture client'},'viewerApplication':{'appliedAt':'2026-10-18T00:00:00Z'} if stats['applied'] else None}}}
def read(self,calls):
 stats['reads']+=len(calls)
 return {name+':'+str(i):{'structuredContent':{'projects':[{'id':'project-fixture','title':'Presentation sample','description':'An actual presentation example','isDraft':False}]}} if name=='list_portfolio_projects' else job(args.get('slug','canva-browser-fixture')) for i,(name,args) in enumerate(calls)}
def write(self,calls):
 name,args=calls[0]
 if name=='apply_to_job_prepare':
  stats['prepares']+=1
  return {'prepare:0':{'structuredContent':{'ok':True,'draftId':'c257a0bd-bd72-4eb4-a40a-d569f56cd50d','preview':{'job':'Canva to Google Slides Conversion Specialist','message':args['message'],'workSamples':['Presentation sample']}}}}
 assert name=='apply_to_job_confirm' and args['confirm'] is True
 stats['submits']+=1;stats['applied']=True
 return {'confirm:0':{'structuredContent':{'ok':True}}}
ContraConnection.read_tools=read;ContraConnection.application_tools=write
app.engine.set_setting('contra_tokens',{'access_token':'fixture'})
app.engine.ai_request=lambda payload:{'choices':[{'message':{'content':'Review this Canva opportunity and its requirements before applying.'}}]}
class Fixture(app.Handler):
 def do_GET(self):
  if self.path=='/fixture-stats':return self.output(stats)
  return super().do_GET()
from http.server import ThreadingHTTPServer
ThreadingHTTPServer(('127.0.0.1','''+str(port)+'''),Fixture).serve_forever()
''')
 server=subprocess.Popen([str(root/'.venv/bin/python'),str(fixture)],cwd=root,env={'PATH':os.environ['PATH'],'OTU_DATA_DIR':folder,'HF_INFERENCE_TOKEN':'fixture-only'})
 base='http://127.0.0.1:'+str(port)
 try:
  for _ in range(60):
   try:urllib.request.urlopen(base+'/health');break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1180,'height':800});context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("""window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{paused:false,getVoices:()=>[{name:'Samantha Enhanced',voiceURI:'fixture-samantha',lang:'en-US',localService:true}],speak(u){window.testUtterance=u;this.paused=false},cancel(){this.paused=false},pause(){this.paused=true},resume(){this.paused=false}}});""")
   page.goto(base);page.wait_for_function('()=>selectedWorkspace!==null');page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled()
   page.locator('#conversation-text').fill('Keep my unfinished message.')
   entry=page.locator('#workspace-links [data-tab=contra-application]')
   if not entry.is_visible():page.locator('#workspace-tools-toggle').click()
   entry.click();expect(page.locator('#contra-application-url')).to_be_visible()
   page.locator('#contra-application-url').fill('https://contra.com/opportunity/canva-browser-fixture');page.locator('[data-action=contra-application-choose]').click()
   expect(page.locator('#contra-application-message')).to_be_visible(timeout=5000);expect(page.locator('#contra-application-content')).to_contain_text('unrelated CRM');expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished message.')
   page.locator('#contra-application-message').fill('My edited application message for this exact opportunity.')
   page.locator('#close-workspace-panel').click()
   if not entry.is_visible():page.locator('#workspace-tools-toggle').click()
   entry.click();expect(page.locator('#contra-application-url')).to_be_visible();expect(page.locator('#contra-application-message')).to_have_count(0)
   page.locator('#contra-application-content [data-action=contra-application-open]').first.click();expect(page.locator('#contra-application-message')).to_have_value('My edited application message for this exact opportunity.')
   page.locator('[data-action=contra-application-reset]').click();expect(page.locator('#contra-application-url')).to_be_visible()
   page.locator('#contra-application-content [data-action=contra-application-open]').first.click();expect(page.locator('#contra-application-message')).to_have_value('My edited application message for this exact opportunity.');expect(page.locator('#contra-application-fit')).not_to_be_checked()
   page.locator('[data-action=contra-application-reset]').click();page.locator('#contra-application-url').fill('https://contra.com/opportunity/vis-browser-fixture');page.locator('[data-action=contra-application-choose]').click();expect(page.locator('#contra-application-content h2')).to_have_text('Social Media Content Manager');expect(page.locator('#contra-application-message')).not_to_have_value('My edited application message for this exact opportunity.');expect(page.locator('#contra-application-fit')).not_to_be_checked()
   page.locator('[data-action=contra-application-reset]').click();page.locator('#contra-application-content [data-action=contra-application-open]').filter(has_text='Canva to Google Slides Conversion Specialist').click();expect(page.locator('#contra-application-message')).to_have_value('My edited application message for this exact opportunity.')
   reader=page.locator('[data-action=read-application]');reader.click();expect(reader).to_have_text('⏸ Pause');assert page.evaluate('testUtterance.rate')==1;assert page.evaluate('testUtterance.voice.name')=='Samantha Enhanced'
   page.locator('#application-audio [data-speech-speed]').select_option('1.5');assert page.evaluate('testUtterance.rate')==1.5
   reader.click();expect(reader).to_have_text('▶ Resume');reader.click();expect(reader).to_have_text('⏸ Pause')
   spoken=[]
   for _ in range(100):
    if page.evaluate('audioSession===null'):break
    spoken.append(page.evaluate('testUtterance.text'));page.evaluate('testUtterance.onend()')
   assert 'My edited application message for this exact opportunity.' in ''.join(spoken)
   expect(reader).to_have_text('🔊 Read aloud');reader.click();page.locator('#application-audio [data-action=stop-answer]').click();expect(reader).to_have_text('🔊 Read aloud')
   page.locator('[data-action=contra-application-prepare]').click();expect(page.locator('#status')).to_contain_text('Review the skills');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['prepares']==0
   page.locator('[data-contra-project]').check();page.locator('#contra-application-fit').check();page.locator('[data-action=contra-application-prepare]').click();expect(page.locator('#contra-application-approved')).to_be_visible(timeout=5000);expect(page.locator('#contra-application-content')).to_contain_text('Presentation sample');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['prepares']==1;assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==0
   page.locator('[data-action=contra-application-submit]').click();expect(page.locator('#status')).to_contain_text('approval box first');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==0
   page.screenshot(path='/tmp/otu-native-application-preview.png');page.locator('#contra-application-approved').check();page.locator('[data-action=contra-application-submit]').click();expect(page.locator('#contra-application-content')).to_contain_text('Application sent',timeout=5000);assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==1;expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished message.')
   page.reload();assert page.evaluate('speechRate()')==1.5;expect(page.locator('#conversation-feed')).to_contain_text('Contra confirmed submission.');page.locator('[data-action=contra-application-open]').first.click();expect(page.locator('#contra-application-content')).to_contain_text('Application sent');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==1
   page.set_viewport_size({'width':390,'height':740});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors;browser.close()
  print('Native application UI passed: application speech/pause/resume/stop, saved speed, edited-message readout, chooser reset on reopen, choose-another-job, scoped edit recovery, Tools entry without an AI reply, exact-listing form, retained form edits, fit/portfolio review, unsent preview, separate explicit approval, verified mocked submission once, saved receipt/reload, composer preservation and phone bounds. Local fixtures only; no external submission or paid AI.')
 finally:server.terminate();server.wait(timeout=10)
