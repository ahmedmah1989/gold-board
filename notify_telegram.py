"""Conditional market alerts. Credentials stay in environment; no configuration is public."""
import hashlib, json, math, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STATE=ROOT/'data/alert-state.json'

def timestamp(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise ValueError('Missing quote timezone')
    return parsed.timestamp()

def observation(snapshot, now=None):
    now=now or datetime.now(timezone.utc).timestamp()
    try:
        s=snapshot['sources']; a,b,g=(s[k] for k in ('isagha','misr','gold'))
        if any(q['status']!='available' for q in (a,b,g)): return None
        times=[timestamp(q['sourceTime']) for q in (a,b,g)]
        if any(now-t>300 or t-now>120 for t in times) or max(times)-min(times)>300:return None
        local24,local21,bank,ounce=a['24']['sell'],a['21']['sell'],b['sell'],g['sell']
        if not all(type(x) in (int,float) and math.isfinite(x) and x>0 for x in (local24,local21,bank,ounce)):return None
        usd=ounce/31.1034768; fair=usd*bank; implied=local24/usd
        return {'local24':local24,'local21':local21,'gap':local24-fair,'gapPct':(local24/fair-1)*100,'fxGap':implied-bank,'fxPct':(implied/bank-1)*100,'implied':implied,'bank':bank,'ounce':ounce,'time':max(times)}
    except (KeyError,TypeError,ValueError):return None

def reasons(previous,current,peaks):
    if not previous:return []
    result=[]
    if abs(current['gap']-previous['gap'])>=75 or abs(current['gapPct']-previous['gapPct'])>=1.5:result.append('تغير فجوة الذهب بلغ 75 جنيهًا أو 1.5 نقطة مئوية')
    if abs(current['fxGap']-previous['fxGap'])>=1 or abs(current['fxPct']-previous['fxPct'])>=2:result.append('تغير فجوة الدولار الضمني بلغ جنيهًا أو نقطتين مئويتين')
    if current['local24']>peaks['24'] or current['local21']>peaks['21']:result.append('قمة جديدة ضمن السجل المرصود منذ تفعيل الخدمة')
    for karat in ('24','21'):
        dd=(peaks[karat]-current['local'+karat])/peaks[karat]*100
        old=previous.get('dd'+karat,0)
        if dd-old>=2:result.append('تعمق الهبوط من القمة المرصودة بنقطتين مئويتين لعيار '+karat)
    return result

def local_observation(snapshot,now=None):
    now=datetime.now(timezone.utc).timestamp() if now is None else now
    try:
        a=snapshot['sources']['isagha'];t=timestamp(a['sourceTime'])
        if a['status']!='available' or not -120<=now-t<=300:return None
        values={k:a[k]['sell'] for k in ('24','21')}
        if not all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in values.values()):return None
        return {'local24':values['24'],'local21':values['21'],'time':t}
    except (KeyError,TypeError,ValueError):return None

def evaluate(state,current,local):
    """Fresh local highs are independent of the stricter multi-source FX comparison."""
    why=[];created=False
    if current:
        previous=state.get('baseline')
        if not previous:state['baseline']=current;created=True
        else:
            if abs(current['gap']-previous['gap'])>=75 or abs(current['gapPct']-previous['gapPct'])>=1.5:why.append('تغير فجوة الذهب بلغ 75 جنيهًا أو 1.5 نقطة مئوية')
            if abs(current['fxGap']-previous['fxGap'])>=1 or abs(current['fxPct']-previous['fxPct'])>=2:why.append('تغير فجوة الدولار الضمني بلغ جنيهًا أو نقطتين مئويتين')
    if local:
        previous=state.get('localBaseline');peaks=state.get('localPeaks')
        if not previous or not peaks:
            state['localBaseline']={**local,'dd24':0,'dd21':0};state['localPeaks']={'24':local['local24'],'21':local['local21']};created=True
        else:
            if any(local['local'+k]>peaks[k] for k in ('24','21')):why.append('قمة محلية جديدة ضمن السجل المرصود منذ تفعيل المراقبة المحلية')
            for k in ('24','21'):
                dd=(peaks[k]-local['local'+k])/peaks[k]*100
                if dd-previous.get('dd'+k,0)>=2:why.append('تعمق الهبوط من القمة المحلية المرصودة بنقطتين مئويتين لعيار '+k)
            state['localPeaks']={k:max(v,local['local'+k]) for k,v in peaks.items()}
    return why,created

def save(value):
    STATE.parent.mkdir(exist_ok=True)
    temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(STATE)

def telegram(token, method, payload):
    req=urllib.request.Request('https://api.telegram.org/bot'+token+'/'+method,
        data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=20) as response:result=json.load(response)
    if result.get('ok') is not True:raise ValueError('Telegram request rejected')
    return result.get('result',{})

