"""Build-time public model fetch with pinned SHA256; no paid inference or credentials."""
import sys,hashlib,urllib.request
from pathlib import Path
root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True)
assets={'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for name,digest in assets.items():
 target=root/name
 if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
  url='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'+name
  with urllib.request.urlopen(url,timeout=120) as response,target.open('wb') as stream:
   while block:=response.read(4*1024**2):stream.write(block)
 if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise SystemExit('Voice model checksum mismatch')
 print(name+' verified')
