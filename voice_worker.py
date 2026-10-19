# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone CPU speech process. JSON lines in/out; no account credentials or network calls."""
import os,json,sys,time,re,hashlib
from pathlib import Path
import onnxruntime as ort
ort.disable_telemetry_events()
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from cpu_voice import MODEL_SHA,VOICES_SHA
models=Path(os.environ['OTU_VOICE_MODEL_DIR']);output=Path(os.environ['OTU_VOICE_OUTPUT_DIR'])
for name,digest in [('kokoro-v1.0.onnx',MODEL_SHA),('voices-v1.0.bin',VOICES_SHA)]:
 if hashlib.sha256((models/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Unverified speech asset')
options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1;options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
session=ort.InferenceSession(str(models/'kokoro-v1.0.onnx'),sess_options=options,providers=['CPUExecutionProvider']);engine=Kokoro.from_session(session,str(models/'voices-v1.0.bin'))
for line in sys.stdin:
 try:
  d=json.loads(line);text=d['text'];identity=d['id']
  if not isinstance(text,str) or not 1<=len(text)<=280 or not re.fullmatch('[0-9a-f]{32}',identity):raise ValueError()
  start=time.perf_counter();samples,rate=engine.create(text,voice='af_heart',speed=1.0,lang='en-us')
  if not np.isfinite(samples).all() or not 0<len(samples)<=rate*75:raise ValueError()
  part=output/(identity+'.part');sf.write(str(part),samples,rate,format='WAV',subtype='PCM_16');part.replace(output/(identity+'.wav'))
  result={'ok':True,'duration':round(len(samples)/rate,3),'sample_rate':rate,'generation_seconds':round(time.perf_counter()-start,3)}
 except Exception:result={'ok':False}
 print(json.dumps(result),flush=True)
