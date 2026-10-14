"""Source-grounded application documents. No credentials or internal instructions exported."""
import io,re,html,json,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from pathlib import Path
FONT_DIR=Path(reportlab.__file__).parent/"fonts"
pdfmetrics.registerFont(TTFont("OTURegular",str(FONT_DIR/"Vera.ttf")))
pdfmetrics.registerFont(TTFont("OTUBold",str(FONT_DIR/"VeraBd.ttf")))
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from pypdf import PdfReader
NAVY='#172B42';GOLD='#9A793F'
SKILLS={
 'CRM / GoHighLevel':['GoHighLevel CRM','Pipeline design','Email/SMS automation','Customer journeys','Forms, calendars & funnels','Workflow testing','Zapier','Process documentation'],
 'AI / business automation':['AI-assisted product development','Requirements and workflow design','Testing and troubleshooting','CRM automation','Integration coordination','Documentation','Business operations'],
 'Sales / operations':['B2B sales','Prospecting','Needs discovery','Customer communication','CRM follow-up','Relationship management','Customer operations','Digital marketing'],
 'Coaching':['Youth coaching','Athlete development','Practice planning','Family communication','Program leadership','Scheduling','Camps and clinics','League operations'],
 'Contract':['Business operations','CRM automation','Sales and marketing','Customer workflows','Project coordination','Testing and documentation']}
PROFILES={
 'CRM / GoHighLevel':'CRM and marketing automation professional with hands-on GoHighLevel experience supporting lead capture, pipelines, customer journeys, scheduling and follow-up. Combines business-process design with sales and customer-service experience to build practical workflows, test handoffs and maintain clear documentation.',
 'AI / business automation':'Business-systems builder and product owner experienced in directing AI-assisted development from requirements and workflow design through testing, troubleshooting and iterative improvement. Background includes CRM automation, customer operations and digital systems. Coordinates product requirements, testing and operational handoffs.',
 'Sales / operations':'Sales and customer-operations professional with experience in prospecting, needs discovery, remote customer communication, relationship management and CRM-supported follow-up. Brings customer-service leadership, digital marketing and an organized approach to moving opportunities through defined stages.',
 'Coaching':'Western New York coach and sports-program professional with 18+ years of coaching and youth athletics experience, beginning in 2008. Background includes athlete development, school and youth coaching, practice planning, family communication and league operations.',
 'Contract':'Business operations and digital-systems professional with experience spanning sales, customer service, CRM automation and independent AI-assisted development. Turns business needs into organized workflows, coordinates execution and tests how systems work in practice.'}
def section(text,start,end):
    lines=text.splitlines();active=False;out=[]
    for line in lines:
        if line.strip()==start:active=True;continue
        if active and line.strip()==end:break
        if active:out.append(line.strip())
    return out
def clean(line):
    if any(x in line.lower() for x in ['verify','confirm','do not','never include','source résumé','not a ready-to','master record','reference phone','refresh_token','joat_db','/data/','/opportunity-data']):
        if '; prior résumé metrics' in line:return line.split('; prior résumé metrics')[0].strip()+'.'
        return ''
    return line.strip()
