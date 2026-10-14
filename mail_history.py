"""Private Gmail sent-history import. Reads relevant threads, never sends messages."""
import base64,re,time,json,urllib.parse
from email.utils import parseaddr,getaddresses
from datetime import datetime,timezone,timedelta
from engine import fetch_json,plain,now,choose_category

def decode(data):
    try:return base64.urlsafe_b64decode(data+'='*((-len(data))%4)).decode('utf-8',errors='replace')
    except Exception:return ''
def body(payload):
    texts=[];htmls=[]
    def walk(p):
        if p.get('filename'):return
        content=decode(p.get('body',{}).get('data',''))
        if p.get('mimeType')=='text/plain' and content:texts.append(content)
        elif p.get('mimeType')=='text/html' and content:htmls.append(plain(content))
        for part in p.get('parts',[]):walk(part)
    walk(payload)
    text='\n'.join(texts or htmls)
    text=re.split(r'(?im)^On .{0,200}wrote:\s*$|^-{2,}\s*Original Message\s*-{2,}|^From:\s+.*',text)[0]
    return text.strip()[:30000]
def filenames(payload):
    out=[]
    if payload.get('filename'):out.append(payload['filename'])
    for part in payload.get('parts',[]):out.extend(filenames(part))
    return out

def summarize(messages):
    outgoing=[m for m in messages if m['direction']=='sent'];incoming=[m for m in messages if m['direction']=='received'];human=[m for m in incoming if not m['automated']]
    latest=messages[-1] if messages else {};words='\n'.join(m['body'] for m in human[-2:]).lower()
    status='No reply found' if not incoming else 'Automated acknowledgment only' if not human else 'Reply received'
    stage='Contacted';evidence=[]
    if re.search(r'not moving forward|not selected|cannot offer|can.t offer|unable to offer|position (?:has been )?filled|unfortunately.{0,80}(?:application|position)',words):status='Rejection / closed wording';stage='Parked'
    elif re.search(r'offer you|pleased to offer|welcome to (?:the|our) team|employment offer|offer letter|offer from|(?:increase|improve|raise|revised).{0,50}offer',words):status='Offer wording — verify terms';stage='Offer / contract'
    elif re.search(r'\binterview\b|schedule.{0,40}(?:call|meeting)|(?:meet|meeting).{0,30}(?:you|with)',words):status='Interview / meeting discussed';stage='Interview / meeting'
    relationship='Follow-up'
    if latest.get('direction')=='received' and re.search(r'(?:send|provide|need|attach).{0,50}(?:resume|résumé|cover letter)',latest.get('body',''),re.I):relationship='Requested paperwork'
    for m in human:
        for sentence in re.split(r'(?<=[.!?])\s+|\n',m['body']):
            if re.search(r'interview|offer|meeting|resume|résumé|position|schedule',sentence,re.I):evidence.append(sentence[:400])
    return {'status':status,'stage':stage,'relationship':relationship,'sent':len(outgoing),'received':len(incoming),'human_replies':len(human),'evidence':evidence[:8],'latest_direction':latest.get('direction'),'latest_date':latest.get('date'),'paid_outcome_verified':False}

def parse_messages(raw,owner):
    messages=[]
    for item in raw.get('messages',[]):
        if 'DRAFT' in item.get('labelIds',[]):continue
        payload=item.get('payload',{});h={x['name'].lower():x['value'] for x in payload.get('headers',[])}
        sent='SENT' in item.get('labelIds',[]) or parseaddr(h.get('from',''))[1].lower()==owner
        automated=h.get('auto-submitted','no').lower()!='no' or bool(re.search(r'mailer-daemon|postmaster|no.?reply',h.get('from',''),re.I))
        messages.append({'id':item['id'],'thread_id':item.get('threadId',raw.get('id','')),'direction':'sent' if sent else 'received','sender':h.get('from',''),'recipient':h.get('to',''),'cc':h.get('cc',''),'subject':h.get('subject',''),'body':body(payload),'rfc_message_id':h.get('message-id',''),'attachments':filenames(payload),'automated':automated,'date':datetime.fromtimestamp(int(item.get('internalDate','0'))/1000,timezone.utc).isoformat()})
    messages.sort(key=lambda m:m['date'])
    return messages

def gmail_read(url,headers):
    for attempt in range(4):
        try:return fetch_json(url,headers=headers)
        except ValueError as e:
            if attempt==3 or (re.search(r'HTTP (?:400|401|403|404)',str(e)) and not re.search(r'(?:userRateLimitExceeded|rateLimitExceeded)',str(e))):raise
            time.sleep(2**attempt)

