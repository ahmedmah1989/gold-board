import unittest
from store_offers import parse_galla,parse_jsonld,eligible
from datetime import datetime,timezone
class OfferTests(unittest.TestCase):
 def test_total(self):
  s='<div>Sell Price</div><div>Gold Amount</div><div>49,000 EGP</div><div>Making Charge + VAT</div><div>600 EGP</div><div>Total</div><div>49,600 EGP</div>'
  self.assertEqual(parse_galla(s)['listedPrice'],49600)
  with self.assertRaises(ValueError):parse_galla(s.replace('49,600','49,700'))
 def test_unknown_fees_excluded(self):
  now=datetime.now(timezone.utc);o={'status':'observed','listedPrice':50000,'sourceTime':now.isoformat(),'inStock':True,'manufacturingIncluded':True,'taxIncluded':True,'stampIncluded':None}
  self.assertFalse(eligible(o,now.timestamp()));o['stampIncluded']=True;self.assertTrue(eligible(o,now.timestamp()));o['inStock']=False;self.assertFalse(eligible(o,now.timestamp()))
