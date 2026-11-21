import unittest
from bank_sources import parse
class BankTests(unittest.TestCase):
 def test_rejected_and_missing_time(self):
  with self.assertRaises(ValueError):parse('<title>Request Rejected</title>','nbe')
  with self.assertRaises(ValueError):parse('<table><tr><td>US Dollar</td><td>50</td><td>51</td></tr></table>','nbe')
 def test_cbe_is_reference_not_bank_sell(self):
  html='<table><tr><td>US Dollar</td><td>50</td><td>51</td></tr></table>This page was last updated 11 Nov 2026'
  with self.assertRaisesRegex(ValueError,'missing_quote_time'):parse(html,'cbe')
 def test_cbe_heading_date(self):
  html='<h3>Average Market Rate in EGP</h3>19 Nov 2026<table><tr><td>US Dollar</td><td>53.7629</td><td>53.8629</td></tr></table>This page was last updated 19 Nov 2026'
  html=html.replace('EGP</h3>','EGP 19 Nov 2026</h3>').replace('</h3>19 Nov 2026','</h3>')
  r=parse(html,'cbe');self.assertEqual((r['buy'],r['sell'],r['quoteDate']),(53.7629,53.8629,'2026-11-19'))
  with self.assertRaisesRegex(ValueError,'missing_quote_time'):parse(html.replace('19 Nov 2026</h3>','19 Nov 2099</h3>'),'cbe')
