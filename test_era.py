import json,unittest
from store_offers import parse_era,PRODUCTS
class EraTests(unittest.TestCase):
 def test_identity_currency_and_visible_price_must_agree(self):
  expected=next(p for p in PRODUCTS if p.get('parser')=='era' and p['productId']=='bar20')
  p={'@type':'Product','name':expected['expectedTitle'],'brand':{'name':'Gold Era'},'description':'Price includes all the making and stamping fess.','offers':{'url':expected['url'],'priceCurrency':'EGP','price':'137400','availability':'https://schema.org/InStock'}}
  def html():return '<script type="application/ld+json">'+json.dumps(p)+'</script><p class="price">137,400.00 EGP</p>'
  r=parse_era(html(),expected);self.assertTrue(r['manufacturingIncluded']);self.assertTrue(r['stampIncluded']);self.assertIsNone(r['taxIncluded']);self.assertTrue(r['inStock'])
  with self.assertRaises(ValueError):parse_era(html().replace('137,400.00','137,500.00'),expected)
  p['name']='Gold 10 Gram Ingot'
  with self.assertRaises(ValueError):parse_era(html(),expected)
  p['name']=expected['expectedTitle'];p['offers']['priceCurrency']='USD'
  with self.assertRaises(ValueError):parse_era(html(),expected)
