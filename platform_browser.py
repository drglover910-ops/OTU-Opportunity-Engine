"""Single-owner, memory-only browser. No stealth, CAPTCHA bypass, or saved login profiles."""
import asyncio,concurrent.futures,ipaddress,socket,threading,urllib.parse,time,os

def public_url(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443):raise ValueError('Use a public HTTPS website address without passwords.')
    try:addresses=socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)
    except OSError:raise ValueError('That website could not be reached.') from None
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):raise ValueError('Private and internal network addresses are blocked.')
    return p.hostname.lower()

class PlatformBrowser:
    def __init__(self):
        self.loop=None;self.thread=None;self.browser=None;self.context=None;self.page=None;self.mutex=threading.Lock();self.hosts=set();self.checked={}
    def call(self,action,data=None,hosts=()):
        with self.mutex:
            if self.loop is None:
                self.loop=asyncio.new_event_loop();self.thread=threading.Thread(target=self.loop.run_forever,daemon=True);self.thread.start()
            self.hosts.update(hosts)
            future=asyncio.run_coroutine_threadsafe(self.execute(action,data or {}),self.loop)
            try:return future.result(timeout=65)
            except concurrent.futures.TimeoutError:future.cancel();raise ValueError('The browser took too long. Check its page before retrying.') from None
            except ValueError:raise
            except Exception as e:
                if action=='start':
                    try:asyncio.run_coroutine_threadsafe(self.execute('stop',{}),self.loop).result(timeout=10)
                    except Exception:pass
                if any(word in str(e).lower() for word in ('sandbox','namespace','operation not permitted')):raise ValueError('This host cannot start the required browser sandbox. Do not enter credentials. Use the platform on your own device while browser hosting is configured.') from None
                raise ValueError('The browser could not complete that action. Check the page before retrying. No automatic retry was made.') from None
    def allowed(self,url):
        p=urllib.parse.urlsplit(url)
        return p.hostname and any(p.hostname==h or p.hostname.endswith('.'+h) for h in self.hosts|{'accounts.google.com','appleid.apple.com','login.microsoftonline.com'})
    async def route(self,route):
        req=route.request;url=req.url
        try:
            host=urllib.parse.urlsplit(url).hostname
            if self.checked.get(host,0)<time.monotonic():
                public_url(url);self.checked[host]=time.monotonic()+15
            if req.is_navigation_request() and req.frame==self.page.main_frame and not self.allowed(url):await route.abort();return
            await route.continue_()
        except Exception:await route.abort()
    async def execute(self,action,d):
        if action=='status':return {'open':bool(self.page)}
        if action=='start':
            public_url(d['url'])
            if not self.allowed(d['url']):raise ValueError('Add this platform before opening its website.')
            if not self.browser:
                from playwright.async_api import async_playwright
                self.playwright=await async_playwright().start()
                self.browser=await self.playwright.chromium.launch(headless=True,chromium_sandbox=True,env={'PATH':os.defpath,'LANG':'C.UTF-8'},args=['--disable-dev-shm-usage'],**({'executable_path':os.environ['OTU_BROWSER_EXECUTABLE']} if os.getenv('OTU_BROWSER_EXECUTABLE') else {}))
                self.context=await self.browser.new_context(viewport={'width':1024,'height':768},accept_downloads=False,service_workers='block')
                self.page=await self.context.new_page();await self.context.route('**/*',self.route)
                self.context.on('page',lambda p:setattr(self,'page',p))
            try:response=await self.page.goto(d['url'],wait_until='domcontentloaded',timeout=35000)
            except Exception:raise ValueError('The platform did not open. It may restrict hosted browsers. Check the screen; no access controls were bypassed.') from None
            return {'started':True,'http_status':response.status if response else None}
        if action=='stop':
            if self.browser:await self.browser.close()
            if getattr(self,'playwright',None):await self.playwright.stop();self.playwright=None
            self.browser=None;self.context=None;self.page=None;self.checked={};return {'closed':True}
        if not self.page:raise ValueError('Open a platform browser first.')
        if action=='frame':return await self.page.screenshot(type='jpeg',quality=65,timeout=15000)
        if action=='read':
            if not self.allowed(self.page.url):raise ValueError('This page is outside the selected platforms.')
            text=await self.page.locator('body').inner_text(timeout=10000)
            links=await self.page.locator('a[href]').evaluate_all("els=>els.filter(e=>e.getClientRects().length).map(e=>({title:e.innerText.trim().slice(0,200),url:e.href})).filter(e=>e.title&&/\\/(?:jobs?|opportunities|projects?)(?:\\/|[?#])/.test(e.url)).slice(0,60)")
            return {'url':self.page.url,'title':await self.page.title(),'text':text[:24000],'candidates':links,'scope':'Visible page only. Candidate links need review; they are not verified jobs.'}
        if action=='click':
            x=max(0,min(1023,int(d['x'])));y=max(0,min(767,int(d['y'])))
            sensitive=await self.page.evaluate("""p=>{let e=document.elementFromPoint(p.x,p.y);let b=e?.closest('button,input[type=submit],input[type=button]');return !!b&&(b.type==='submit'||/submit|sign.?up|create.*account|apply|send|publish|pay|purchase|buy|accept/i.test((b.innerText||b.value||'')+' '+(b.getAttribute('aria-label')||'')));}""",{'x':x,'y':y})
            if sensitive and not d.get('approved'):raise ValueError('Review the page and check “Approve this page action” before using that button.')
            await self.page.mouse.click(x,y);return {'clicked':True,'message':'Page action attempted. Check the page for confirmation; submission is not independently verified.'}
        if action=='type':
            text=str(d.get('text',''))
            if not text or len(text)>10000:raise ValueError('Enter up to 10,000 characters.')
            await self.page.keyboard.insert_text(text);return {'typed':True}
        if action=='back':
            await self.page.go_back(wait_until='domcontentloaded',timeout=20000);return {'back':True}
        if action=='key':
            if d.get('key') not in ('Tab','Shift+Tab','Backspace','Escape','ArrowDown','ArrowUp'):raise ValueError('That key is not supported. Use the page button for submission.')
            await self.page.keyboard.press(d['key']);return {'pressed':True}
        if action=='scroll':await self.page.mouse.wheel(0,600 if d.get('direction')=='down' else -600);return {'scrolled':True}
        if action=='fill':
            filled=[]
            for el in await self.page.locator('input:not([type=password]):not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=file]):not([type=submit]),textarea').all():
                if not await el.is_visible() or not await el.is_editable():continue
                descriptor=await el.evaluate("e=>[e.name,e.id,e.placeholder,e.getAttribute('aria-label'),e.autocomplete,e.id?document.querySelector('label[for=\"'+CSS.escape(e.id)+'\"]')?.innerText:''].filter(Boolean).join(' ').toLowerCase()")
                if any(t in descriptor for t in ('password','verification','one-time','credit','card number','social security','birthday','birth date','tax','rate','salary')):continue
                for field,value in d.get('fields',{}).items():
                    import re
                    patterns={'email':r'\bemail\b','first_name':r'first.?name|given.?name','last_name':r'last.?name|family.?name|surname','full_name':r'full.?name|display.?name|^name name','headline':r'headline|professional.?title','bio':r'\bbio\b|about.?me|professional.?summary','message':r'cover.?letter|proposal|application.?message','skills':r'\bskills\b'}
                    if field in patterns and value and re.search(patterns[field],descriptor):
                        await el.fill(str(value)[:10000]);filled.append(field);break
            return {'filled':filled,'message':f'{len(filled)} fields filled. Review the page. Nothing was submitted.'}
        if action=='upload':
            inputs=self.page.locator('input[type=file]');index=int(d.get('index',0))
            if index<0 or index>=await inputs.count():raise ValueError('No matching upload field was found. Open the upload part of the form first.')
            await inputs.nth(index).set_input_files(d['path']);return {'attached':True,'message':'Document attached to the page. Review before submitting.'}
        raise ValueError('Unknown browser action.')
