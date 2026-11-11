import unittest
import json,tempfile
from pathlib import Path
import notify_telegram as notifier
from notify_telegram import observation,reasons
from unittest.mock import patch
from notify_telegram import connect,evaluate,local_observation

class TelegramTests(unittest.TestCase):
    def test_pending_market_delivery_remains_visible_without_new_trigger(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir()
            (root/'data/quotes.json').write_text('{}')
            state=root/'data/alert-state.json'
            state.write_text(json.dumps({'connection':{'status':'confirmed'},'delivery':{'status':'pending_or_unknown'}}))
            with patch.object(notifier,'ROOT',root),patch.object(notifier,'STATE',state),patch.dict('os.environ',{'TELEGRAM_BOT_TOKEN':'fake','TELEGRAM_CHAT_ID':'123'}),patch('notify_telegram.urllib.request.urlopen') as network:
                notifier.main()
                network.assert_not_called()
            self.assertEqual(json.loads(state.read_text())['service']['status'],'delivery_needs_review')
    def test_gap_reference_is_silent_then_uses_material_threshold(self):
        state={};old={'gap':0,'gapPct':0,'fxGap':0,'fxPct':0}
        self.assertEqual(evaluate(state,old,None)[0],[])
        self.assertEqual(evaluate(state,{**old,'gap':74},None)[0],[])
        self.assertEqual(len(evaluate(state,{**old,'gap':75},None)[0]),1)
    def test_local_peaks_do_not_require_bank_quote(self):
        state={};local={'local24':7000,'local21':6125,'time':1}
        self.assertEqual(evaluate(state,None,local)[0],[])
        self.assertEqual(evaluate(state,None,local)[0],[])
        why,_=evaluate(state,None,{**local,'local24':7001})
        self.assertEqual(len(why),1);self.assertIn('قمة محلية',why[0])
    def test_local_drawdown_and_stale_local_gate(self):
        state={};local={'local24':7000,'local21':6125,'time':1};evaluate(state,None,local)
        why,_=evaluate(state,None,{**local,'local24':6800})
        self.assertTrue(any('الهبوط' in x for x in why))
        q={'sources':{'isagha':{'status':'available','sourceTime':'2026-11-11T12:00:00Z','24':{'sell':7000},'21':{'sell':6125}}}}
        from notify_telegram import timestamp
        self.assertIsNotNone(local_observation(q,timestamp('2026-11-11T12:01:00Z')))
        self.assertIsNone(local_observation(q,timestamp('2026-11-11T12:06:00Z')))
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
