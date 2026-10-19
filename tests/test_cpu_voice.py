import tempfile,time,threading,wave,unittest
from pathlib import Path
from cpu_voice import CPUVoice
from engine import Engine
class VoiceTests(unittest.TestCase):
 def setUp(self):
  self.calls=[];self.active=0;self.peak=0
  def render(text,target):
   self.active+=1;self.peak=max(self.peak,self.active);self.calls.append(text);time.sleep(.03)
   with wave.open(str(target),'wb') as stream:stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(24000);stream.writeframes(b'\x00\x00'*2400)
   self.active-=1;return {'duration':.1,'sample_rate':24000,'generation_seconds':.03}
  self.voice=CPUVoice(Engine(tempfile.mkdtemp()),renderer=render);self.scope={'workspace':'assistant'}
 def tearDown(self):self.voice.pool.shutdown(wait=True);self.voice.close()
 def wait(self,j):
  for _ in range(100):
   r=self.voice.record({**self.scope,'id':j['id']})
   if r['status'] not in ('queued','running'):return r
   time.sleep(.01)
  self.fail('Speech did not complete')
 def test_cpu_cache_replay_and_scope_isolation(self):
  a=self.voice.prepare({**self.scope,'text':'A synthetic voice check.'});self.assertEqual(self.wait(a)['status'],'ready');b=self.voice.prepare({**self.scope,'text':'A synthetic voice check.'});self.assertEqual(a['id'],b['id']);self.assertEqual(len(self.calls),1);self.assertTrue(self.voice.audio({**self.scope,'id':a['id']}).startswith(b'RIFF'))
  with self.assertRaises(ValueError):self.voice.record({'workspace':'contra','id':a['id']})
  c=self.voice.prepare({'workspace':'contra','text':'A synthetic voice check.'});self.assertNotEqual(a['id'],c['id'])
 def test_serial_limits_validation_and_no_text_in_receipt(self):
  jobs=[self.voice.prepare({**self.scope,'text':'Synthetic segment '+str(i)}) for i in range(3)]
  for j in jobs:self.assertEqual(self.wait(j)['status'],'ready');self.assertNotIn('text',self.voice.record({**self.scope,'id':j['id']}))
  self.assertEqual(self.peak,1)
  for text in ['', 'x'*281, 'bad\x00text']:
   with self.assertRaises(ValueError):self.voice.prepare({**self.scope,'text':text})
  with self.assertRaises(ValueError):self.voice.prepare({**self.scope,'text':'Hi','voice':'unapproved'})
 def test_failed_render_not_automatically_retried(self):
  def fail(text,target):raise RuntimeError('private failure details')
  self.voice.renderer=fail;a=self.voice.prepare({**self.scope,'text':'A synthetic failure.'});r=self.wait(a);self.assertEqual(r['status'],'failed');self.assertNotIn('private failure',r['error']);self.assertEqual(a['id'],self.voice.prepare({**self.scope,'text':'A synthetic failure.'})['id'])
