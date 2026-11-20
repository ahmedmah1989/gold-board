import io
import json
import unittest
from datetime import datetime, timezone
from goldtimo import parse_price, crosscheck
from collection_health import receipt

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)


class FollowupTests(unittest.TestCase):
    def sample(self):
        return dict(symbol='XAU', currency='EGP', unit='oz', karat=21, price=200000,
                    gram=5500, gramBuy=5510, gramSell=5490, updatedAt=NOW.isoformat())

    def test_crosscheck_identity_and_values(self):
        self.assertEqual(parse_price(self.sample(), 21, NOW)['gramBuy'], 5510)
        for delta in ({'currency':'USD'}, {'karat':24}, {'gram':True}, {'gram':float('nan')},
                      {'gramBuy':1}, {'updatedAt':'2026-11-20T11:00:00Z'},
                      {'updatedAt':'2026-11-20T12:05:00Z'}, {'updatedAt':'2026-11-20T12:00:00'}):
            with self.assertRaises((ValueError,TypeError)):
                parse_price({**self.sample(),**delta}, 21, NOW)

    def test_not_configured_does_not_make_requests(self):
        def never(*args,**kw):
            raise AssertionError('request made')
        self.assertEqual(crosscheck('', never)['status'], 'not_configured')

    def test_request_errors_never_leak_key(self):
        def fail(*args,**kw):
            raise ValueError('secret-test-key')
        out = crosscheck('secret-test-key', fail)
        self.assertEqual(out['status'], 'incomplete')
        self.assertNotIn('secret-test-key', json.dumps(out))
        self.assertFalse(out['usedForPrimaryPrices'])
        self.assertFalse(out['directionVerified'])

    def test_collection_gap_not_hidden_by_new_snapshot(self):
        out = receipt('2026-11-20T11:00:00Z', {'generatedAt':NOW.isoformat()}, {'generatedAt':NOW.isoformat()}, NOW)
        self.assertEqual(out['status'], 'recent')
        self.assertTrue(out['missedTargetSincePrevious'])
        self.assertEqual(out['secondsSincePreviousCollection'], 3600)
        self.assertFalse(out['schedulerGuarantee'])

    def test_receipt_rejects_missing_old_naive_future(self):
        for stamp in (None, 'bad', '2026-11-20T12:00:00', '2026-11-20T11:00:00Z', '2026-11-20T12:10:00Z'):
            self.assertEqual(receipt(None, {'generatedAt':stamp}, {'generatedAt':NOW.isoformat()}, NOW)['status'], 'delayed')
        out=receipt('2026-11-20T11:55:00Z', {'generatedAt':NOW.isoformat()}, {'checkedAt':NOW.isoformat()}, NOW)
        self.assertEqual(out['status'],'recent')
        self.assertFalse(out['missedTargetSincePrevious'])


if __name__ == '__main__':
    unittest.main()
