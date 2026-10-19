"""Private, bounded CPU speech jobs. Heavy/GPL speech runtime stays in a child process."""
import atexit,concurrent.futures,hashlib,importlib.util,json,os,re,secrets,selectors,subprocess,sys,tempfile,threading,time
from pathlib import Path
MODEL_SHA='beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a'
VOICES_SHA='bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'
class CPUVoice:
 def __init__(self,engine,renderer=None):
  self.engine=engine;self.models=Path(os.getenv('OTU_VOICE_MODEL_DIR','/opt/otu-voice'));self.root=Path(tempfile.mkdtemp(prefix='otu-private-speech-'));self.jobs={};self.keys={};self.lock=threading.RLock();self.slots=threading.BoundedSemaphore(4);self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix='otu-cpu-speech');self.proc=None;self.renderer=renderer;atexit.register(self.close)
 def status(self):
  available=bool(self.renderer) or (all((self.models/n).is_file() for n in ('kokoro-v1.0.onnx','voices-v1.0.bin')) and importlib.util.find_spec('kokoro_onnx') is not None)
  return {'available':available,'voice':'Heart','engine':'Kokoro CPU','cpu_threads':1,'max_characters':280,'paid_provider':False,'note':'Local CPU speech; short chunks, one worker, private temporary cache. No hosted inference API.'}
 def scope(self,d):
  w,o=self.engine.conversation_scope(d);return [w,o,self.engine.chat_key(d,w,o)]
 def _clean(self):
  ready=sorted((j for j in self.jobs.values() if j['status'] not in ('queued','running')),key=lambda j:j['created'])
  size=sum((self.root/(j['id']+'.wav')).stat().st_size for j in ready if (self.root/(j['id']+'.wav')).exists())
  for j in ready:
   if time.time()-j['created']<1800 and len(self.jobs)<48 and size<16*1024**2:continue
   path=self.root/(j['id']+'.wav')
   if path.exists():size-=path.stat().st_size;path.unlink()
   self.jobs.pop(j['id'],None);self.keys.pop(j['key'],None)
 def prepare(self,d):
  scope=self.scope(d);text=d.get('text')
  if not isinstance(text,str) or not 1<=len(text.strip())<=280:raise ValueError('Read a speech segment between 1 and 280 characters.')
  text=text.strip()
  if any(ord(c)<32 and c not in '\n\t' for c in text):raise ValueError('Invalid speech text.')
  if d.get('voice','heart')!='heart':raise ValueError('Choose the approved Heart voice.')
  if not self.status()['available']:raise ValueError('CPU voice is unavailable. Device voice is still available.')
  key=hashlib.sha256(json.dumps([scope,'kokoro-heart-v1',text],ensure_ascii=False).encode()).hexdigest()
  with self.lock:
   self._clean()
   if key in self.keys:return self._view(self.jobs[self.keys[key]])
   if not self.slots.acquire(blocking=False):raise ValueError('The CPU voice is busy. Try again shortly or use device voice.')
   identity=secrets.token_hex(16);job={'id':identity,'key':key,'scope':scope,'status':'queued','created':time.time()};self.jobs[identity]=job;self.keys[key]=identity
   self.pool.submit(self._run,identity,text)
   return self._view(job)
 def _view(self,j):return {k:v for k,v in j.items() if k in ('id','status','error','duration','generation_seconds','sample_rate')}
 def record(self,d):
  identity=str(d.get('id',''))
  if not re.fullmatch('[0-9a-f]{32}',identity):raise ValueError('Speech sample not found.')
  scope=self.scope(d)
  with self.lock:
   j=self.jobs.get(identity)
   if not j or j['scope']!=scope:raise ValueError('Speech sample not found in this conversation.')
   return self._view(j)
 def audio(self,d):
  j=self.record(d)
  if j['status']!='ready':raise ValueError('Speech sample is not ready.')
  return (self.root/(j['id']+'.wav')).read_bytes()
 def _render(self,text,target):
  if self.renderer:return self.renderer(text,target)
  if self.proc is None or self.proc.poll() is not None:
   env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'OTU_VOICE_MODEL_DIR':str(self.models),'OTU_VOICE_OUTPUT_DIR':str(self.root),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','PYTHONUNBUFFERED':'1'}
   self.proc=subprocess.Popen([sys.executable,str(Path(__file__).with_name('voice_worker.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,env=env)
  self.proc.stdin.write(json.dumps({'text':text,'id':target.stem})+'\n');self.proc.stdin.flush()
  with selectors.DefaultSelector() as selector:
   selector.register(self.proc.stdout,selectors.EVENT_READ)
   if not selector.select(timeout=45):self.close();raise ValueError('CPU speech timed out.')
  result=json.loads(self.proc.stdout.readline())
  if not result.get('ok'):raise ValueError('CPU speech could not complete.')
  return result
 def _run(self,identity,text):
  with self.lock:self.jobs[identity]['status']='running'
  try:
   target=self.root/(identity+'.wav');result=self._render(text,target)
   if not target.exists() or not 44<target.stat().st_size<4*1024**2:raise ValueError('Invalid speech audio.')
   with self.lock:self.jobs[identity].update(status='ready',duration=result['duration'],generation_seconds=result['generation_seconds'],sample_rate=result['sample_rate'])
  except Exception:
   with self.lock:self.jobs[identity].update(status='failed',error='Heart could not finish this segment. Device voice is available.')
  finally:self.slots.release()
 def close(self):
  proc=self.proc;self.proc=None
  if proc and proc.poll() is None:
   proc.kill();proc.wait(timeout=5)
