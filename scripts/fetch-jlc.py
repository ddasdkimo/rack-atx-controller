#!/usr/bin/env python3
"""Read public JLC part pages; retain only public catalog fields, never signed URLs."""
import re,json,urllib.request,sys,concurrent.futures,datetime
from html.parser import HTMLParser
from pathlib import Path
class Text(HTMLParser):
 def __init__(self): super().__init__();self.items=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style'):self.skip+=1
 def handle_endtag(self,t):
  if t in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,s):
  if not self.skip and s.strip():self.items.append(s.strip())
def fetch(code):
 url='https://jlcpcb.com/partdetail/'+code
 cache=Path('artifacts/local/catalog/'+code+'.html')
 if cache.exists():
  raw=cache.read_text()
  previous=Path('hardware/research/'+code+'.json')
  checked=json.loads(previous.read_text()).get('checked_at') if previous.exists() else None
 else:
  raw=urllib.request.urlopen(url,timeout=40).read().decode()
  cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(raw);checked=None
 checked=checked or datetime.datetime.fromtimestamp(cache.stat().st_mtime,datetime.timezone.utc).isoformat()
 chunks=[]
 for m in re.finditer(r'self\.__next_f\.push\((\[1,.*?\])\)</script>',raw):
  try:chunks.append(json.loads(m.group(1))[1])
  except:pass
 records={}
 for ln in ''.join(chunks).splitlines():
  try:k,v=ln.split(':',1);records[k]=json.loads(v)
  except:pass
 ds=[d for d in records.values() if isinstance(d,dict) and d.get('componentCode')==code]
 part=next((d for d in ds if 'overseasStockCount' in d),{})
 spec=next((d for d in ds if 'attributes' in d),{})
 price=[{'min_qty':d['startNumber'],'max_qty':d['endNumber'],'usd':d['productPrice']} for d in ds if 'productPrice' in d]
 
 if part.get('initialPrice') is not None:price.insert(0,{'min_qty':1,'max_qty':price[0]['min_qty']-1 if price else -1,'usd':part['initialPrice']})
 parser=Text();parser.feed(raw);txt='\n'.join(parser.items)
 idx=txt.find('MFR.Part #');around=txt[max(0,idx-250):idx]
 library='Basic' if re.search(r'\bBasic\b',around) else 'Preferred Extended' if re.search(r'Preferred|Promotional',around) else 'Extended'
 def after(label):
  try:return parser.items[parser.items.index(label)+1]
  except:return None
 out={'id':code,'mpn':part.get('componentModelEn'),'manufacturer':part.get('componentBrandEn'),'package':part.get('componentSpecificationEn'),'classification':library,'assembly':after('Assembly Type'),'pcba_type':after('PCBA Type'),'stock':part.get('overseasStockCount'),'loss':part.get('lossNumber'),'prices':price,'source':url,'checked_at':checked,'status':'public JLC page observed; recheck at ordering'}
 Path('hardware/research/'+code+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 return out
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  for x in ex.map(fetch,sys.argv[1:]): print(json.dumps(x,ensure_ascii=False))
