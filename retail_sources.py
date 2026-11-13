"""Named retailer observations. No conversion of jewelry totals into a shop gram rate."""
import json, math, re
from html import unescape

BTC_PATHS={'quarter':'2gm-322','half':'4gm-329','pound':'8gm-340','bar1':'1gm-311','bar2_5':'2-5gm-314','bar5':'5gm-335','bar10':'10gm-307','bar20':'20gm-318','bar50':'50gm-334','bar100':'100gm-306'}
LAZURDE=[
 ('lazurde-chain','115051400082450','rectangular-links-chain-necklace-in-18k-gold-sku-115051400082450','سلسلة بحلقات مستطيلة',5.41),
 ('lazurde-ring','115021100012180','polished-dome-ring-in-18k-gold-sku-115021100012180','خاتم قبة مصقولة — مقاس 18',5),
 ('lazurde-earrings','113031400172001','circles-drop-earrings-in-18k-gold-sku-113031400172001','أقراط متدلية بأشكال دائرية',4.6),
]

def extra_products(catalog):
 out=[]
 for c in catalog:
  if c['id'] not in BTC_PATHS:continue
  title=('Coins' if c['karat']==21 else 'Ingots')+' - '+str(c['weight'])+'gm ['+str(c['karat'])+'K]'
  out.append({**{k:v for k,v in c.items() if k!='id'},'productId':c['id'],'store':'BTC','brand':'BTC','parser':'btc','expectedTitle':title,'url':'https://eg-backend.bulliontradingcenter.com/shop/'+BTC_PATHS[c['id']]})
 for pid,sku,slug,name,weight in LAZURDE:
  out.append({'productId':pid,'name':name,'kind':'jewelry','weight':weight,'karat':18,'sku':sku,'store':'لازوردي','brand':"L'azurde",'parser':'lazurde','url':'https://www.lazurde.com/ar-eg/p/'+slug})
 return out

def text(value):return re.sub(r'\s+',' ',unescape(re.sub(r'<[^>]+>',' ',value))).strip()

def field(html,name):
 values=re.findall(r'<([\w]+)\b[^>]*\bitemprop=["\']'+re.escape(name)+r'["\'][^>]*>(.*?)</\1>',html,re.S|re.I)
 if len(values)!=1:raise ValueError('ambiguous_'+name)
 return text(values[0][1])

def base(price,stock=None):
 if not math.isfinite(price) or price<=0:raise ValueError('invalid_product_price')
 return {'listedPrice':price,'sourceTime':None,'inStock':stock,'manufacturingIncluded':None,'taxIncluded':None,'stampIncluded':None,'shippingIncluded':None,'identityVerified':True}

def parse_btc(html,expected):
 if field(html,'name')!=expected['expectedTitle'] or field(html,'url').rstrip('/')!=expected['url'].rstrip('/'):raise ValueError('identity_mismatch')
 if field(html,'priceCurrency')!='EGP':raise ValueError('invalid_currency')
 price=float(field(html,'price'))
 start=re.search(r'itemprop=["\']offers["\']',html)
 if not start:raise ValueError('missing_offer')
 visible=re.search(r'<span\b[^>]*class=["\']oe_currency_value["\'][^>]*>(.*?)</span>',html[start.start():],re.S)
 if not visible or abs(float(text(visible[1]).replace(',',''))-price)>.01:raise ValueError('price_mismatch')
 result=base(price)
 result.update(priceKind='indicative',reason='سعر استرشادي للوزن المعروض. التصميم والتوافر والرسوم والإجمالي يراجعون قبل الشراء.')
 return result

def parse_lazurde(html,expected):
 match=re.search(r'<script\b[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',html,re.S)
 if not match:raise ValueError('missing_product_data')
 props=json.loads(match[1])['props']['pageProps'];p=props['product']
 if isinstance(p,str):p=json.loads(p)
 custom={i['node']['name']:i['node']['value'] for i in p['customFields']['edges']}
 if props.get('locale')!='ar-eg' or p.get('sku')!=expected['sku'] or custom.get('Country')!='EGY':raise ValueError('identity_mismatch')
 if p.get('brand',{}).get('name')!="L'azurde":raise ValueError('identity_mismatch')
 weight=re.fullmatch(r'(\d+(?:\.\d+)?)\s*g',custom.get('Gold Weight',''))
 if not weight or abs(float(weight[1])-expected['weight'])>1e-6 or custom.get('Metal Karat')!=str(expected['karat'])+'K':raise ValueError('identity_mismatch')
 price=p['prices']['price']
 if price.get('currencyCode')!='EGP':raise ValueError('invalid_currency')
 result=base(float(price['value']),p.get('inventory',{}).get('isInStock'))
 result.update(weightBasis='gold_weight',productTitle=p.get('newTitle') or expected['name'],reason='سعر القطعة كاملة حسب الموديل والوزن؛ ليس سعر جرام الذهب الخام.')
 return result

def retailer_coverage(offers):
 return [{'name':name,'category':category,'pricedProducts':sum(o.get('store')==name and o.get('status')=='observed' and o.get('identityVerified') is True for o in offers),'status':status}
  for name,category,status in [('لازوردي','jewelry','connected'),('BTC','bullion','connected'),('إيجيبت جولد','jewelry','access_required'),('مجوهرات واصف','jewelry','awaiting_verified_prices')]]
