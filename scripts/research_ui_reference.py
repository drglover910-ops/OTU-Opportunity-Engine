"""Read public authoritative accessibility and animation guidance; no account actions."""
import json,urllib.request,concurrent.futures,re
from html.parser import HTMLParser
from pathlib import Path
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.skip+=1
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
SOURCES=[
 ('Pause moving content','https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html',['five seconds','pause','essential']),
 ('Reduce animation','https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion',['reduce','vestibular','preference']),
 ('Frame scheduling','https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame',['background tabs','refresh rate','one-shot']),
 ('Canvas performance','https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas',['requestAnimationFrame','devicePixelRatio','offscreen']),
 ('Text contrast','https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html',['4.5:1','3:1']),
 ('Touch controls','https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html',['24 by 24','24 CSS','spacing'])]
def read(source):
 name,url,terms=source;result={'title':name,'url':url}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'OTU UI accessibility research'}),timeout=30) as r:page=r.read().decode('utf-8','replace');result['http_status']=r.status
  parser=Text();parser.feed(page);text=re.sub(r'\s+',' ',' '.join(parser.parts));excerpts=[]
  for term in terms:
   hit=re.search(re.escape(term),text,re.I)
   if hit:excerpts.append(text[max(0,hit.start()-130):hit.end()+300])
  result['excerpts']=excerpts;result['verified']=bool(excerpts)
 except Exception as error:result['verified']=False;result['error_type']=type(error).__name__
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(read,SOURCES))
Path('docs/UI_REFERENCE_RESEARCH.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps([{'title':r['title'],'verified':r['verified']} for r in results]))
