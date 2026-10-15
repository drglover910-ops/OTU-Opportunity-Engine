"""Portable private PDF page previews, independent of browser PDF plugins."""
import io,threading
from functools import lru_cache
from pathlib import Path
import pypdfium2 as pdfium
_lock=threading.Lock()  # PDFium calls are serialized across HTTP worker threads.
@lru_cache(maxsize=12)
def render_page(path,page_index):
 with _lock:
  document=None;page=None;bitmap=None
  try:
   if Path(path).stat().st_size>25*1024*1024:raise ValueError('This PDF is too large for a page preview. Use its readable text view.')
   document=pdfium.PdfDocument(path)
   if not 0<=page_index<len(document):raise ValueError('PDF page not found.')
   page=document[page_index];scale=min(1.5,1600/max(page.get_width(),1),2200/max(page.get_height(),1));bitmap=page.render(scale=scale)
   image=bitmap.to_pil();output=io.BytesIO();image.save(output,format='PNG');return output.getvalue()
  except ValueError:raise
  except Exception:raise ValueError('This PDF could not be previewed. Use its readable text view.') from None
  finally:
   if bitmap is not None:bitmap.close()
   if page is not None:page.close()
   if document is not None:document.close()
