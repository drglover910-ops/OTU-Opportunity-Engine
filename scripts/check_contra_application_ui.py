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
def job():return {'structuredContent':{'ok':True,'job':{'title':'Canva to Google Slides Conversion Specialist','publicUrl':url,'description':'Canva and Google Slides experience required. Preserve formatting.','status':'POSTED','jobPosting':{'jobPostingId':'posting-fixture'},'organization':{'name':'Fixture client'},'viewerApplication':{'appliedAt':'2026-10-18T00:00:00Z'} if stats['applied'] else None}}}
def read(self,calls):
 stats['reads']+=len(calls)
 return {name+':'+str(i):{'structuredContent':{'projects':[{'id':'project-fixture','title':'Presentation sample','description':'An actual presentation example','isDraft':False}]}} if name=='list_portfolio_projects' else job() for i,(name,args) in enumerate(calls)}
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
   page.goto(base);page.wait_for_function('()=>selectedWorkspace!==null');page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled()
   page.locator('#conversation-text').fill('Review application requirements for https://contra.com/opportunity/canva-browser-fixture');page.locator('#ask-workspace').click()
   try:expect(page.locator('[data-action=contra-application-open]')).to_be_visible(timeout=7000)
   except Exception:
    print('Fixture errors:',errors);print('Fixture requests:',page.evaluate('JSON.stringify(chatLastData?.data?.requests?.map(r=>({status:r.status,error:r.error,focus:r.result?.focus})))'));raise
   page.locator('#conversation-text').fill('Keep my unfinished message.');page.locator('[data-action=contra-application-open]').first.click();expect(page.locator('#contra-application-message')).to_be_visible(timeout=5000);expect(page.locator('#contra-application-content')).to_contain_text('unrelated CRM');expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished message.')
   page.locator('[data-action=contra-application-prepare]').click();expect(page.locator('#status')).to_contain_text('Review the skills');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['prepares']==0
   page.locator('[data-contra-project]').check();page.locator('#contra-application-fit').check();page.locator('[data-action=contra-application-prepare]').click();expect(page.locator('#contra-application-approved')).to_be_visible(timeout=5000);expect(page.locator('#contra-application-content')).to_contain_text('Presentation sample');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['prepares']==1;assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==0
   page.locator('[data-action=contra-application-submit]').click();expect(page.locator('#status')).to_contain_text('approval box first');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==0
   page.screenshot(path='/tmp/otu-native-application-preview.png');page.locator('#contra-application-approved').check();page.locator('[data-action=contra-application-submit]').click();expect(page.locator('#contra-application-content')).to_contain_text('Application sent',timeout=5000);assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==1;expect(page.locator('#conversation-text')).to_have_value('Keep my unfinished message.')
   page.reload();expect(page.locator('#conversation-feed')).to_contain_text('Contra confirmed submission.');page.locator('[data-action=contra-application-open]').first.click();expect(page.locator('#contra-application-content')).to_contain_text('Application sent');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['submits']==1
   page.set_viewport_size({'width':390,'height':740});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors;browser.close()
  print('Native application UI passed: exact-listing form, fit/portfolio review, unsent preview, separate explicit approval, verified mocked submission once, saved receipt/reload, composer preservation and phone bounds. Local fixtures only; no external submission or paid AI.')
 finally:server.terminate();server.wait(timeout=10)
