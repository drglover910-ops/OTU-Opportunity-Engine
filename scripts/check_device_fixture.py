"""Optional device-tool fixture. Run from repo root with .venv/bin/python.
Uses Chromium with local fixtures only; it does not verify real iPad Safari.
"""
import os,tempfile,subprocess,time,urllib.request,sys
sys.path.insert(0,'.');sys.path.insert(0,'tests')
from engine import Engine
from test_applications import MASTER
from playwright.sync_api import sync_playwright,expect
folder=tempfile.mkdtemp(prefix='otu-device-tools-');engine=Engine(folder);engine.import_file('Master_Career_Resume_Fixture.txt',MASTER.replace('DESMOND L. GLOVER','EXAMPLE OWNER').replace('dr.glover910@gmail.com','example@example.com').encode())
base='http://127.0.0.1:18871';server=subprocess.Popen(['.venv/bin/python','app.py'],env={**os.environ,'PORT':'18871','OTU_DATA_DIR':folder})
try:
 for _ in range(40):
  try:urllib.request.urlopen(base+'/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=browser.new_context();app=context.new_page();app.goto(base);expect(app.locator('#version')).to_have_text('v'+open('VERSION').read().strip())
  reader=app.evaluate('() => readerBookmarklet()');filler=app.evaluate("() => profileBookmarklet({first_name:'Example',last_name:'Owner',email:'example@example.com',bio:'Verified career summary'})")
  context.route('https://contra.com/**',lambda r:r.fulfill(status=200,content_type='text/html',body='''<html><head><title>CRM contract</title></head><body><h1>CRM contract</h1><p>Build a lead workflow. Project budget requires confirmation.</p><form onsubmit="event.preventDefault();window.didSubmit=true"><input name="first_name" placeholder="First name"><input name="last_name" placeholder="Last name"><input name="email" placeholder="Email"><textarea name="bio" placeholder="Bio"></textarea><input type="password" name="password"><input type="checkbox" name="terms"><button>Submit</button></form></body></html>'''))
  platform=context.new_page();platform.goto('https://contra.com/opportunities/fixture')
  platform.on('dialog',lambda d:d.accept());platform.evaluate('url=>{location.href=url}',filler)
  expect(platform.locator('[name="first_name"]')).to_have_value('Example');expect(platform.locator('[name="password"]')).to_have_value('');expect(platform.locator('[name="terms"]')).not_to_be_checked();assert platform.evaluate('!window.didSubmit')
  platform.locator('[name="password"]').evaluate("e=>e.style.display='none'")
  with context.expect_page() as popup:platform.evaluate('url=>{location.href=url}',reader)
  imported=popup.value;imported.locator('#device-import').wait_for(state='visible',timeout=15000);expect(imported.locator('#device-import-title')).to_have_value('CRM contract')
  imported.locator('#device-import-company').fill('Fixture client');imported.locator('#device-import-form button').click();imported.locator('#conversation').wait_for(state='visible')
  expect(imported.locator('#conversation-title')).to_contain_text('Fixture client')
  assert len([l for l in engine.list() if l['company']=='Fixture client'])==1
  print('Device tools end-to-end passed in Chromium: reviewed profile filling without passwords/consent/submission; cross-origin page-reader handshake; capture review; deduplicated save into the Contra conversation. Actual iPad Safari installation remains an owner test.')
  browser.close()
finally:server.terminate();server.wait(timeout=5)
