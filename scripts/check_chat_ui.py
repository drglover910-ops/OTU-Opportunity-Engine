"""Trusted localhost-only delayed chat fixture. No provider, email or paid calls."""
import json,os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
root=Path(__file__).resolve().parents[1];folder=tempfile.mkdtemp(prefix='otu-chat-ui-')
wrapper=Path(folder)/'fixture.py';wrapper.write_text('''import sys,time,json
sys.path.insert(0,'''+repr(str(root))+''')
import app
calls=[]
def model(payload):
 question=json.loads(payload['messages'][1]['content'])['question'];calls.append(question);time.sleep(1.8)
 if 'failfixture' in question:raise ValueError('Fixture provider unavailable. Your question is saved.')
 text='**Saved context**\\nWe will continue the existing Contra work. Nothing has been submitted.\\n'+'\\n'.join('Work item '+str(i)+': review the actual requirements before moving forward.' for i in range(1,23))
 return {'choices':[{'message':{'content':text}}]}
app.engine.ai_request=model
class Fixture(app.Handler):
 def do_GET(self):
  if self.path=='/fixture-stats':return self.output({'calls':len(calls)})
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
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1366,'height':1024});context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("""window.SpeechSynthesisUtterance=class {constructor(text){this.text=text}};Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{name:'Samantha',voiceURI:'fixture',localService:true,lang:'en-US'}],speak(u){window.sample=u},cancel(){},pause(){},resume(){}}});Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>{if(window.denyCopy)throw Error('denied');window.copiedText=t}}});""")
  page.goto(base);expect(page.locator('#version')).to_have_text('v'+(root/'VERSION').read_text().strip());page.wait_for_function('()=>selectedWorkspace!==null');page.locator('[data-action=new-chat]').click();page.wait_for_function('()=>selectedChat!==null');expect(page.locator('[data-action=new-chat]')).to_be_enabled()
  page.locator('#conversation-text').fill('Review our existing Contra work without submitting.');page.locator('#ask-workspace').click();expect(page.locator('#conversation-text')).to_have_value('',timeout=750);expect(page.locator('.user-message')).to_contain_text('Review our existing Contra work');expect(page.locator('.chat-thinking')).to_contain_text('Isis is thinking',timeout=1000);expect(page.locator('#ask-workspace')).to_be_disabled();page.screenshot(path='/tmp/otu-chat-thinking.png')
  page.locator('#conversation-text').fill('Keep this next question for later.');expect(page.locator('[aria-label="Copy response"]')).to_be_visible(timeout=7000);expect(page.locator('.chat-thinking')).to_have_count(0);expect(page.locator('#conversation-text')).to_have_value('Keep this next question for later.');expect(page.locator('.message-text strong')).to_have_text('Saved context');expect(page.locator('#ask-workspace')).to_be_enabled()
  # The action row remains inside the chat viewport while reading a long answer.
  page.evaluate("let feed=document.getElementById('conversation-feed'),article=feed.querySelector('.assistant-message');feed.scrollTop=article.offsetTop-feed.offsetTop")
  copy=page.locator('[aria-label="Copy response"]');expect(copy).to_be_in_viewport();feed=page.locator('#conversation-feed').bounding_box();bounds=copy.bounding_box();assert bounds['y']+bounds['height']<=feed['y']+feed['height']+1
  copy.click();assert page.evaluate('copiedText').startswith('Saved context');page.locator('[data-action=read-answer]').click();assert page.evaluate('sample.text').startswith('Saved context');assert page.evaluate('sample.voice.name')=='Samantha';page.locator('[data-action=stop-answer]').click()
  up=page.locator('[aria-label="Good response"]');down=page.locator('[aria-label="Needs improvement"]');up.click();expect(up).to_have_attribute('aria-pressed','true');down.click();expect(down).to_have_attribute('aria-pressed','true');expect(up).to_have_attribute('aria-pressed','false');page.screenshot(path='/tmp/otu-chat-actions.png');page.locator('#conversation-text').fill('');page.reload();expect(page.locator('[aria-label="Needs improvement"]')).to_have_attribute('aria-pressed','true')
  page.locator('#conversation-text').fill('failfixture: show an honest failure');page.locator('#ask-workspace').click();expect(page.locator('.chat-request-error')).to_contain_text('Fixture provider unavailable',timeout=7000);expect(page.locator('.user-message')).to_have_count(2);page.locator('[data-action=retry-chat]').click();expect(page.locator('#conversation-text')).to_have_value('failfixture: show an honest failure');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['calls']==2;page.locator('#conversation-text').fill('')
  # A reply finishing in another chat cannot steal the current view.
  page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled();source=page.evaluate('selectedChat');page.locator('#conversation-text').fill('Keep this reply in its own conversation');page.locator('#ask-workspace').click();expect(page.locator('.chat-thinking')).to_be_visible();page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled();other=page.evaluate('selectedChat');assert source!=other;page.wait_for_timeout(3000);assert page.evaluate('selectedChat')==other;expect(page.locator('.chat-welcome')).to_be_visible();page.evaluate('id=>openConversation("assistant",null,id)',source);expect(page.locator('[aria-label="Copy response"]')).to_be_visible()
  # Refresh reconnects to the existing request and never starts another inference.
  page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled();page.locator('#conversation-text').fill('Reload fixture without another paid request');page.locator('#ask-workspace').click();expect(page.locator('.chat-thinking')).to_be_visible();page.reload();expect(page.locator('[aria-label="Copy response"]')).to_be_visible(timeout=7000);expect(page.locator('.user-message')).to_have_count(1);assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['calls']==4
  page.evaluate('window.denyCopy=true;document.execCommand=()=>false');page.locator('[aria-label="Copy response"]').click();expect(page.locator('.copy-tool-dialog')).to_contain_text('Copy message');expect(page.locator('.copy-tool-dialog textarea')).to_have_value(__import__('re').compile('Saved context'));page.locator('.copy-tool-dialog button').click()
  # Losing an acknowledgement cannot charge another inference on a manual retry.
  page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled();lost={'post':True,'get':True}
  def lose_ack(route):
   if route.request.method=='POST' and lost['post']:
    lost['post']=False;route.fetch();route.abort()
   elif route.request.method=='GET' and lost['get']:lost['get']=False;route.abort()
   else:route.continue_()
  page.route('**/api/chat/request*',lose_ack);page.locator('#conversation-text').fill('Uncertain delivery fixture');page.locator('#ask-workspace').click();expect(page.locator('#conversation-text')).to_have_value('Uncertain delivery fixture',timeout=5000);expect(page.locator('[aria-label="Copy response"]')).to_be_visible(timeout=7000);expect(page.locator('#ask-workspace')).to_be_enabled();page.locator('#ask-workspace').click();expect(page.locator('#ask-workspace')).to_be_enabled(timeout=5000);expect(page.locator('.user-message')).to_have_count(1);assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['calls']==5
  assert not errors,errors;browser.close();print('Delayed chat checks passed: immediate bubble/clear/thinking, preserved next draft, reachable Copy/read-aloud/votes, persistent ratings, honest failure, no automatic retries, navigation isolation, reload recovery and clipboard fallback. Five mocked inference calls only, including acknowledgement-loss deduplication.')
finally:server.terminate();server.wait(timeout=10)
