import unittest
from collect import parse_isagha, parse_misr

class ParseTests(unittest.TestCase):
    def test_isagha_sides(self):
        def row(unit, sell, buy):
            return f'<tr data-unit="{unit}"><td>label</td><td><span data-testid="price-figure">{sell}</span></td><td>gap</td><td><span data-testid="price-figure">{buy}</span></td></tr>'
        html = '<time datetime="2026-11-11T12:00:00+02:00" data-testid="prices-updated">'
        data = parse_isagha(html + row(24, 8000, 7900) + row(21, 7000, 6900))
        self.assertEqual(data['24']['sell'], 8000)
        self.assertEqual(data['21']['buy'], 6900)
        with self.assertRaises(ValueError): parse_isagha(row(24, 8000, 7900))
    def test_bank_notes_not_transfer(self):
        html = '<div class="generic-details-title"><p>11-11-2026 12:00:00</p></div><tr><td>US Dollar</td><td>50</td><td>51</td><td>52</td><td>53</td></tr>'
        data = parse_misr(html)
        self.assertEqual(data['buy'], 50)
        self.assertEqual(data['sell'], 51)
        with self.assertRaises(ValueError): parse_misr('<html>Request Rejected</html>')