def profile(master,category,updates):
    lines=[line.strip() for line in master.splitlines() if line.strip()]
    if not lines or 'PROFESSIONAL EMPLOYMENT HISTORY' not in master:raise ValueError('The complete master career résumé is required to generate an application.')
    name=lines[0];email=re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',master);phone=re.search(r'\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}',master)
    if not email or not phone:raise ValueError('The master record needs your contact email and phone.')
    roles=[]
    for line in section(master,'PROFESSIONAL EMPLOYMENT HISTORY','INDEPENDENT BUSINESS, AI PRODUCT & SYSTEMS WORK'):
        if '|' in line and len(line.split('|'))>=3:
            parts=[x.strip() for x in line.split('|')];roles.append({'heading':parts[0]+' | '+parts[1],'dates':parts[-1],'bullets':[]})
        elif roles and clean(line):roles[-1]['bullets'].append(clean(line))
    if not roles:raise ValueError('Employment chronology could not be read from the master record.')
    projects=[clean(x) for x in section(master,'INDEPENDENT BUSINESS, AI PRODUCT & SYSTEMS WORK','COACHING, ATHLETICS & PROGRAM LEADERSHIP') if ':' in x and clean(x)]
    # Preserve explicit ongoing/planned status in source projects.
    completed=[x for x in projects if x.startswith('Image Host:')]
    # Prefer evidence of working tools; keep the ongoing label on unfinished work.
    all_projects=[clean(x) for x in section(master,'INDEPENDENT BUSINESS, AI PRODUCT & SYSTEMS WORK','COACHING, ATHLETICS & PROGRAM LEADERSHIP') if ':' in x and clean(x)]
    completed=[x for x in all_projects if x.startswith('Image Host:')]
    projects=(completed+projects)[:2]
    if updates:projects=([u['fact'] for u in updates if u['type']=='app_milestone'][:1]+projects)[:2]
    if category=='Coaching':
        coaching=[]
        source=section(master,'COACHING, ATHLETICS & PROGRAM LEADERSHIP','EDUCATION')
        for label in ['Pop Warner','South Buffalo Shamrocks','St. Francis','Western New York Maritime','Kodex Elite','WNYFFL']:
            line=next((x for x in source if x.startswith(label)),None)
            if not line:continue
            # Ambiguous dates and championship counts stay in the source record, not applications.
            if label=='Pop Warner':heading='Pop Warner | Head Coach';body='Youth football and flag football coaching in Buffalo and Mississippi.'
            elif label=='South Buffalo Shamrocks':heading='South Buffalo Shamrocks | Assistant / Volunteer';body='Supported youth coaching and athlete development as an assistant and volunteer.'
            elif label=='St. Francis':heading='St. Francis High School | JV Offensive Coordinator / Quarterbacks Coach';body='Offensive planning and quarterback instruction; experience across tackle and flag football.'
            elif label=='Western New York Maritime':heading='WNY Maritime / Tapestry | Girls Flag Football Head Coach';body='High-school girls flag football coaching and program leadership.'
            elif label=='Kodex Elite':heading='Kodex Elite Sports Training | Athlete Development';body='Athlete development, performance training and sports programming.'
            else:heading='WNYFFL | League Leadership';body='Adult flag football operations, event coordination and league administration.'
            coaching.append({'heading':heading,'dates':'','bullets':[body]})
        roles=coaching;projects=[]
    else:
        desired={'CRM / GoHighLevel':('Marketing','Customer Service','Sales Executive','Web Page'),'Sales / operations':('Marketing','Customer Service','Sales Executive','Sales Representative'),'AI / business automation':('Marketing','Customer Service','Website','Web Page')}.get(category,())
        selected=[r for r in roles if any(t in r['heading'] for t in desired)]
        roles=(selected or roles)[:4]
    edu=' '.join(section(master,'EDUCATION','TECHNOLOGY & PLATFORMS'))
    return {'name':name,'contact':'Buffalo, NY | '+phone.group(0)+' | '+email.group(0),'summary':PROFILES[category],'skills':SKILLS[category],'roles':roles,'projects':projects,'education':edu,'category':category,'recent_updates':[u['fact'] for u in updates if u['type']=='user_fact' and u['category'] in ('All',category)]}
def resume_sections(data):
    sections=[('PROFILE',[data['summary']]),('CORE CAPABILITIES',[' • '.join(data['skills'])]),('COACHING & PROGRAM EXPERIENCE' if data['category']=='Coaching' else 'RELEVANT EXPERIENCE',data['roles'])]
    if data['recent_updates']:sections.append(('RECENT ACCOMPLISHMENTS',data['recent_updates'][:3]))
    if data['projects']:sections.append(('INDEPENDENT SYSTEMS & PROJECTS',data['projects']))
    sections.append(('EDUCATION',[data['education']]))
    return sections
def cover_paragraphs(data,row):
    date=datetime.now(ZoneInfo('America/New_York')).strftime('%B %d, %Y')
    intro=f'I am interested in the {row["title"]} opportunity at {row["company"]}.'
    background=data['summary'].replace('Coordinates product requirements, testing and operational handoffs.','').strip()
    requirements=[]
    for term in ['CRM','automation','customer communication','sales','coaching','workflow','marketing']:
        if term.lower() in row.get('description','').lower() and term.lower() in (' '.join(data['skills'])+' '+background).lower():requirements.append(term)
    fit=('Your emphasis on '+', '.join(requirements[:3])+' aligns with the work I have done in these areas. ') if requirements else ''
    close=fit+'I would welcome a conversation about your priorities and how my experience could support the role. Thank you for your consideration.'
    return [date,row['company'],'Re: '+row['title'],'Dear Hiring Team,',intro,background,close,'Sincerely,',data['name']]
