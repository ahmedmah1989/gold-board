import json
import unittest
from marketplace_sources import parse_isagha_product


class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.expected=dict(sku='171',url='https://market.isagha.com/products/171',seller='آل حسن',weight=10,karat=24)
        p=dict(sku='171',url=self.expected['url'],brand={'name':'بي تي سي BTC'},description='سبيكة وزن 10 جرام عيار 24',
               offers=dict(url=self.expected['url'],price=65000,priceCurrency='EGP',availability='https://schema.org/InStock'))
        p['@type']='Product'
        self.html='<script type="application/ld+json">'+json.dumps(p,ensure_ascii=False)+'</script>'
        self.html+='<p data-testid="product-price"><span data-testid="price-figure">65000</span></p>'
        for k,v in [('صاحب المنتج','آل حسن'),('كود المنتج','171'),('العيار','عيار 24'),('وزن المنتج','10'),('الماركة','بي تي سي BTC'),('سعر المنتج','65000 جنيه')]:
            self.html+='<tr><th>'+k+'</th><td>'+v+'</td></tr>'

    def test_identity_and_same_response_agreement(self):
        p=parse_isagha_product(self.html,self.expected)
        self.assertEqual(p['listedPrice'],65000)
        self.assertEqual(p['seller'],'آل حسن')
        self.assertTrue(p['inStock'])
        self.assertIsNone(p['sourceTime'])
        self.assertIsNone(p['manufacturingIncluded'])

    def test_mismatch_rejected(self):
        for a,b in [('>65000</span>','>66000</span>'),('65000 جنيه','64000 جنيه'),('>آل حسن<','>other seller<'),('>10<','>20<'),('>عيار 24<','>عيار 21<'),('>171<','>172<'),('EGP','USD'),('وزن 10 جرام','وزن 100 جرام')]:
            with self.subTest(change=a),self.assertRaises((ValueError,KeyError)):
                parse_isagha_product(self.html.replace(a,b),self.expected)
        with self.assertRaises(ValueError):
            parse_isagha_product(self.html+self.html,self.expected)


if __name__=='__main__':
    unittest.main()
