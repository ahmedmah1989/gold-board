"""Cached daily references; validates dates and coverage, never labels them exchange closes."""
import json,math,urllib.request,sys
from datetime import datetime,timedelta,timezone,date
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE='https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@'

def parse_day(raw,day):
 if raw.get('date')!=day:raise ValueError('Reference date mismatch')
 usd,egp=raw['xau']['usd'],raw['xau']['egp']
 if not all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in (usd,egp)):raise ValueError('Invalid reference values')
 if not 100<usd<100000 or not 1<egp/usd<1000:raise ValueError('Invalid reference units')
 return {'d':day,'usd':usd,'egp':egp}

def profile(points,end):
 start=end-timedelta(days=372)
 expected={ (start+timedelta(days=i)).isoformat() for i in range(373) if (start+timedelta(days=i)).weekday()<5}
 dates={p['d'] for p in points if p['d'] in expected}
 ordered=sorted(dates)
 return {'expectedWeekdays':len(expected),'availableWeekdays':len(dates),'missingWeekdays':sorted(expected-dates),
         'lastReferenceDate':ordered[-1] if ordered else None,'maxCalendarGap':max([(date.fromisoformat(b)-date.fromisoformat(a)).days for a,b in zip(ordered,ordered[1:])],default=0),
         'calendar':'Weekdays only; exchange holidays not independently reconciled'}

def main():
 path=ROOT/'data/history.json';today=datetime.now(timezone.utc).date();end=today-timedelta(days=1)
 try:old=json.loads(path.read_text(encoding='utf-8'))
 except (FileNotFoundError,ValueError):old={}
 if old.get('checkedDate')==today.isoformat() and '--force' not in sys.argv:print('History: cached daily check.');return
 wanted={(end-timedelta(days=i)).isoformat() for i in list(range(373))+[730,731,732,733]}
 known={p['d']:p for p in old.get('points',[]) if p.get('d') in wanted}
 # Revalidate recent files; backfill missing dates once a day, never every visitor/minute.
 todo=sorted(d for d in wanted if d not in known or (end-date.fromisoformat(d)).days<3)
 def fetch(day):
  for url in [BASE+day+'/v1/currencies/xau.json','https://'+day+'.currency-api.pages.dev/v1/currencies/xau.json']:
   try:
    req=urllib.request.Request(url,headers={'User-Agent':'GoldBoard/1.0 daily reference cache'})
    with urllib.request.urlopen(req,timeout=12) as r:raw=json.load(r)
    return day,{**parse_day(raw,day),'url':url}
   except Exception:continue
  return day,None
 with ThreadPoolExecutor(max_workers=6) as pool:
  for day,point in pool.map(fetch,todo):
   if point:known[day]=point
 points=sorted(known.values(),key=lambda p:p['d'])
 out={'schemaVersion':1,'checkedDate':today.isoformat(),'checkedAt':datetime.now(timezone.utc).isoformat(),'source':BASE+'{date}/v1/currencies/xau.json',
      'fallbackSource':'https://{date}.currency-api.pages.dev/v1/currencies/xau.json','kind':'daily_reference_not_exchange_close','independentVerification':'partial_manual_sample_only','profile':profile(points,end),'points':points}
 path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('History:',len(points),'daily references;',len(out['profile']['missingWeekdays']),'missing weekdays.')
if __name__=='__main__':main()
