"""Private, resumable bounded uploads. File contents never enter inference automatically."""
import base64,hashlib,json,mimetypes,os,re,secrets,time
from pathlib import Path
MAX_FILE=1024**3
CHUNK=4*1024**2
class AttachmentStore:
 def __init__(self,engine):
  self.e=engine;self.root=engine.data/'attachments';self.root.mkdir(exist_ok=True)
  with engine.connect() as c:c.execute('CREATE TABLE IF NOT EXISTS attachment_uploads(id TEXT PRIMARY KEY,name TEXT,size INTEGER,received INTEGER,workspace TEXT,opportunity_id INTEGER,chat_id TEXT,state TEXT,created REAL,digest TEXT)')
 def scope(self,d):
  w,o=self.e.conversation_scope(d);return w,o,self.e.chat_key(d,w,o)
 def row(self,key):
  if not re.fullmatch('[0-9a-f]{32}',str(key)):raise ValueError('File not found.')
  with self.e.connect() as c:r=c.execute('SELECT * FROM attachment_uploads WHERE id=?',(key,)).fetchone()
  if not r:raise ValueError('File not found.')
  return dict(r)
 def status(self):
  quota=max(MAX_FILE,int(os.getenv('OTU_ATTACHMENT_QUOTA_BYTES',str(5*MAX_FILE))))
  with self.e.connect() as c:
   used=c.execute('SELECT COALESCE(SUM(size),0) FROM attachment_uploads WHERE state="complete"').fetchone()[0]
   reserved=c.execute('SELECT COALESCE(SUM(size),0) FROM attachment_uploads WHERE state="uploading"').fetchone()[0]
  return {'used':used,'reserved':reserved,'allowance':quota,'max_file':MAX_FILE,'chunk_size':CHUNK,'note':'App allowance; actual bucket capacity and host upload availability may differ. Files are not automatically processed by AI.'}
 def start(self,d):
  w,o,chat=self.scope(d);size=d.get('size');name=Path(str(d.get('name','')).replace('\\','/')).name[:180]
  if not isinstance(size,int) or isinstance(size,bool) or not 0<size<=MAX_FILE:raise ValueError('Choose a file between 1 byte and 1 GiB.')
  if not name or any(ord(c)<32 for c in name):raise ValueError('Invalid filename.')
  if Path(name).suffix.lower() not in ('.pdf','.docx','.txt','.md','.json','.csv','.xlsx','.pptx','.zip','.png','.jpg','.jpeg','.webp','.gif','.mp4','.mov','.mp3','.wav','.m4a'):raise ValueError('Choose a photo, document, ZIP, video or audio file.')
  with self.e.lock,self.e.connect() as c:
   # Expired partial uploads release reservations; never remove completed files.
   for r in c.execute('SELECT id FROM attachment_uploads WHERE state="uploading" AND created<?',(time.time()-7*86400,)).fetchall():
    (self.root/(r['id']+'.part')).unlink(missing_ok=True);c.execute('DELETE FROM attachment_uploads WHERE id=?',(r['id'],))
   stat=self.status();stat['reserved']=c.execute('SELECT COALESCE(SUM(size),0) FROM attachment_uploads WHERE state="uploading"').fetchone()[0]
   if stat['used']+stat['reserved']+size>stat['allowance']:raise ValueError('Storage allowance reached. Remove an unfinished upload or ask to increase the allowance after checking bucket capacity.')
   key=secrets.token_hex(16);(self.root/(key+'.part')).touch()
   c.execute('INSERT INTO attachment_uploads VALUES(?,?,?,?,?,?,?,?,?,?)',(key,name,size,0,w,o,chat,'uploading',time.time(),''))
  return self.row(key)
 def chunk(self,d):
  raw=base64.b64decode(d.get('content',''),validate=True)
  if not 0<len(raw)<=CHUNK:raise ValueError('Invalid upload chunk.')
  with self.e.lock,self.e.connect() as c:
   r=self.row(d.get('id'));offset=d.get('offset')
   if r['state']!='uploading' or not isinstance(offset,int) or offset<0:raise ValueError('Invalid upload state.')
   path=self.root/(r['id']+'.part')
   if offset<r['received']:
    with path.open('rb') as f:f.seek(offset);prior=f.read(len(raw))
    if offset+len(raw)<=r['received'] and prior==raw:return {'received':r['received']}
    raise ValueError('Chunk conflicts with saved data.')
   if offset!=r['received'] or offset+len(raw)>r['size']:raise ValueError('Upload offset does not match saved data.')
   with path.open('r+b') as f:f.seek(offset);f.write(raw);f.flush()
   received=offset+len(raw);c.execute('UPDATE attachment_uploads SET received=? WHERE id=?',(received,r['id']))
  return {'received':received}
 def finish(self,d):
  with self.e.lock,self.e.connect() as c:
   r=self.row(d.get('id'))
   if r['state']=='complete':return r
   if r['received']!=r['size']:raise ValueError('Upload is incomplete. Resume it before finishing.')
   path=self.root/(r['id']+'.part');path=path if path.exists() else self.root/r['id'];digest=hashlib.sha256()
   with path.open('rb') as f:
    for block in iter(lambda:f.read(CHUNK),b''):digest.update(block)
   if path.name!=r['id']:path.rename(self.root/r['id'])
   c.execute('UPDATE attachment_uploads SET state="complete",digest=? WHERE id=?',(digest.hexdigest(),r['id']))
  return self.row(r['id'])
 def cancel(self,d):
  with self.e.lock,self.e.connect() as c:
   r=self.row(d.get('id'))
   if r['state']=='complete':raise ValueError('Completed files are retained. Cancel only unfinished uploads.')
   (self.root/(r['id']+'.part')).unlink(missing_ok=True);c.execute('DELETE FROM attachment_uploads WHERE id=?',(r['id'],))
  return {'cancelled':True}
 def listing(self,d):
  w,o,chat=self.scope(d)
  with self.e.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM attachment_uploads WHERE workspace=? AND opportunity_id IS ? AND chat_id IS ? ORDER BY created DESC',(w,o,chat))]
 def file(self,key):
  r=self.row(key)
  if r['state']!='complete':raise ValueError('File is still uploading.')
  return self.root/r['id'],r

 def photo(self,key):
  from PIL import Image,ImageOps
  import io,warnings
  path,r=self.file(key)
  if r['size']>25*1024**2:raise ValueError('This image is too large for an inline preview. Save the original to view it.')
  try:
   with warnings.catch_warnings():
    warnings.simplefilter('error',Image.DecompressionBombWarning)
    with Image.open(path) as im:
     if im.width*im.height>25_000_000:raise ValueError('Photo dimensions are too large for a preview.')
     im=ImageOps.exif_transpose(im);im.thumbnail((1800,1800));im=im.convert('RGB');out=io.BytesIO();im.save(out,format='JPEG',quality=85);return out.getvalue()
  except (OSError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise ValueError('Cannot preview this image. Save the original to view it.')

 def remove(self,d):
  if d.get('confirmed') is not True:raise ValueError('Confirm removal of this conversation file first.')
  with self.e.lock,self.e.connect() as c:
   r=self.row(d.get('id'))
   if r['state']!='complete':raise ValueError('Cancel an unfinished upload instead.')
   (self.root/r['id']).unlink(missing_ok=True);c.execute('DELETE FROM attachment_uploads WHERE id=?',(r['id'],))
  return {'removed':True}
