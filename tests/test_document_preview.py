import io,tempfile,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from reportlab.pdfgen.canvas import Canvas
from PIL import Image,ImageChops
from document_preview import render_page
class PortablePDF(unittest.TestCase):
 def test_real_pages_render_without_browser_plugin_and_reject_invalid_page(self):
  path=Path(tempfile.mkdtemp())/'fixture.pdf';pdf=Canvas(str(path));pdf.drawString(50,700,'FIRST PAGE');pdf.showPage();pdf.drawString(50,700,'SECOND PAGE');pdf.save()
  one=render_page(str(path),0);two=render_page(str(path),1)
  self.assertTrue(one.startswith(b'\x89PNG'));self.assertNotEqual(one,two)
  image=Image.open(io.BytesIO(one)).convert('RGB');self.assertGreater(image.width,500)
  self.assertIsNotNone(ImageChops.difference(image,Image.new('RGB',image.size,'white')).getbbox())
  with ThreadPoolExecutor(max_workers=3) as pool:self.assertTrue(all(x==one for x in pool.map(lambda _:render_page(str(path),0),range(3))))
  with self.assertRaises(ValueError):render_page(str(path),2)
