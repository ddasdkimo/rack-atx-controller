import re,json,urllib.request,sys
from pathlib import Path
for c in sys.argv[1:]:
 s=Path('artifacts/local/catalog/'+c+'.html').read_text()
 stream=''.join(json.loads(m.group(1))[1] for m in re.finditer(r'self\.__next_f\.push\((\[1,.*?\])\)</script>',s))
 texts={m.group(1):stream[m.end():m.end()+int(m.group(2),16)] for m in re.finditer(r'([0-9a-f]+):T([0-9a-f]+),',stream)}
 ref=re.search(r'"dataManualFileAccessIdUrl":"\$([0-9a-f]+)"',stream)
 if ref and ref.group(1) in texts:
  try:urllib.request.urlretrieve(texts[ref.group(1)],'artifacts/local/'+c+'.pdf'); print(c,'downloaded')
  except Exception as e:print(c,type(e).__name__)
 else:print(c,'no link')
