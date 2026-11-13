"""Direct retail product observations; identity first, never gram-price multiplication."""
import json,re,urllib.request,math
from html import unescape
from html.parser import HTMLParser
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CATALOG=[
 {'id':'quarter','name':'ربع جنيه ذهب','kind':'quarter','weight':2,'karat':21},
 {'id':'half','name':'نصف جنيه ذهب','kind':'half','weight':4,'karat':21},
 {'id':'pound','name':'جنيه ذهب','kind':'pound','weight':8,'karat':21},
 *[{'id':'bar'+str(w).replace('.','_'),'name':'سبيكة '+str(w)+' جرام','kind':'bars','weight':w,'karat':24} for w in [1,2.5,5,10,20,50,100]],
 {'id':'ounce','name':'أونصة ذهب فعلية','kind':'ounce','weight':31.1034768,'karat':24,'weightBasis':'one_troy_ounce_nominal'},
]
GALLA='https://www.elgallagold.com/shop/'
DZ='https://dahabzaman.eg/en/products/gold/'
COINS={'quarter':('Quarter',2,'quarter-gold-pound-2-grams'),'half':('Half',4,'btc-half-gold-pound-4-grams'),'pound':('One',8,'btc-gold-pound-8-gm')}
DZ_BARS={1:'btc-1-gram-gold-bar',2.5:'btc-25-gram-gold-bar',5:'btc-5-gram-golds-bar',10:'btc-10-gram-gold-bar',20:'btc-20-gram-gold-bar',50:'btc-50-gram-golds-bar',100:'btc-100-gram-gold-bar'}
PRODUCTS=[]
for c in CATALOG:
 base={**c,'productId':c['id']};base.pop('id')
 if c['id'] in COINS:
  prefix,w,slug=COINS[c['id']];name=f'{prefix} Gold Coin, {w} Grams, 21 Karat';path='Gold-Coins/'+prefix+'-Gold-Coin/'
 elif c['kind']=='ounce':name='One Troy Ounce Gold Bar, 24 Karat';path='Gold-Bars/One-Troy-Ounce-Gold-Bar/'
 else:name=str(c['weight'])+'gr Gold Bar, 24 Karat';path='Gold-Bars/'+str(c['weight'])+'gr-Gold-Bar/'
 PRODUCTS.append({**base,'store':'الجلا جولد','brand':'El Galla','url':GALLA+path,'parser':'galla','expectedTitle':name})
 if c['id'] in COINS or c['weight'] in DZ_BARS:
  path='coins/'+COINS[c['id']][2] if c['id'] in COINS else 'ingots/'+DZ_BARS[c['weight']]
  PRODUCTS.append({**base,'store':'دهب زمان','brand':'BTC','url':DZ+path,'parser':'jsonld'})

# Each additional brand retains the same strict weight, karat, metal and URL checks.
for c in CATALOG:
 if c['kind']=='bars':
  slug='gold-era-'+str(c['weight']).replace('.','')+'-gram-gold-bar'
  PRODUCTS.append({**{k:v for k,v in c.items() if k!='id'},'productId':c['id'],'store':'دهب زمان','brand':'Gold Era','url':DZ+'ingots/'+slug,'parser':'jsonld'})

class Text(HTMLParser):
 def __init__(self):super().__init__();self.values=[]
 def handle_data(self,value):
  if value.strip():self.values.append(unescape(value.strip()))

def plain(html):
 p=Text();p.feed(html);return ' '.join(p.values)

def amount(text):return float(text.replace('EGP','').replace(',','').strip())

def parse_galla(html):
 p=Text();p.feed(html);v=p.values;i=v.index('Sell Price');segment=v[i:]
 gold=amount(segment[segment.index('Gold Amount')+1]);fees=amount(segment[segment.index('Making Charge + VAT')+1]);total=amount(segment[segment.index('Total')+1])
 if not all(math.isfinite(x) and x>=0 for x in (gold,fees,total)) or total<=0 or abs(gold+fees-total)>1:raise ValueError('invalid_product_total')
 result={'listedPrice':total,'goldAmount':gold,'makingAndVAT':fees,'taxIncluded':True,'manufacturingIncluded':True,'stampIncluded':None,'shippingIncluded':None,'sourceTime':None,'inStock':None,'identityVerified':True,
  'reason':'المصنعية والضريبة ضمن الإجمالي المعلن؛ شمول الدمغة والتوافر ووقت تسعير المنتج غير مؤكدة.'}
 if 'We buy at' in segment:
  try:
   buy=segment[segment.index('We buy at'):];gold_buy=amount(buy[buy.index('Gold Amount')+1]);cashback=amount(buy[buy.index('Cash back')+1]);total_buy=amount(buy[buy.index('Total')+1])
   if all(math.isfinite(x) and x>=0 for x in (gold_buy,cashback,total_buy)) and abs(gold_buy+cashback-total_buy)<=1:result.update(buybackPrice=total_buy,cashback=cashback)
  except (ValueError,IndexError):pass
 return result

