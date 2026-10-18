"""Research UI on a trusted localhost fixture; model and Contra reads are mocked."""
import json,os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='otu-research-ui-') as folder:
 wrapper=Path(folder)/'fixture.py';wrapper.write_text('''import sys,time,json
sys.path.insert(0,'''+repr(str(root))+''')
import app
from contra_mcp import ContraConnection
stats={'reads':0,'writes':0}
app.engine.set_setting('contra_tokens',{'access_token':'fixture-only'})
def read(self,calls):
 assert len(calls)==1 and calls[0][0]=='list_job_feed'
 stats['reads']+=1;time.sleep(1.5)
 return {'list_job_feed:0':{'structuredContent':{'entries':[{'job':{'title':'Example CRM contract','publicUrl':'https://contra.com/opportunity/example-crm','description':'Set up two pipelines. <img src=x onerror=window.injected=true>','status':'POSTED'}}]}}}
ContraConnection.read_tools=read
def model(payload):
 stats['writes']+=1;time.sleep(1.4)
 context=json.loads(payload['messages'][1]['content']);assert 'research_receipt' in context
 return {'choices':[{'message':{'content':'Example CRM contract is a returned option [S2]. Review its actual requirements before applying.'}}]}
app.engine.ai_request=model
class Fixture(app.Handler):
 def do_GET(self):
  if self.path=='/fixture-stats':return self.output(stats)
  return super().do_GET()
from http.server import ThreadingHTTPServer
ThreadingHTTPServer(('127.0.0.1','''+str(port)+'''),Fixture).serve_forever()
''')
 server=subprocess.Popen([str(root/'.venv/bin/python'),str(wrapper)],cwd=root,env={'PATH':os.environ['PATH'],'OTU_DATA_DIR':folder,'HF_INFERENCE_TOKEN':'fixture-only'})
 base='http://127.0.0.1:'+str(port)
 try:
  for _ in range(60):
   try:urllib.request.urlopen(base+'/health');break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1180,'height':720});context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base);page.wait_for_function('()=>selectedWorkspace!==null');page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled()
   question='Find Contra CRM opportunities';page.locator('#conversation-text').fill(question);page.locator('#ask-workspace').click();expect(page.locator('#conversation-text')).to_have_value('',timeout=750);expect(page.locator('.chat-thinking')).to_contain_text('Checking Contra',timeout=2500);page.locator('#conversation-text').fill('Keep my next question.');expect(page.locator('.assistant-message .message-text')).to_contain_text('Example CRM',timeout=7000);expect(page.locator('#conversation-text')).to_have_value('Keep my next question.')
   page.locator('.answer-sources>summary').click();expect(page.locator('.answer-sources')).to_contain_text('list_job_feed: live');expect(page.locator('.answer-sources a')).to_have_attribute('href','https://contra.com/opportunity/example-crm');assert not page.evaluate('window.injected||false');page.screenshot(path='/tmp/otu-research-sources.png')
   page.locator('#conversation-text').fill(question);page.locator('#ask-workspace').click();expect(page.locator('.assistant-message')).to_have_count(2,timeout=7000);page.locator('.answer-sources>summary').last.click();expect(page.locator('.answer-sources').last).to_contain_text('cached');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))=={'reads':1,'writes':2}
   page.evaluate("fetch('/api/ai/limits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({paused:true})}).then(r=>r.json())")
   page.locator('#conversation-text').fill(question);page.locator('#ask-workspace').click();expect(page.locator('.assistant-message')).to_have_count(3,timeout=7000);expect(page.locator('.assistant-message .message-text').last).to_contain_text('AI writing was not called');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))=={'reads':1,'writes':2}
   page.reload();expect(page.locator('.assistant-message')).to_have_count(3);page.locator('.answer-sources>summary').last.click();expect(page.locator('.answer-sources').last).to_contain_text('cached')
   page.set_viewport_size({'width':390,'height':720});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors;browser.close()
  print('Research UI passed: immediate send/progress, preserved draft, receipts/links escaping, cached reads, allowance fallback without another model call, reload and phone bounds. Mocked services only.')
 finally:server.terminate();server.wait(timeout=10)
