"""Optional local check with a trusted, locally fulfilled page; no platform traffic.
The root-only fixture disables Chromium sandboxing. Production never does.
Run from repository root with PYTHONPATH=. .venv/bin/python scripts/check_browser_fixture.py.
"""
import os
from unittest.mock import patch
from platform_browser import PlatformBrowser
from playwright.async_api import BrowserType
original_launch=BrowserType.launch
async def fixture_launch(self,*args,**kwargs):
 kwargs["chromium_sandbox"]=False
 return await original_launch(self,*args,**kwargs)
os.environ['OTU_BROWSER_EXECUTABLE']='/usr/bin/chromium'
fixture='''<html><body><h1>CRM opportunity</h1><p>Build a lead follow-up workflow.</p><a href="https://contra.com/opportunities/test-job">CRM contract</a><form onsubmit="event.preventDefault();document.body.append('Submission fixture confirmed')"><label>First name<input name="first_name" placeholder="First name"></label><input name="email" type="email" placeholder="Email"><textarea name="bio" placeholder="Bio"></textarea><input type="password" name="password"><button type="submit" style="position:absolute;left:20px;top:400px;width:150px;height:40px">Create account</button></form></body></html>'''
async def route(self,r):await r.fulfill(status=200,content_type='text/html',body=fixture)
b=PlatformBrowser()
try:
 with patch('platform_browser.public_url',return_value='contra.com'),patch.object(PlatformBrowser,'route',route),patch.object(BrowserType,'launch',fixture_launch):
  b.call('start',{'url':'https://contra.com'},{'contra.com'})
  result=b.call('fill',{'fields':{'first_name':'Example','email':'example@example.com','bio':'Verified profile','password':'do not fill'}})
  assert set(result['filled'])=={'first_name','email','bio'},result
  page=b.call('read');assert len(page['candidates'])==1
  assert b.call('frame')[:2]==b'\xff\xd8'
  try:b.call('click',{'x':70,'y':420});raise AssertionError('Submission was not blocked')
  except ValueError as e:assert 'Approve' in str(e)
  b.call('click',{'x':70,'y':420,'approved':True})
  assert 'Submission fixture confirmed' in b.call('read')['text']
  b.call('stop')
 print('Real Chromium fixture passed: profile fill, visible-page extraction, candidate detection, screenshot, submission approval gate, session closure. No platform was contacted.')
finally:
 try:b.call('stop')
 except Exception:pass
