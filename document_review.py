"""Owner-reviewed document versions; originals remain unchanged."""
import io,html,re,json
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
from docx import Document
from docx.shared import Pt,RGBColor

def render(text):
 styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='OTURevision',fontName='Helvetica',fontSize=10,leading=14,textColor=HexColor('#172B42'),spaceAfter=5))
 blocks=[];doc=Document()
 for index,line in enumerate(text.splitlines()):
  if not line.strip():blocks.append(Spacer(1,7));continue
  blocks.append(Paragraph(html.escape(line),styles['Title'] if index==0 else styles['OTURevision']))
  paragraph=doc.add_paragraph(line)
  for run in paragraph.runs:run.font.name='Calibri';run.font.size=Pt(18 if index==0 else 10);run.font.color.rgb=RGBColor.from_string('172B42')
 output=io.BytesIO();SimpleDocTemplate(output,leftMargin=45,rightMargin=45,topMargin=40,bottomMargin=40).build(blocks)
 word=io.BytesIO();doc.save(word);return output.getvalue(),word.getvalue()

def save(engine,data):
 from engine import now
 did=int(data['document_id']);text=str(data.get('text','')).strip()
 if data.get('reviewed') is not True:raise ValueError('Review the complete revised document before saving a new version.')
 if not 20<=len(text)<=16000:raise ValueError('Use 20–16,000 characters for the revised document.')
 if re.search(r'(?i)hf_token|google_client_secret|/opportunity-data/|internal verification section',text):raise ValueError('Remove internal configuration or verification notes before saving.')
 with engine.connect() as c:
  old=c.execute('SELECT * FROM documents WHERE id=?',(did,)).fetchone()
  candidates=c.execute('SELECT * FROM packages ORDER BY id DESC').fetchall()
 if not old or old['kind'] not in ('resume','cover_letter'):raise ValueError('Only prepared résumés and cover letters can be revised here.')
 package=next((p for p in candidates if did in json.loads(p['files']).values()),None)
 if not package:raise ValueError('This is not a current application document. Open the latest prepared version.')
 pdf,word=render(text);prefix='resume' if old['kind']=='resume' else 'cover';stamp=now().replace(':','').replace('.','').replace('+','')
 # Rendering and persistence complete before the package changes; old files remain intact.
 new={}
 for extension,content in [('pdf',pdf),('docx',word)]:
  result=engine.import_file(Path(old['name']).stem+'_reviewed_'+stamp+'.'+extension,content,old['kind']);new[prefix+'_'+extension]=result['id']
 with engine.lock,engine.connect() as c:
  current=c.execute('SELECT * FROM packages WHERE id=?',(package['id'],)).fetchone();files=json.loads(current['files'])
  if did not in files.values():raise ValueError('A newer version was saved while you were editing. Open that version before retrying.')
  replaced={files.get(prefix+'_pdf'),files.get(prefix+'_docx')};files.update(new)
  checks=json.loads(current['checks']);checks.update({prefix+'_pages':len(PdfReader(io.BytesIO(pdf)).pages),'owner_reviewed_revision':True,'factual_check':'Owner review; no automated factual certification'})
  c.execute('UPDATE packages SET files=?,checks=? WHERE id=?',(json.dumps(files),json.dumps(checks),package['id']))
  # Changing attachments revokes any prior approval; sent drafts remain untouched.
  draft=c.execute('SELECT * FROM drafts WHERE id=?',(package['draft_id'],)).fetchone()
  if draft and draft['status'] not in ('Sent','Sending','Delivery unknown'):
   attachments=[x for x in json.loads(draft['attachments']) if x not in replaced]+[new[prefix+'_pdf']]
   digest=engine.draft_digest(draft['recipient'],draft['subject'],draft['body'],attachments)
   c.execute('UPDATE drafts SET attachments=?,digest=?,status="Draft",repeat_authorized=0 WHERE id=?',(json.dumps(attachments),digest,draft['id']))
  engine.log(c,package['opportunity_id'],'Document version saved','Owner reviewed; original retained; message approval reset')
 return {'document_id':new[prefix+'_pdf'],'files':new,'message':'New PDF and Word versions saved. Originals kept. Review and approve the updated attachments before sending.'}
