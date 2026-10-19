"""Trusted local prerecorded-audio check. No model, hosted inference or account writes."""
import os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='otu-audio-ui-') as folder:
 wrapper=Path(folder)/'server.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(root))+')\nimport app\napp.ThreadingHTTPServer(("127.0.0.1",'+str(port)+'),app.Handler).serve_forever()\n')
 server=subprocess.Popen([str(root/'.venv/bin/python'),str(wrapper)],cwd=root,env={'PATH':os.environ['PATH'],'OTU_DATA_DIR':folder})
 base='http://127.0.0.1:'+str(port)
 try:
  for _ in range(60):
   try:urllib.request.urlopen(base+'/health');break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1180,'height':800});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
   page.goto(base);page.wait_for_function('()=>selectedWorkspace!==null');page.locator('#workspace-menu > summary').click();page.locator('#workspace-menu [data-action=open-voice]').click();audio=page.locator('[data-voice-sample]');expect(audio).to_have_count(2);expect(audio.first).to_be_visible();assert audio.first.get_attribute('preload')=='none';assert not audio.first.get_attribute('autoplay')
   audio.first.evaluate('(a)=>a.play()');page.wait_for_function('()=>document.querySelectorAll("[data-voice-sample]")[0].currentTime>0.1');assert audio.first.evaluate('(a)=>a.duration>15&&a.duration<25')
   audio.nth(1).evaluate('(a)=>a.play()');page.wait_for_function('()=>document.querySelectorAll("[data-voice-sample]")[1].currentTime>0.1');assert audio.first.evaluate('(a)=>a.paused');page.evaluate('stopAnswer()');assert audio.nth(1).evaluate('(a)=>a.paused')
   page.set_viewport_size({'width':390,'height':740});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors;browser.close()
  print('Voice samples passed: actual MP3 decode/playback and duration, one sample at a time, stop control, same-origin requests and phone bounds. Local Chromium, not actual iPad audio output. No inference calls.')
 finally:server.terminate();server.wait(timeout=10)