def connect(state,token,chat):
    """Verify intended bot and private chat, with one non-market setup receipt."""
    if state.get('connection',{}).get('status')=='confirmed':return True
    if state.get('connection',{}).get('status')=='pending_or_unknown':return False
    try:
        me=telegram(token,'getMe',{})
        if me.get('username','').lower()!='goldmodybot':raise ValueError('Unexpected bot')
        target=telegram(token,'getChat',{'chat_id':chat})
        if target.get('type')!='private' or str(target.get('id'))!=str(chat):raise ValueError('Unexpected chat')
    except Exception:
        state['connection']={'status':'configuration_invalid','checkedAt':datetime.now(timezone.utc).isoformat()}
        save(state);return False
    state['connection']={'status':'pending_or_unknown'};save(state)
    try:
        telegram(token,'sendMessage',{'chat_id':chat,'text':'تم ربط بوت لوحة الذهب بنجاح ✅\nدي رسالة تأكيد إعداد فقط. تنبيهات السوق تُرسل عند تحقق الشروط وتوفر أسعار حديثة ومتزامنة، وليست توصيات شراء.\nhttps://ahmedmah1989.github.io/gold-board/','link_preview_options':{'is_disabled':True}})
        state['connection']={'status':'confirmed','confirmedAt':datetime.now(timezone.utc).isoformat()};save(state);return True
    except Exception:
        # Never automatically repeat a receipt whose delivery is unknown.
        save(state);return False

def main():
    snapshot=json.loads((ROOT/'data/quotes.json').read_text(encoding='utf-8'))
    try:state=json.loads(STATE.read_text(encoding='utf-8'))
    except (FileNotFoundError,ValueError):state={}
    public={'checkedAt':datetime.now(timezone.utc).isoformat(),'enabled':False}
    token,chat=os.environ.get('TELEGRAM_BOT_TOKEN'),os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat:
        public['status']='awaiting_configuration';state['service']=public;save(state);print('Telegram: awaiting repository secrets.');return
    if not connect(state,token,chat):
        public['status']='connection_needs_review';state['service']=public;save(state);print('Telegram: connection needs review. No credentials logged.');return
    public['enabled']=True
    if state.get('delivery',{}).get('status')=='pending_or_unknown':
        public['status']='delivery_needs_review';state['service']=public;save(state);print('Telegram: prior uncertain delivery requires review.');return
    current=observation(snapshot);local=local_observation(snapshot)
    if current is None and local is None:
        public['status']='waiting_for_fresh_synchronized_quotes';state['service']=public;save(state);print('Telegram: no alert; quotes are incomplete or unsynchronized.');return
    why,created=evaluate(state,current,local)
    if not why:
        public['status']='local_monitoring_gap_waiting' if current is None else 'baseline_created' if created else 'no_material_change';state['service']=public;save(state);print('Telegram: references evaluated; no material-change message.');return
    identity=hashlib.sha256(json.dumps({'baseline':state.get('baseline'),'localBaseline':state.get('localBaseline'),'current':current,'local':local,'reasons':why},sort_keys=True).encode()).hexdigest()[:20]
    text='تنبيه لوحة الذهب\n'+'\n'.join('• '+r for r in why)
    if local:text+=f"\nعيار 24: {local['local24']:,.2f} ج\nعيار 21: {local['local21']:,.2f} ج\nوقت آي صاغة UTC: {datetime.fromtimestamp(local['time'],timezone.utc).isoformat()}"
    if current:text+=f"\nالفجوة: {current['gap']:,.2f} ج ({current['gapPct']:.2f}%)\nالدولار الضمني: {current['implied']:.2f} ج\nبنك مصر بيع: {current['bank']:.2f} ج"
    else:text+='\nمقارنة الفجوة والدولار معلقة لعدم حداثة أو تزامن أحد مصادرها؛ هذا تنبيه محلي فقط.'
    text+='\nhttps://ahmedmah1989.github.io/gold-board/\nالمصادر: آي صاغة للمحلي؛ بنك مصر وGold API للمقارنة عند صلاحيتها. تنبيه تغير وليس توصية شراء.'
    state['delivery']={'id':identity,'status':'pending_or_unknown'};state['service']=public;save(state)
    try:
        payload=json.dumps({'chat_id':chat,'text':text,'link_preview_options':{'is_disabled':True}}).encode()
        req=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',data=payload,headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=20) as response:result=json.load(response)
        if result.get('ok') is not True:raise ValueError('Rejected')
        if current:state['baseline']=current
        if local:state['localBaseline']={**local,**{'dd'+k:(v-local['local'+k])/v*100 for k,v in state['localPeaks'].items()}}
        state['delivery']={'id':identity,'status':'sent','sentAt':public['checkedAt']};public['status']='sent';state['service']=public;save(state);print('Telegram: one material-change alert sent.')
    except Exception:
        public['status']='delivery_needs_review';state['service']=public;save(state);print('Telegram: delivery uncertain; inspect bot before retrying. No credential details are logged.')

if __name__=='__main__':main()