def pdf_document(data,sections,is_cover=False):
    out=io.BytesIO();styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='NameOTU',fontName='OTUBold',fontSize=23,leading=27,textColor=colors.HexColor(NAVY),spaceAfter=7))
    styles.add(ParagraphStyle(name='ContactOTU',fontName='OTURegular',fontSize=9,leading=12,textColor=colors.HexColor(NAVY),spaceAfter=10))
    styles.add(ParagraphStyle(name='SectionOTU',fontName='OTUBold',fontSize=10,leading=13,textColor=colors.HexColor(GOLD),spaceBefore=10,spaceAfter=5,keepWithNext=True))
    styles.add(ParagraphStyle(name='BodyOTU',fontName='OTURegular',fontSize=9.5,leading=12.5,spaceAfter=4))
    styles.add(ParagraphStyle(name='RoleOTU',parent=styles['BodyOTU'],fontName='OTUBold',spaceBefore=6,keepWithNext=True))
    def para(text,style='BodyOTU'):return Paragraph(html.escape(str(text)),styles[style])
    story=[para(data['name'],'NameOTU'),para(data['contact'],'ContactOTU')]
    if not is_cover:story.append(para('TARGET ROLE: '+data['target'],'ContactOTU'))
    if is_cover:
        for text in sections:story.extend([para(text),Spacer(1,7)])
    else:
        for title,items in sections:
            story.append(para(title,'SectionOTU'))
            for item in items:
                if isinstance(item,dict):
                    story.append(para(item['heading'],'RoleOTU'))
                    if item['dates']:story.append(para(item['dates']))
                    for bullet in item['bullets'][:2]:story.append(para('• '+bullet))
                else:story.append(para(item))
    def page(canvas,doc):
        canvas.setStrokeColor(colors.HexColor(GOLD));canvas.setLineWidth(1.2);canvas.line(42,letter[1]-36,letter[0]-42,letter[1]-36)
        canvas.setFont('OTURegular',8);canvas.setFillColor(colors.HexColor(NAVY));canvas.drawString(42,25,data['name']);canvas.drawRightString(letter[0]-42,25,str(doc.page))
    SimpleDocTemplate(out,pagesize=letter,rightMargin=42,leftMargin=42,topMargin=44,bottomMargin=34).build(story,onFirstPage=page,onLaterPages=page)
    return out.getvalue()
def docx_document(data,sections,is_cover=False):
    doc=Document();sec=doc.sections[0];sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.6);sec.left_margin=sec.right_margin=Inches(.6)
    style=doc.styles['Normal'];style.font.name='Calibri';style.font.size=Pt(10);style.paragraph_format.space_after=Pt(5)
    p=doc.add_paragraph();run=p.add_run(data['name']);run.bold=True;run.font.size=Pt(23);run.font.color.rgb=RGBColor.from_string(NAVY[1:]);doc.add_paragraph(data['contact'])
    if not is_cover:doc.add_paragraph('Target role: '+data['target'])
    if is_cover:
        for text in sections:doc.add_paragraph(text)
    else:
        for title,items in sections:
            p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;r=p.add_run(title);r.bold=True;r.font.color.rgb=RGBColor.from_string(GOLD[1:])
            for item in items:
                if isinstance(item,dict):
                    p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run(item['heading']).bold=True
                    if item['dates']:doc.add_paragraph(item['dates'])
                    for bullet in item['bullets'][:2]:doc.add_paragraph(bullet,style='List Bullet')
                else:doc.add_paragraph(item)
    out=io.BytesIO();doc.save(out);return out.getvalue()
def build_package(master,row,updates):
    data=profile(master,row['category'],updates);data['target']=row['title'];sections=resume_sections(data);cover=cover_paragraphs(data,row)
    result={'resume_pdf':pdf_document(data,sections),'resume_docx':docx_document(data,sections),'cover_pdf':pdf_document(data,cover,True),'cover_docx':docx_document(data,cover,True)}
    pages={};texts=[]
    for key in ['resume_pdf','cover_pdf']:
        reader=PdfReader(io.BytesIO(result[key]));pages[key]=len(reader.pages);texts.append('\n'.join(p.extract_text() or '' for p in reader.pages))
    if pages['resume_pdf']>2 or pages['cover_pdf']>1:raise ValueError('Generated document is too long; source material needs a shorter selection.')
    text='\n'.join(texts).lower()
    for phrase in ['verify current','confirm measurement','refresh_token','/data/','internal note','do not invent','source résumé']:
        if phrase in text:raise ValueError('Internal source text found; document generation stopped for correction.')
    for required in [data['name'],row['company'],row['title']]:
        if required.lower() not in text:raise ValueError('Generated document is missing a required name or role.')
    return result,{'passed':True,'resume_pages':pages['resume_pdf'],'cover_pages':pages['cover_pdf'],'source':'Imported master career record; wording and dates preserved','ai_used':False}

def master_document(record):
    doc=Document();doc.styles['Normal'].font.name='Calibri';doc.styles['Normal'].font.size=Pt(10)
    for line in record['baseline'].splitlines():
        if line.strip():doc.add_paragraph(line)
    doc.add_heading('CONFIRMED CAREER UPDATES',level=1)
    for update in record['updates']:
        doc.add_paragraph(update['fact']);doc.add_paragraph('Record source: '+update['source'])
    doc.add_paragraph('Internal master source. Tailored applications omit these record notes.')
    out=io.BytesIO();doc.save(out);return out.getvalue()
