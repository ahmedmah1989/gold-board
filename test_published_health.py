import copy, unittest
from datetime import datetime, timezone, timedelta
from published_health import validate, recent, wait_for_publication, source_state, generated_at_least

class PublishedHealthTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,20,14,0,tzinfo=timezone.utc)
        self.t=self.now.isoformat()
        self.q={'generatedAt':self.t,'sources':{'isagha':{'status':'available','sourceTime':self.t,'fetchedAt':self.t,'21':{'buy':5500,'sell':5550},'24':{'buy':6285.75,'sell':6342.75}}}}
        self.o={'checkedAt':self.t,'offers':[{'id':'test'}]}
    def test_real_published_observation(self):
        self.assertTrue(validate(self.q,self.o,self.now,self.t))
        self.assertFalse(validate(self.q,self.o,self.now,'different-run'))
    def test_newer_published_generation_proves_superseded_run_alive(self):
        # A later run published over this one: pipeline demonstrably alive.
        self.assertTrue(validate(self.q,self.o,self.now,(self.now-timedelta(minutes=3)).isoformat()))
    def test_older_published_generation_is_not_this_run(self):
        # A recent but older publication (previous cycle's file) must not satisfy this run.
        self.q['generatedAt']=(self.now-timedelta(minutes=3)).isoformat()
        self.assertFalse(validate(self.q,self.o,self.now,self.t))
        self.assertFalse(generated_at_least('bad', self.t))
        self.assertFalse(generated_at_least(self.t, 'bad'))
        self.assertFalse(generated_at_least('2026-11-20T14:00:00', self.t))
    def test_fresh_fetch_cannot_hide_stale_provider(self):
        self.q['sources']['isagha']['sourceTime']=(self.now-timedelta(minutes=11)).isoformat()
        # The pipeline proof passes on its own timestamps; provider age is reported, not hidden.
        self.assertTrue(validate(self.q,self.o,self.now))
        self.assertEqual(source_state(self.q['sources']['isagha'],self.now),'quiet')
    def test_fresh_provider_reports_fresh(self):
        self.assertEqual(source_state(self.q['sources']['isagha'],self.now),'fresh')
    def test_provider_older_than_display_limit_fails_closed(self):
        self.q['sources']['isagha']['sourceTime']=(self.now-timedelta(hours=25)).isoformat()
        self.assertFalse(validate(self.q,self.o,self.now))
        self.assertIsNone(source_state(self.q['sources']['isagha'],self.now))
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

    def test_wait_accepts_slow_pages_build_inside_the_wall_clock_limit(self):
        clock=[self.now+timedelta(seconds=30)]
        calls=[]
        def now(): return clock[0]
        def sleep(s): clock[0]+=timedelta(seconds=s)
        def fetch(name):
            calls.append(name)
            return copy.deepcopy(self.q if name=='quotes.json' else self.o)
        def check(q,o,at,exp):
            # Old files until 5.7 minutes after generation, then the new run is visible.
            return (at-self.now).total_seconds()>=342 and validate(q,o,at,exp)
        self.assertTrue(wait_for_publication(fetch,check,self.t,now,sleep))
        self.assertLessEqual((clock[0]-self.now).total_seconds(),600)
    def test_wait_never_accepts_publication_after_ten_minutes(self):
        clock=[self.now+timedelta(seconds=30)]
        def now(): return clock[0]
        def sleep(s): clock[0]+=timedelta(seconds=s)
        # Files appear 11 minutes late: validate() rejects the aged timestamps and the wait ends.
        late=lambda name: copy.deepcopy(self.q if name=='quotes.json' else self.o)
        self.assertFalse(wait_for_publication(late,lambda q,o,at,exp: (at-self.now).total_seconds()>=660 and validate(q,o,at,exp),self.t,now,sleep))
        self.assertLessEqual((clock[0]-self.now).total_seconds(),600)
    def test_stale_published_values_stay_stale_however_long_we_wait(self):
        clock=[self.now+timedelta(seconds=30)]
        def sleep(s): clock[0]+=timedelta(seconds=s)
        old=self.now-timedelta(minutes=30)
        q=copy.deepcopy(self.q);q['generatedAt']=old.isoformat()
        fetch=lambda name: q if name=='quotes.json' else self.o
        self.assertFalse(wait_for_publication(fetch,validate,self.t,lambda: clock[0],sleep))
    def test_unusable_expected_time_fails_closed(self):
        for bad in ['', 'bad', '2026-11-20T14:00:00', None]:
            self.assertFalse(wait_for_publication(lambda n:{},validate,bad,lambda:self.now,lambda s:None))

if __name__=='__main__':unittest.main()
