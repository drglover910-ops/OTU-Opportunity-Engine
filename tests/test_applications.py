import io,tempfile,unittest,zipfile
from pathlib import Path
from engine import Engine
from applications import build_package,master_document
from pypdf import PdfReader
MASTER='''DESMOND L. GLOVER
Buffalo, NY | (716) 579-1670 | dr.glover910@gmail.com
PROFESSIONAL EMPLOYMENT HISTORY
Digital Marketing Executive | OTU+ LLC — Buffalo, NY / Remote | Jun 2025 – Jun 2026
Built GoHighLevel CRM pipelines and automated customer follow-up.
Supported B2B outreach and marketing; prior résumé metrics reported 110 leads (confirm measurement period).
Vice President of Customer Service | OTU+ LLC | May 2025 – May 2026
Managed customer service and CRM records.
INDEPENDENT BUSINESS, AI PRODUCT & SYSTEMS WORK
J.O.A.T. Content Engine: designed a content workflow; implementation is ongoing.
Image Host: developed and deployed an image-hosting service.
COACHING, ATHLETICS & PROGRAM LEADERSHIP
Pop Warner head coach, Buffalo — four seasons and four championships.
South Buffalo Shamrocks — assistant/volunteer for two seasons.
EDUCATION
Advanced Regents High School Diploma — Lackawanna High School (2003–2007).
TECHNOLOGY & PLATFORMS
GoHighLevel, Zapier, AI-assisted development.
MASTER RECORD INTEGRITY / TAILORING NOTES
Never include internal notes in applications.
'''
class Applications(unittest.TestCase):
    def setUp(self):
        self.e=Engine(tempfile.mkdtemp());self.e.import_file('Master_Career_Resume_Original.txt',MASTER.encode())
        self.oid=self.e.add({'title':'CRM Automation Specialist','company':'Example Client','description':'GoHighLevel CRM and automation workflows','category':'CRM / GoHighLevel','url':'https://example.com/job'})['id']
    def test_finished_package_and_source_fidelity(self):
        result=self.e.create_package({'id':self.oid});self.assertTrue(result['checks']['passed']);self.assertEqual(len(result['files']),4)
        draft=self.e.draft(result['draft_id']);self.assertEqual(draft['status'],'Draft');self.assertEqual(len(__import__('json').loads(draft['attachments'])),2)
        with self.e.connect() as c:row=c.execute('SELECT * FROM documents WHERE id=?',(result['files']['resume_pdf'],)).fetchone()
        text='\n'.join(p.extract_text() for p in PdfReader(row['path']).pages)
        self.assertIn('Jun 2025',text);self.assertIn('private beta deployment',text);self.assertNotIn('110 leads',text);self.assertNotIn('confirm measurement',text)
    def test_unfinished_projects_keep_their_status(self):
        source=MASTER.replace('Image Host: developed and deployed an image-hosting service.','')
        files,checks=build_package(source,self.e.get(self.oid),[])
        text='\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(files['resume_pdf'])).pages)
        self.assertIn('implementation is ongoing',text)
    def test_master_preserved_and_new_facts_versioned(self):
        self.e.add_career_update({'fact':'Completed a CRM workflow audit.','category':'CRM / GoHighLevel','confirmed':True})
        record=self.e.master_record();self.assertEqual(record['baseline'],MASTER);self.assertTrue(any(u['fact']=='Completed a CRM workflow audit.' for u in record['updates']))
        self.assertTrue(master_document(record).startswith(b'PK'))
    def test_updates_require_confirmation(self):
        with self.assertRaises(ValueError):self.e.add_career_update({'fact':'Unconfirmed achievement'})
    def test_coaching_counts_and_uncertain_dates_not_reconstructed(self):
        row=self.e.get(self.oid);row['category']='Coaching'
        files,checks=build_package(MASTER,row,[]);text='\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(files['resume_pdf'])).pages)
        self.assertIn('18+',text);self.assertIn('Assistant / Volunteer',text);self.assertNotIn('four championships',text)
    def test_missing_master_or_requirements_fails(self):
        other=Engine(tempfile.mkdtemp());oid=other.add({'company':'X','title':'CRM role','description':'CRM workflow'})['id']
        with self.assertRaises(ValueError):other.create_package({'id':oid})
    def test_generated_package_and_master_updates_survive_restore(self):
        self.e.create_package({'id':self.oid});target=Engine(tempfile.mkdtemp());target.restore(self.e.backup());self.assertEqual(len(target.packages()),1);self.assertTrue(target.career_updates());self.assertEqual(len(target.packages()[0]['files'])>0,True)