def parse_jsonld(html,expected=None):
 products=[]
 for text in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',html,re.S):
  try:
   value=json.loads(text)
   if isinstance(value,dict) and value.get('@type')=='Product':products.append(value)
  except ValueError:continue
 if len(products)!=1:raise ValueError('ambiguous_product')
 product=products[0];offer=product['offers'];price=float(offer['price'])
 if offer['priceCurrency']!='EGP' or not math.isfinite(price) or price<=0:raise ValueError('invalid_product_price')
 props={str(x.get('name','')).lower():x.get('value') for x in product.get('additionalProperty',[])}
 if expected:
  weight=float(props['weight']);karat=float(props['karat']);brand=product.get('brand',{}).get('name','')
  if abs(weight-expected['weight'])>1e-6 or karat!=expected['karat'] or brand.lower()!=expected['brand'].lower() or str(props.get('metal','')).lower()!='gold':raise ValueError('identity_mismatch')
  if offer.get('url','').rstrip('/')!=expected['url'].rstrip('/') or product.get('url','').rstrip('/')!=expected['url'].rstrip('/'):raise ValueError('identity_mismatch')
 result={'listedPrice':price,'sourceTime':None,'inStock':True if offer.get('availability','').endswith('/InStock') else False if offer.get('availability','').endswith('/OutOfStock') else None,
  'manufacturingIncluded':None,'taxIncluded':None,'stampIncluded':None,'shippingIncluded':None,'identityVerified':True,'productTitle':product.get('name'),
  'reason':'سعر منشور للمنتج؛ شمول المصنعية والضريبة والدمغة ووقت التسعير غير مؤكدة، والسعر النهائي يراجَع لدى المتجر.'}
 for key,value in re.findall(r'<dt\b[^>]*>(.*?)</dt>\s*<dd\b[^>]*>(.*?)</dd>',html,re.S):
  if plain(key).strip().lower()=='manufacturing cost':
   try:
    making=amount(plain(value))
    if math.isfinite(making) and making>=0:result['declaredMakingCharge']=making
   except ValueError:pass
   break
 # A known catalog defect must be visible, not silently resolved by selecting convenient fields.
 if expected:
  descriptions=plain(product.get('description',''))
  weights=re.findall(r'\bWeight\s*:\s*(\d+(?:\.\d+)?)\s*(?:grams?|g)\b',descriptions,re.I)
  if any(abs(float(w)-expected['weight'])>1e-6 for w in weights):result.update(identityVerified=False,contentWarning='وصف المتجر يذكر وزنًا يختلف عن مواصفات المنتج؛ السعر محجوب حتى يتأكد التطابق.',reason='تعارض وزن في وصف المصدر؛ لا يعتمد هذا العرض للمقارنة.')
 return result

def eligible(offer,now):
 try:
  stamp=datetime.fromisoformat(offer['sourceTime'].replace('Z','+00:00'))
  if stamp.tzinfo is None:return False
  return offer['status']=='observed' and offer.get('identityVerified') is True and offer['inStock'] is True and all(offer.get(k) is True for k in ('manufacturingIncluded','taxIncluded','stampIncluded')) and -120<=now-stamp.timestamp()<=300 and type(offer.get('listedPrice')) in (int,float) and math.isfinite(offer['listedPrice']) and offer['listedPrice']>0
 except (KeyError,ValueError,AttributeError,TypeError):return False

def fetch(product):
 result={k:v for k,v in product.items() if k not in ('parser','expectedTitle')};result.update(requestedAt=datetime.now(timezone.utc).isoformat(),eligible=False)
 try:
  req=urllib.request.Request(product['url'],headers={'User-Agent':'GoldBoard/1.0 public product observation'})
  with urllib.request.urlopen(req,timeout=20) as response:html=response.read().decode('utf-8')
  if product['parser']=='galla':
   title=re.search(r'<title[^>]*>(.*?)</title>',html,re.S|re.I)
   if not title or product['expectedTitle'].lower() not in plain(title[1]).lower():raise ValueError('identity_mismatch')
   data=parse_galla(html)
  else:data=parse_jsonld(html,product)
  if not 100<data['listedPrice']/product['weight']<100000:raise ValueError('invalid_product_units')
  result.update(data,status='observed')
 except Exception as error:
  code=str(error) if isinstance(error,ValueError) else 'fetch_or_parse_failed'
  result.update(status='unavailable',identityVerified=False,errorCode=code,reason='تعذر توثيق صفحة المنتج ومواصفاته وسعره؛ افتح المصدر للمراجعة. لا نستخدم سعرًا محسوبًا من الجرام.')
 result['checkedAt']=datetime.now(timezone.utc).isoformat();result['eligible']=eligible(result,datetime.now(timezone.utc).timestamp());return result

def main():
 with ThreadPoolExecutor(max_workers=3) as pool:offers=list(pool.map(fetch,PRODUCTS))
 out={'schemaVersion':2,'catalogVersion':2,'checkedAt':datetime.now(timezone.utc).isoformat(),'catalog':CATALOG,'offers':offers,
      'qualifiedStores':len(set(o['store'] for o in offers if o['eligible'])),
      'coverageNotes':['متجر BTC الرسمي غير موصول بقناة عروض مؤرخة مستقرة.','الأونصة الفعلية منتج مستقل عن السعر العالمي؛ الأوزان المعروضة حسب مواصفات كل منتج.']}
 path=ROOT/'data/offers.json';path.parent.mkdir(exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8');temp.replace(path)
 print('Products:',len(CATALOG),'direct observations:',len(offers),'usable identities:',sum(o.get('identityVerified') is True for o in offers),'qualified stores:',out['qualifiedStores'])
if __name__=='__main__':main()
