import unittest
from notify_telegram import observation,reasons
from unittest.mock import patch
from notify_telegram import connect

class TelegramTests(unittest.TestCase):
    @patch('notify_telegram.save')
    @patch('notify_telegram.telegram')
    def test_connection_receipt_once(self,api,save):
        api.side_effect=[{'username':'goldmodybot'},{'type':'private','id':123},{}]
        state={}
        self.assertTrue(connect(state,'fake','123'))
        self.assertEqual(api.call_count,3)
        self.assertTrue(connect(state,'fake','123'))
        self.assertEqual(api.call_count,3)
    @patch('notify_telegram.save')
    @patch('notify_telegram.telegram')
    def test_wrong_bot_never_receives_message(self,api,save):
        api.return_value={'username':'anotherbot'}
        self.assertFalse(connect({},'fake','123'))
        self.assertEqual(api.call_count,1)
    @patch('notify_telegram.save')
    @patch('notify_telegram.telegram')
    def test_uncertain_receipt_is_not_retried(self,api,save):
        api.side_effect=[{'username':'goldmodybot'},{'type':'private','id':123},TimeoutError()]
        state={}
        self.assertFalse(connect(state,'fake','123'))
        self.assertFalse(connect(state,'fake','123'))
        self.assertEqual(api.call_count,3)
    def test_gate_and_calculations(self):
        q={'status':'available','sourceTime':'2026-11-11T12:00:00+00:00'}
        snap={'sources':{'isagha':{**q,'24':{'sell':5100},'21':{'sell':4462.5}},'misr':{**q,'sell':50},'gold':{**q,'sell':3110.34768}}}
        r=observation(snap,1794398400)
        # Explicit test clock uses the timestamp itself, not the host date.
        from notify_telegram import timestamp
        r=observation(snap,timestamp(q['sourceTime']))
        self.assertAlmostEqual(r['gap'],100);self.assertAlmostEqual(r['implied'],51)
        self.assertIsNone(observation(snap,timestamp(q['sourceTime'])+301))
        snap['sources']['gold']['sourceTime']='missing';self.assertIsNone(observation(snap))
    def test_thresholds(self):
        old={'gap':0,'gapPct':0,'fxGap':0,'fxPct':0,'local24':7000,'local21':6125,'dd24':0,'dd21':0}
        self.assertEqual(reasons(old,old,{'24':7000,'21':6125}),[])
        self.assertTrue(reasons(old,{**old,'gap':75},{'24':7000,'21':6125}))
        self.assertTrue(reasons(old,{**old,'local24':7001},{'24':7000,'21':6125}))
