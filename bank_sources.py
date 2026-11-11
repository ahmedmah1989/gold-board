"""Official bank-page checks. Reject block pages and unknown quote times."""
import re,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

URLS={'nbe':'https://www.nbe.com.eg/NBE/E/#/EN/ExchangeRates','cbe':'https://www.cbe.org.eg/en/economic-research/statistics/exchange-rates'}

class Cells(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=[];self.cell=None
 def handle_starttag(self,tag,attrs):
  if tag=='tr':self.row=[]
  if tag in ('td','th'):self.cell=[]
 def handle_data(self,data):
  if self.cell is not None:self.cell.append(data)
 def handle_endtag(self,tag):
  if tag in ('td','th') and self.cell is not None:self.row.append(' '.join(self.cell).strip());self.cell=None
  if tag=='tr' and self.row:self.rows.append(self.row)

def parse(html,name):
 if 'Request Rejected' in html or 'Access Denied' in html:raise ValueError('blocked')
 p=Cells();p.feed(html);rows=[r for r in p.rows if r and re.search(r'US Dollar|الدولار الأمريكي',r[0],re.I)]
 if len(rows)!=1 or len(rows[0])<3:raise ValueError('unrecognized')
 buy,sell=[float(re.sub(r'[^\d.]','',v)) for v in rows[0][1:3]]
 if not 1<buy<=sell<1000:raise ValueError('unrecognized')
 if name=='cbe':
  date=re.search(r'This page was last updated\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',re.sub('<[^>]+>',' ',html))
  if not date:raise ValueError('missing_time')
  # A page-maintenance date does not establish the effective date of this USD row.
  raise ValueError('missing_quote_time')
 raise ValueError('missing_time')

def fetch(name):
 out={'url':URLS[name],'fetchedAt':datetime.now(timezone.utc).isoformat(),'quoteType':'average_market_reference' if name=='cbe' else 'bank_quote'}
 try:
  req=urllib.request.Request(URLS[name],headers={'User-Agent':'GoldBoard/1.0 official public reference check'})
  with urllib.request.urlopen(req,timeout=20) as response:html=response.read().decode('utf-8')
  out.update(parse(html,name),status='available')
 except ValueError as error:
  code=str(error);out.update(status='unavailable',errorCode=code,reason='المصدر الرسمي رفض القراءة الآلية.' if code=='blocked' else 'تعذر توثيق السعر ووقت نشره من الصفحة الرسمية.')
 except Exception:out.update(status='unavailable',errorCode='fetch_failed',reason='تعذر الوصول للمصدر الرسمي؛ لم يُستخدم بديل منسوب إليه.')
 return name,out