def study(engine):
    try:
        token=engine.gmail_token();headers={'Authorization':'Bearer '+token};api='https://gmail.googleapis.com/gmail/v1/users/me'
        engine.set_setting('history_study',{'status':'running','started':now(),'threads_reviewed':0})
        profile=gmail_read(api+'/profile',headers=headers);owner=profile['emailAddress'].lower();engine.set_setting('gmail_owner',owner)
        cases={};limited=False
        queries=[('Buffalo Stallions','in:sent -in:chats stallions'),('Relevant outreach','in:sent -in:chats {resume résumé "cover letter" application coaching "job opportunity" "GoHighLevel" "Contra" proposal contract opportunity sales marketing}')]
        for label,query in queries:
            page=None
            for index in range(10):
                params={'maxResults':100,'q':query}
                if page:params['pageToken']=page
                listing=gmail_read(api+'/messages?'+urllib.parse.urlencode(params),headers=headers)
                for ref in listing.get('messages',[]):
                    tid=ref['threadId']
                    if tid not in cases:cases[tid]=label
                page=listing.get('nextPageToken')
                if not page:break
            if page:limited=True
        reviewed=0;errors=[]
        for tid,label in cases.items():
            try:
                time.sleep(0.25)
                raw=gmail_read(api+'/threads/'+tid+'?format=full',headers=headers);messages=[]
                messages=parse_messages(raw,owner)
                outgoing=[m for m in messages if m['direction']=='sent']
                if not outgoing:continue
                summary=summarize(messages);first=outgoing[0]
                recipient=next((address for _,address in getaddresses([first['recipient']]) if address.lower()!=owner),'')
                text=' '.join(m['subject']+' '+m['body']+' '+' '.join(m['attachments']) for m in messages)
                company=label if label=='Buffalo Stallions' else next((name for name in ['Kids Choice Sports','Public Flower','Toke Lane','KushMart','STIIIZY','Healthy Buffalo','Upwork','Contra','Yelp','Seneca'] if name.lower().replace(' ','') in re.sub(r'\s+','',text.lower())),None)
                company=company or (recipient.split('@')[-1] if '@' in recipient else 'Outreach conversation')
                category='Coaching' if company in ('Buffalo Stallions','Kids Choice Sports','Healthy Buffalo') else choose_category(text)
                url='https://mail.google.com/mail/u/0/#all/'+tid
                result=engine.add({'company':company,'title':first['subject'].strip() or 'Opportunity conversation','url':url,'category':category,'description':'Imported Gmail correspondence. Open the thread for original opportunity context.','source':'Gmail history','relationship':summary['relationship']})
                oid=result['id']
                if result['added']:
                    with engine.connect() as c:
                        c.execute('UPDATE opportunities SET stage=?,contact=?,notes=?,followup=? WHERE id=?',(summary['stage'],recipient,'History: '+summary['status']+'. Hiring/payment outcomes are not inferred.',(datetime.now(timezone.utc)+timedelta(days=1)).date().isoformat() if summary['stage'] not in ('Parked','Offer / contract') and datetime.fromisoformat(summary['latest_date'])>datetime.now(timezone.utc)-timedelta(days=60) else '',oid))
                with engine.lock,engine.connect() as c:
                    c.execute('INSERT OR REPLACE INTO email_threads(thread_id,opportunity_id,company,subject,summary,messages,reviewed) VALUES(?,?,?,?,?,?,?)',(tid,oid,company,first['subject'],json.dumps(summary),json.dumps(messages),now()))
                    engine.log(c,oid,'Sent conversation studied',summary['status'])
                reviewed+=1
                engine.set_setting('history_study',{'status':'running','threads_reviewed':reviewed,'threads_found':len(cases),'limited':limited})
            except Exception as e:
                detail=str(e) if isinstance(e,ValueError) and str(e).startswith(('Service returned HTTP','Service could not be reached','Add both','Unknown category')) else type(e).__name__
                errors.append(detail)
        learn(engine)
        engine.set_setting('history_study',{'status':'partial' if errors else 'complete','threads_skipped':len(errors),'read_errors':list(dict.fromkeys(errors)),'threads_reviewed':reviewed,'threads_found':len(cases),'limited':limited,'finished':now(),'scope':'Sent-folder career/contract queries plus all messages in matching threads. Up to 10 pages per query; no attachment bodies downloaded.'})
    except Exception as e:
        current=engine.setting('history_study',{});current.update({'status':'failed','error':'Gmail history read failed: '+type(e).__name__,'finished':now()});engine.set_setting('history_study',current)

def learn(engine):
    cases=engine.email_cases();examples=[];total=0;replies=0
    for case in cases:
        detail=engine.email_case(case['thread_id']);summary=detail['summary'];replies+=int(summary['human_replies']>0)
        for message in detail['messages']:
            if message['direction']!='sent':continue
            total+=1
            # Learn only short, professional outreach lines; never copy recipient identities or personal details.
            for line in message['body'].splitlines():
                if re.search(r"I(?:’|')?m interested|I am interested|please find|attached.{0,40}(?:resume|résumé)|looking forward|following up|please let me know",line,re.I):
                    if re.search(r'password|secret|api.?key|token',line,re.I):continue
                    line=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[email omitted]',line)
                    line=re.sub(r'\+?\d[\d ().-]{7,}\d','[phone omitted]',line)
                    if len(line)<350 and line not in examples:examples.append(line)
    engine.set_setting('outreach_style',{'sent_messages_reviewed':total,'threads_with_human_replies':replies,'examples':examples[:10],'rules':['Short, confident introduction tied to the actual opportunity.','Requested-paperwork replies should just provide the requested documents.','Follow-ups should reference prior contact and ask for the next step.','Never infer a hire or payment from a positive reply.','Check historical correspondence before sending duplicate outreach.'],'learned_at':now()})

def refresh_known_thread(engine,tid,raw):
    owner=engine.setting('gmail_owner','')
    case=engine.email_case(tid);messages=parse_messages(raw,owner);summary=summarize(messages)
    old_stage=case['summary'].get('stage');current=engine.get(case['opportunity_id'])
    with engine.lock,engine.connect() as c:
        c.execute('UPDATE email_threads SET summary=?,messages=?,reviewed=? WHERE thread_id=?',(json.dumps(summary),json.dumps(messages),now(),tid))
        if current['stage']==old_stage:c.execute('UPDATE opportunities SET stage=?,relationship=? WHERE id=?',(summary['stage'],summary['relationship'],case['opportunity_id']))
        engine.log(c,case['opportunity_id'],'Conversation refreshed',summary['status'])
