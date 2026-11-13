import unittest
from local_history import update


def quotes(time, sell21=5950.0, sell24=6800.0, status='available', usd=53.49):
    return {'sources': {
        'isagha': {'status': status, 'sourceTime': time,
                   '24': {'sell': sell24, 'buy': sell24 - 60}, '21': {'sell': sell21, 'buy': sell21 - 50}},
        'misr': {'status': 'available', 'sell': usd},
    }}


class LocalHistory(unittest.TestCase):
    def test_day_record_tracks_open_high_low_close(self):
        h = {'days': []}
        h, c = update(h, quotes('2026-11-13T10:00:00+02:00', 5950)); self.assertTrue(c)
        h, c = update(h, quotes('2026-11-13T12:00:00+02:00', 6000)); self.assertTrue(c)
        h, c = update(h, quotes('2026-11-13T15:00:00+02:00', 5900)); self.assertTrue(c)
        day = h['days'][0]
        self.assertEqual(day['d'], '2026-11-13')
        self.assertEqual(day['21'], {'open': 5950, 'high': 6000, 'low': 5900, 'close': 5900, 'closeBuy': 5850})
        self.assertEqual(day['readings'], 3)
        self.assertEqual(day['usd'], 53.49)

    def test_same_published_time_is_not_counted_twice(self):
        h = {'days': []}
        update(h, quotes('2026-11-13T10:00:00+02:00'))
        h, c = update(h, quotes('2026-11-13T10:00:00+02:00', 9999))
        self.assertFalse(c); self.assertEqual(h['days'][0]['readings'], 1); self.assertEqual(h['days'][0]['21']['close'], 5950)

    def test_day_is_the_cairo_date_and_new_day_adds_record(self):
        h = {'days': []}
        update(h, quotes('2026-11-13T22:30:00+00:00'))          # 00:30 on the 14th in Cairo
        self.assertEqual(h['days'][0]['d'], '2026-11-14')
        update(h, quotes('2026-11-15T09:00:00+02:00'))
        self.assertEqual([d['d'] for d in h['days']], ['2026-11-14', '2026-11-15'])

    def test_unavailable_invalid_or_older_readings_change_nothing(self):
        h = {'days': []}
        update(h, quotes('2026-11-13T10:00:00+02:00'))
        for bad in (quotes('2026-11-13T11:00:00+02:00', status='unavailable'),
                    quotes('2026-11-12T11:00:00+02:00'),
                    quotes('2026-11-13T11:00:00'),
                    quotes('2026-11-13T11:00:00+02:00', sell21=0)):
            h, c = update(h, bad); self.assertFalse(c)
        self.assertEqual(len(h['days']), 1); self.assertEqual(h['days'][0]['readings'], 1)


if __name__ == '__main__':
    unittest.main()
