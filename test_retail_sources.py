import json,unittest
from pathlib import Path
from retail_sources import parse_btc,parse_lazurde,extra_products,retailer_coverage
from store_offers import CATALOG
class RetailSourceTests(unittest.TestCase):
 def test_btc_price_currency_weight_and_page_identity(self):
  e=next(o for o in extra_products(CATALOG) if o['store']=='BTC' and o['productId']=='bar1')
  h='<h1 itemprop="name">Ingots - 1gm [24K]</h1><span itemprop="url">'+e['url']+'</span><div itemprop="offers"><span class="oe_currency_value">7,182.35</span><span itemprop="price">7182.35</span><span itemprop="priceCurrency">EGP</span></div>'
  r=parse_btc(h,e);self.assertEqual(r['listedPrice'],7182.35);self.assertEqual(r['priceKind'],'indicative');self.assertIsNone(r['inStock']);self.assertIsNone(r['sourceTime'])
  for bad in [h.replace('24K','21K'),h.replace('>EGP<','>SAR<'),h.replace('7,182.35','7,182.45'),h.replace(e['url'],e['url']+'wrong')]:
   with self.assertRaises(ValueError):parse_btc(bad,e)
 def lazurde(self,mutate=None,locale='ar-eg'):
  e=next(o for o in extra_products(CATALOG) if o['productId']=='lazurde-chain')
  p=json.loads((Path(__file__).parent/'tests/fixtures/lazurde-product-facts.json').read_text(encoding='utf-8'))
  if mutate:mutate(p)
  h='<script id="__NEXT_DATA__" type="application/json">'+json.dumps({'props':{'pageProps':{'locale':locale,'product':p}}})+'</script>'
  return parse_lazurde(h,e)
 def test_lazurde_egypt_total_with_verified_gold_weight(self):
  r=self.lazurde();self.assertEqual(r['listedPrice'],35850);self.assertTrue(r['inStock']);self.assertEqual(r['weightBasis'],'gold_weight');self.assertIsNone(r['manufacturingIncluded'])
 def test_lazurde_rejects_other_country_sku_currency_and_weight(self):
  changes=[lambda p:p.update(sku='wrong'),lambda p:p['prices']['price'].update(currencyCode='SAR'),lambda p:p['customFields']['edges'][-1]['node'].update(value='54.1g')]
  for change in changes:
   with self.assertRaises(ValueError):self.lazurde(change)
  with self.assertRaises(ValueError):self.lazurde(locale='ar-sa')
 def test_unavailable_brands_are_not_given_invented_prices(self):
  rows=retailer_coverage([]);self.assertEqual(len(rows),4);self.assertTrue(all(r['pricedProducts']==0 for r in rows));self.assertTrue(all('listedPrice' not in r for r in rows))
