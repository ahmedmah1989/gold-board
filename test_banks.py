import unittest
from bank_sources import parse
class BankTests(unittest.TestCase):
 def test_rejected_and_missing_time(self):
  with self.assertRaises(ValueError):parse('<title>Request Rejected</title>','nbe')
  with self.assertRaises(ValueError):parse('<table><tr><td>US Dollar</td><td>50</td><td>51</td></tr></table>','nbe')
 def test_cbe_is_reference_not_bank_sell(self):
  html='<table><tr><td>US Dollar</td><td>50</td><td>51</td></tr></table>This page was last updated 11 Nov 2026'
  with self.assertRaisesRegex(ValueError,'missing_quote_time'):parse(html,'cbe')
