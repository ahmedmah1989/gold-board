"""Direct product observations. Never infer final coin prices from gram quotes."""
import json,re,urllib.request,math
from html import unescape
from html.parser import HTMLParser
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PRODUCTS=[
 {'store':'الجلا جولد','brand':'El Galla','weight':8,'url':'https://www.elgallagold.com/shop/Gold-Coins/One-Gold-Coin/','parser':'galla'},
 {'store':'الجلا جولد','brand':'El Galla','weight':4,'url':'https://www.elgallagold.com/shop/Gold-Coins/Half-Gold-Coin/','parser':'galla'},
 {'store':'دهب زمان','brand':'BTC','weight':8,'url':'https://dahabzaman.eg/en/products/gold/coins/btc-gold-pound-8-gm','parser':'jsonld'},
 {'store':'دهب زمان','brand':'BTC','weight':4,'url':'https://dahabzaman.eg/en/products/gold/coins/btc-half-gold-pound-4-grams','parser':'jsonld'},
 {'store':'متجر BTC الرسمي','brand':'BTC','weight':8,'url':'https://shop.bulliontradingcenter.com/','parser':'unavailable'},
]
class Text(HTMLParser):
 def __init__(self):super().__init__();self.values=[]
 def handle_data(self,value):
  if value.strip():self.values.append(unescape(value.strip()))

def parse_galla(html):
 p=Text();p.feed(html);v=p.values;i=v.index('Sell Price');segment=v[i:];gold=float(segment[segment.index('Gold Amount')+1].replace('EGP','').replace(',','').strip());fees=float(segment[segment.index('Making Charge + VAT')+1].replace('EGP','').replace(',','').strip());total=float(segment[segment.index('Total')+1].replace('EGP','').replace(',','').strip())
 if not all(math.isfinite(v) and v>=0 for v in (gold,fees,total)) or not 1000<total<200000 or abs(gold+fees-total)>1:raise ValueError('Inconsistent product total')
 return {'listedPrice':total,'goldAmount':gold,'makingAndVAT':fees,'taxIncluded':True,'manufacturingIncluded':True,'stampIncluded':None,'sourceTime':None,'inStock':None,'reason':'سعر منتج إجمالي معلن مع المصنعية والضريبة، لكن شمول الدمغة ووقت تسعير المنتج والتوافر غير موثقين صراحة.'}

def parse_jsonld(html):
 products=[]
 for text in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',html,re.S):
  try:
   value=json.loads(text)
   if value.get('@type')=='Product':products.append(value)
  except (ValueError,AttributeError):continue
 if len(products)!=1:raise ValueError('Product identity ambiguous')
 offer=products[0]['offers'];price=float(offer['price'])
 if offer['priceCurrency']!='EGP' or not 1000<price<200000:raise ValueError('Invalid product offer')
 return {'listedPrice':price,'sourceTime':None,'inStock':offer.get('availability','').endswith('/InStock'),'manufacturingIncluded':None,'taxIncluded':None,'stampIncluded':None,'reason':'سعر المنتج منشور؛ سياسة المتجر تؤكد السعر النهائي عند الدفع. شمول كل الرسوم ووقت التسعير غير مثبتين في العرض العام.'}

def eligible(offer,now):
 try:
  t=datetime.fromisoformat(offer['sourceTime'].replace('Z','+00:00')).timestamp()
  return offer['status']=='observed' and offer['inStock'] is True and all(offer.get(k) is True for k in ('manufacturingIncluded','taxIncluded','stampIncluded')) and -120<=now-t<=300 and type(offer.get('listedPrice')) in (int,float) and math.isfinite(offer['listedPrice']) and offer['listedPrice']>0
 except (KeyError,ValueError,AttributeError,TypeError):return False

def fetch(product):
 result={k:v for k,v in product.items() if k!='parser'};result.update(karat=21,checkedAt=datetime.now(timezone.utc).isoformat(),eligible=False)
 try:
  req=urllib.request.Request(product['url'],headers={'User-Agent':'GoldBoard/1.0 public product observation'})
  with urllib.request.urlopen(req,timeout=20) as response:html=response.read().decode('utf-8')
  if product['parser']=='unavailable':raise ValueError('No verifiable public offer')
  if product['parser']=='galla' and not re.search(r'(?:One|Half) Gold Coin,\s*'+str(product['weight'])+r'\s*Grams,\s*21\s*Karat',html,re.I):raise ValueError('Product identity mismatch')
  if product['parser']=='jsonld':
   text=Text();text.feed(html)
   if not re.search(r'\b'+str(product['weight'])+r'\s*(?:Grams|g)\b',' '.join(text.values),re.I):raise ValueError('Product weight mismatch')
  result.update((parse_galla if product['parser']=='galla' else parse_jsonld)(html));result['status']='observed'
 except Exception:result.update(status='unavailable',reason='تعذر توثيق عرض منتج مباشر صالح؛ لم يُستنتج سعر بضرب الجرام في الوزن.')
 result['eligible']=eligible(result,datetime.now(timezone.utc).timestamp());return result

def main():
 with ThreadPoolExecutor(max_workers=3) as pool:offers=list(pool.map(fetch,PRODUCTS))
 out={'schemaVersion':1,'checkedAt':datetime.now(timezone.utc).isoformat(),'offers':offers,'qualifiedStores':len(set(o['store'] for o in offers if o['eligible']))}
 Path('data').mkdir(exist_ok=True);Path('data/offers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Product observations:',len(offers),'qualified stores:',out['qualifiedStores'])
if __name__=='__main__':main()
