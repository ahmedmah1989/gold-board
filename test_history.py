import unittest
from datetime import date
from history_collect import parse_day,profile
class HistoryTests(unittest.TestCase):
 def test_actual_payload_date_required(self):
  with self.assertRaises(ValueError):parse_day({'date':'2026-11-09','xau':{'usd':4000,'egp':200000}},'2026-11-10')
  with self.assertRaises(ValueError):parse_day({'date':'2026-11-10','xau':{'usd':float('inf'),'egp':200000}},'2026-11-10')
 def test_weekday_coverage_does_not_count_weekends(self):
  p=profile([{'d':'2026-11-07'},{'d':'2026-11-09'},{'d':'2026-11-10'}],date(2026,11,10))
  self.assertEqual(p['availableWeekdays'],2)
  self.assertNotIn('2026-11-08',p['missingWeekdays'])
