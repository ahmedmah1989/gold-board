import copy, unittest
from datetime import datetime, timezone, timedelta
from published_health import validate, recent

class PublishedHealthTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,20,14,0,tzinfo=timezone.utc)
        self.t=self.now.isoformat()
        self.q={'generatedAt':self.t,'sources':{'isagha':{'status':'available','sourceTime':self.t,'fetchedAt':self.t,'21':{'buy':5500,'sell':5550},'24':{'buy':6285.75,'sell':6342.75}}}}
        self.o={'checkedAt':self.t,'offers':[{'id':'test'}]}
    def test_real_published_observation(self):
        self.assertTrue(validate(self.q,self.o,self.now,self.t))
        self.assertFalse(validate(self.q,self.o,self.now,'different-run'))
    def test_fresh_fetch_cannot_hide_stale_provider(self):
        self.q['sources']['isagha']['sourceTime']=(self.now-timedelta(minutes=11)).isoformat()
        self.assertFalse(validate(self.q,self.o,self.now))
    def test_static200_or_bad_times_not_healthy(self):
        for value in [None,'bad','2026-11-20T14:00:00',(self.now+timedelta(minutes=3)).isoformat(),(self.now-timedelta(minutes=11)).isoformat()]:
            self.assertFalse(recent(value,self.now))
        for bad in [{},{'checkedAt':self.t,'offers':[]}]: self.assertFalse(validate(self.q,bad,self.now))
    def test_bad_prices_fail_closed(self):
        for v in [0,-1,float('nan'),float('inf'),True,'5550']:
            q=copy.deepcopy(self.q);q['sources']['isagha']['21']['sell']=v
            self.assertFalse(validate(q,self.o,self.now))
        self.q['sources']['isagha']['21']['buy']=6000
        self.assertFalse(validate(self.q,self.o,self.now))

if __name__=='__main__':unittest.main()
