import unittest
from pathlib import Path
from silver_sources import parse_isagha_silver

FX = Path(__file__).parent / 'tests/fixtures/isagha_silver_excerpt.html'

class SilverTests(unittest.TestCase):
    def test_dated_page_excerpt(self):
        d = parse_isagha_silver(FX.read_text(encoding='utf-8'))
        self.assertEqual(d['sourceTime'], '2026-11-21T12:36:54+02:00')
        self.assertEqual(d['grades']['999'], {'sell': 73.75, 'buy': 70.75})
        self.assertEqual(d['grades']['925'], {'sell': 68.5, 'buy': 65.5})
        self.assertEqual(d['grades']['600']['sell'], 44.25)
        self.assertEqual(d['ounceUsd'], {'sell': 41.36, 'buy': 41.24})
    def test_fail_closed(self):
        h = FX.read_text(encoding='utf-8')
        import re
        swapped = re.sub(r'(<th\b[^>]*>\s*)بيع', r'\1TMP', h, count=1)
        swapped = re.sub(r'(<th\b[^>]*>\s*)شراء', r'\1بيع', swapped, count=1).replace('TMP', 'شراء')
        for bad in (h.replace('data-testid="prices-updated"', ''), swapped, h.replace('data-unit="925"', 'data-unit="x"')):
            with self.assertRaises(ValueError): parse_isagha_silver(bad)
        with self.assertRaises(ValueError): parse_isagha_silver(h.replace('+02:00', ''))

    def row_cell(self, h, unit, idx, new_inner=None, sub=None):
        import re
        m = re.search(r'<tr\b[^>]*data-unit="%s"[^>]*>.*?</tr>' % unit, h, re.S)
        cells = list(re.finditer(r'<td\b.*?</td>', m[0], re.S))
        c = cells[idx]
        repl = sub(c[0])
        return h.replace(m[0], m[0].replace(c[0], repl))
    def test_currency_labels_required_both_ways(self):
        h = FX.read_text(encoding='utf-8')
        for unit, idx, a, b in (('999', 1, 'ج.م', '$'), ('999', 3, 'ج.م', '$'), ('s_ounce', 1, '$', 'ج.م'), ('s_ounce', 3, '$', 'ج.م'), ('925', 1, 'ج.م', '')):
            with self.assertRaises(ValueError): parse_isagha_silver(self.row_cell(h, unit, idx, sub=lambda c: c.replace(a, b)))
    def test_swapped_adjacent_grades_rejected(self):
        h = FX.read_text(encoding='utf-8')
        h = self.row_cell(h, '925', 1, sub=lambda c: c.replace('68.5', '66.5'))
        h = self.row_cell(h, '900', 1, sub=lambda c: c.replace('66.5', '68.5'))
        with self.assertRaises(ValueError): parse_isagha_silver(h)
    def test_purity_boundary(self):
        h = FX.read_text(encoding='utf-8')
        # 925 sell near purity ratio (0.926 * 73.75 = 68.3) passes; 3 points off (0.956 * 73.75 = 70.5) fails the ratio rule.
        parse_isagha_silver(self.row_cell(h, '925', 1, sub=lambda c: c.replace('68.5', '68.3')))
        with self.assertRaises(ValueError): parse_isagha_silver(self.row_cell(h, '925', 1, sub=lambda c: c.replace('68.5', '70.5')))
    def test_bad_figures(self):
        h = FX.read_text(encoding='utf-8')
        for unit, idx, old, new in (('999', 1, '73.75', '1,073.75'), ('999', 1, '73.75', '70.0'), ('800', 3, '56.75', '59.30'), ('s_ounce', 1, '41.36', '41.0'), ('s_ounce', 3, '41.24', '0'), ('s_ounce', 1, '41.36', 'abc'), ('999', 1, '73.75', '73.75.1')):
            with self.assertRaises(ValueError): parse_isagha_silver(self.row_cell(h, unit, idx, sub=lambda c: c.replace(old, new)))
    def test_unit_checked_against_pound_row(self):
        h = FX.read_text(encoding='utf-8')
        self.assertIn('does not state weight or grade', parse_isagha_silver(h)['unitBasis'])
        for idx, old, new in ((1, '548', '560'), (3, '524', '500')):
            with self.assertRaises(ValueError): parse_isagha_silver(self.row_cell(h, 'pound', idx, sub=lambda c: c.replace(old, new)))
        # every grade scaled to per-ounce while the pound row stays: rejected
        bad = h
        for g, (sell, buy) in (('999', ('73.75', '70.75')), ('925', ('68.5', '65.5')), ('900', ('66.5', '63.75')), ('800', ('59.25', '56.75')), ('600', ('44.25', '42.5'))):
            bad = self.row_cell(bad, g, 1, sub=lambda c: c.replace(sell, str(round(float(sell) * 31, 2))))
            bad = self.row_cell(bad, g, 3, sub=lambda c: c.replace(buy, str(round(float(buy) * 31, 2))))
        with self.assertRaises(ValueError): parse_isagha_silver(bad)
    def test_old_source_time_is_kept_not_refreshed(self):
        import collect
        from unittest import mock
        h = FX.read_text(encoding='utf-8').replace('2026-11-21T12:36:54+02:00', '2026-11-10T12:00:00+02:00')
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return h.encode('utf-8')
        with mock.patch('collect.urllib.request.urlopen', return_value=R()):
            name, d = collect.fetch('isagha_silver')
        self.assertEqual(d['status'], 'available'); self.assertEqual(d['sourceTime'], '2026-11-10T12:00:00+02:00')
        self.assertNotEqual(d['sourceTime'], d['fetchedAt']); self.assertIn('requestedAt', d)
    def scaled(self, h, k):
        import re
        out = h
        for u in ('999', '925', '900', '800', '600', 'pound'):
            m = re.search(r'<tr\b[^>]*data-unit="%s"[^>]*>.*?</tr>' % u, out, re.S)
            row = re.sub(r'(data-testid="price-figure"[^>]*>)(\d+(?:\.\d+)?)(</span>)', lambda x: x[1] + repr(round(float(x[2]) * k, 4)) + x[3], m[0])
            out = out.replace(m[0], row)
        return out
    def test_uniform_rescale_of_whole_silver_table_rejected(self):
        h = FX.read_text(encoding='utf-8')
        parse_isagha_silver(self.scaled(h, 1.0))
        for k in (31.1034768, 1 / 31.1034768, 2, 0.5, 1.15, 0.85):
            with self.assertRaises(ValueError) as c: parse_isagha_silver(self.scaled(h, k))
            self.assertIn('scale check failed', str(c.exception))
        for k in (1.05, 0.95): parse_isagha_silver(self.scaled(h, k))
    def test_scale_check_needs_the_gold_ticker(self):
        import re
        h = FX.read_text(encoding='utf-8')
        with self.assertRaises(ValueError) as c: parse_isagha_silver(re.sub(r'<nav>.*?</nav>', '', h, flags=re.S))
        self.assertIn('scale check failed', str(c.exception))
        with self.assertRaises(ValueError): parse_isagha_silver(h.replace('data-metal="gold"', 'data-metal="silver"'))
    def test_ticker_currency_labels_required(self):
        h = FX.read_text(encoding='utf-8')
        parse_isagha_silver(h)
        import re
        nav = re.search(r'<nav>.*?</nav>', h, re.S)[0]
        for a, b in (('<small>ج.م</small>', '<small>$</small>'), ('<small>$</small>', '<small>ج.م</small>'), ('<small>ج.م</small>', ''), ('<small>$</small>', '<small>USD</small>')):
            with self.assertRaises(ValueError) as c: parse_isagha_silver(h.replace(nav, nav.replace(a, b)))
            self.assertIn('scale check failed', str(c.exception))
if __name__ == '__main__': unittest.main()
