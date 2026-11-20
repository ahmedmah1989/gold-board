import unittest
from store_offers import verified_observation, with_previous

class VerifiedFeedTests(unittest.TestCase):
 def offer(self,**kw):
  return dict(productId='pound',kind='pound',store='merchant',brand='mint',weight=8,karat=21,url='https://merchant.example/pound',status='observed',identityVerified=True,listedPrice=50000,checkedAt='2026-11-20T12:00:00Z',**kw)
 def test_only_verified_basic_prices(self):
  o=self.offer()
  self.assertTrue(verified_observation(o))
  for updates in ({'kind':'jewelry'},{'identityVerified':False},{'listedPrice':float('nan')},{'status':'unavailable'},{'url':'javascript:alert(1)'},{'url':'https://u:p@merchant.example'}):
   self.assertFalse(verified_observation({**o,**updates}))
 def test_previous_is_same_exact_offer_and_earlier(self):
  old=self.offer();current={**old,'listedPrice':51000,'checkedAt':'2026-11-20T12:30:00Z'}
  out=with_previous([current.copy()],[old])[0]
  self.assertEqual(out['previousPrice'],50000)
  self.assertEqual(out['previousCheckedAt'],old['checkedAt'])
  for updates in ({'brand':'other'},{'weight':4},{'url':'https://other.example/'},{'checkedAt':current['checkedAt']},{'identityVerified':False}):
   self.assertNotIn('previousPrice',with_previous([current.copy()],[{**old,**updates}])[0])
if __name__=='__main__':unittest.main()
