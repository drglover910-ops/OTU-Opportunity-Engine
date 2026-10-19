"""Synthetic local CPU-voice lifecycle fixture; no model calls or outbound account actions."""
import json,os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='otu-cpu-ui-') as folder:
 fixture=Path(folder)/'fixture.py';fixture.write_text('''import sys,wave,math,struct,time
sys.path.insert(0,'''+repr(str(root))+''')
import app
from cpu_voice import CPUVoice
calls=[];failed=False
def render(text,target):
 calls.append(text)
 if failed:raise ValueError('fixture failure')
 time.sleep(.15)
 with wave.open(str(target),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(b''.join(struct.pack('<h',int(1000*math.sin(i/10))) for i in range(72000)))
 return {'duration':3,'sample_rate':24000,'generation_seconds':.15}
app.cpu_voice=CPUVoice(app.engine,renderer=render)
app.engine.ai_request=lambda p:{'choices':[{'message':{'content':'This is a synthetic speech test. '+('Keep the original message visible while reading it aloud. '*8)}}]}
class Fixture(app.Handler):
 def do_GET(self):
  if self.path=='/fixture-stats':return self.output({'renders':len(calls)})
  return super().do_GET()
 def do_POST(self):
  global failed
  if self.path=='/fixture-fail':failed=True;return self.output({'ok':True})
  return super().do_POST()
app.ThreadingHTTPServer(('127.0.0.1','''+str(port)+'''),Fixture).serve_forever()
''')
 server=subprocess.Popen([str(root/'.venv/bin/python'),str(fixture)],cwd=root,env={'PATH':os.environ['PATH'],'OTU_DATA_DIR':folder,'HF_INFERENCE_TOKEN':'fixture-only'})
 base='http://127.0.0.1:'+str(port)
 try:
  for _ in range(60):
   try:urllib.request.urlopen(base+'/health');break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1180,'height':800});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
   page.goto(base);page.wait_for_function('()=>selectedWorkspace!==null');page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled();page.locator('#conversation-text').fill('Say hello for our local speech test.');page.locator('#ask-workspace').click();button=page.locator('[data-action=read-answer]').last;expect(button).to_be_visible(timeout=7000)
   button.click();page.wait_for_function('()=>audioSession?.mode==="cpu"&&audioSession.player.currentTime>.1');speed=button.locator('..').locator('[data-speech-speed]');speed.select_option('2');assert page.evaluate('audioSession.player.playbackRate')==2;button.click();expect(button).to_have_text('▶ Resume');assert page.evaluate('audioSession.player.paused');button.click();expect(button).to_have_text('⏸ Pause');button.locator('..').locator('[data-action=stop-answer]').click();expect(button).to_have_text('🔊 Read aloud');assert page.evaluate('audioSession===null')
   page.wait_for_timeout(400);count=json.load(urllib.request.urlopen(base+'/fixture-stats'))['renders'];button.click();page.wait_for_function('()=>audioSession?.mode==="cpu"&&audioSession.player.currentTime>.1');assert json.load(urllib.request.urlopen(base+'/fixture-stats'))['renders']==count;page.locator('[data-action=new-chat]').click();expect(page.locator('[data-action=new-chat]')).to_be_enabled();assert page.evaluate('audioSession===null')
   page.evaluate("window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{getVoices:()=>[],cancel(){},speak(u){window.fallbackVoice=u},pause(){},resume(){}}})")
   page.locator('#conversation-text').fill('Say hello for the failure fixture.');page.locator('#ask-workspace').click();button=page.locator('[data-action=read-answer]').last;expect(button).to_be_visible(timeout=7000);page.locator('.assistant-message .message-text').last.evaluate('(el)=>el.textContent="A different synthetic sentence for the CPU failure case."');page.evaluate("api('/fixture-fail',{})");button.click();page.wait_for_function('()=>audioSession?.mode==="device"');assert page.evaluate('fallbackVoice.text').startswith('A different synthetic');page.set_viewport_size({'width':390,'height':740});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors;browser.close()
  print('CPU speech browser passed: actual fixture WAV playback, pause/resume, speed without rerender, scoped cache reuse, stop/navigation cancellation, device fallback and phone bounds. No hosted inference or account writes.')
 finally:server.terminate();server.wait(timeout=10)
