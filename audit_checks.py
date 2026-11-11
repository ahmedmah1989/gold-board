"""Inspectable arithmetic and coverage receipt. Manual price sample is explicitly dated."""
import json
from decimal import Decimal,getcontext
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Read directly from Investing's public XAU/USD historical table on 2026-11-11.
# These are daily ranges, not a guarantee of identical provider timestamps or upstream independence.
SAMPLE=[('2026-11-10',4031.33,4013.64,4146.94),('2026-11-09',4139.84,4054.04,4148.95),('2026-11-06',4066.63,4029.95,4107.50),('2026-11-05',4087.71,4057.82,4147.02),('2026-11-04',4060.02,3919.65,4070.66)]
def main():
 q=json.loads((ROOT/'data/quotes.json').read_text(encoding='utf-8'))
 h=json.loads((ROOT/'data/history.json').read_text(encoding='utf-8'))
 getcontext().prec=28;s=q['sources'];calc={}
 if all(s.get(k,{}).get('status')=='available' for k in ('gold','misr','isagha')):
  oz=Decimal(str(s['gold']['sell']));fx=Decimal(str(s['misr']['sell']));local=Decimal(str(s['isagha']['24']['sell']))
  usd=oz/Decimal('31.1034768');fair=usd*fx
  calc={k:float(v) for k,v in {'gramUSD':usd,'globalEGP':fair,'gapEGP':local-fair,'gapUSD':(local-fair)/fx,'gapPercent':(local/fair-1)*100,'implied':local/usd,'fxGap':local/usd-fx,'fxPercent':(local/usd/fx-1)*100}.items()}
 points={p['d']:p for p in h['points']};matches=[]
 for d,close,lo,hi in SAMPLE:
  p=points.get(d)
  matches.append({'date':d,'referenceUSD':p['usd'] if p else None,'investingClose':close,'investingLow':lo,'investingHigh':hi,'withinDailyRange':lo<=p['usd']<=hi if p else None,'deltaFromClosePct':(p['usd']/close-1)*100 if p else None})
 out={'schemaVersion':1,'automatedCheckedAt':datetime.now(timezone.utc).isoformat(),'quoteSnapshotTime':q['generatedAt'],
      'arithmetic':{'method':'Python Decimal with original input prices; frontend independently checked in Node tests','values':calc,'note':'Arithmetic only; snapshot timestamps must be assessed separately. Values are retained at quoteSnapshotTime, not live prices.'},
      'historyProfile':h['profile'],'manualSample':{'reviewDate':'2026-11-11','source':'https://www.investing.com/currencies/xau-usd-historical-data','comparison':'Daily reference versus same-date displayed range; provider time boundaries may differ. Not a closing-price reconciliation or full-series verification.','records':matches},
      'sourceFindings':{'nbe':'Public page returned a script-rendered shell without a timestamped USD quote.','cbe':'Official page rejected automated request. Page-maintenance date is never used as USD quote time.','gold':'updatedAt is provider upstream-fetch time, per official documentation; not exchange tick time.'}}
 (ROOT/'data/audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Audit receipt refreshed; manual sample remains dated 2026-11-11.')
if __name__=='__main__':main()
