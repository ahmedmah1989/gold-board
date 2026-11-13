import unittest,json
from store_offers import parse_galla,parse_jsonld,eligible,CATALOG,PRODUCTS
from datetime import datetime,timezone
class OfferTests(unittest.TestCase):
 def test_total(self):
  s='<div>Sell Price</div><div>Gold Amount</div><div>49,000 EGP</div><div>Making Charge + VAT</div><div>600 EGP</div><div>Total</div><div>49,600 EGP</div>'
  self.assertEqual(parse_galla(s)['listedPrice'],49600)
  with self.assertRaises(ValueError):parse_galla(s.replace('49,600','49,700'))
 def test_unknown_fees_excluded(self):
  now=datetime.now(timezone.utc);o={'status':'observed','identityVerified':True,'listedPrice':50000,'sourceTime':now.isoformat(),'inStock':True,'manufacturingIncluded':True,'taxIncluded':True,'stampIncluded':None}
  self.assertFalse(eligible(o,now.timestamp()));o['stampIncluded']=True;self.assertTrue(eligible(o,now.timestamp()));o['inStock']=False;self.assertFalse(eligible(o,now.timestamp()))
 def test_catalog_has_exact_coins_bar_weights_and_physical_ounce(self):
  c={p['id']:p for p in CATALOG}
  self.assertEqual([c[k]['weight'] for k in ['quarter','half','pound']],[2,4,8])
  self.assertEqual(c['ounce']['weight'],31.1034768)
  self.assertEqual(c['bar100']['karat'],24)
  self.assertTrue(any(p['brand']=='Gold Era' and p['productId']=='bar10' for p in PRODUCTS))
  self.assertEqual(len({p['url'] for p in PRODUCTS}),len(PRODUCTS))
 def test_jsonld_requires_weight_karat_brand_and_own_url(self):
  expected={'weight':100,'karat':24,'brand':'BTC','url':'https://example.test/bar'}
  product={'@type':'Product','name':'BTC 100 Gram Gold Bar 24K','url':expected['url'],'brand':{'name':'BTC'},'additionalProperty':[{'name':'Metal','value':'Gold'},{'name':'Karat','value':'24'},{'name':'Weight','value':100}], 'offers':{'url':expected['url'],'price':710000,'priceCurrency':'EGP','availability':'https://schema.org/OutOfStock'}}
  def html():return '<script type="application/ld+json">'+json.dumps(product)+'</script><dl><dt>Manufacturing cost</dt><dd>7,700 EGP</dd></dl>'
  self.assertEqual(parse_jsonld(html(),expected)['listedPrice'],710000)
  self.assertEqual(parse_jsonld(html(),expected)['declaredMakingCharge'],7700)
  self.assertIsNone(parse_jsonld(html(),expected)['manufacturingIncluded'])
  product['additionalProperty'][-1]['value']=10
  with self.assertRaises(ValueError):parse_jsonld(html(),expected)
 def test_conflicting_description_cannot_enter_comparison(self):
  expected={'weight':2,'karat':21,'brand':'BTC','url':'https://example.test/quarter'}
  p={'@type':'Product','name':'Quarter 2 Grams','description':'Weight: 4 Grams','url':expected['url'],'brand':{'name':'BTC'},'additionalProperty':[{'name':'Metal','value':'Gold'},{'name':'Karat','value':'21'},{'name':'Weight','value':2}], 'offers':{'url':expected['url'],'price':12500,'priceCurrency':'EGP'}}
  result=parse_jsonld('<script type="application/ld+json">'+json.dumps(p)+'</script>',expected)
  self.assertFalse(result['identityVerified']);self.assertIsNone(result['inStock'])
