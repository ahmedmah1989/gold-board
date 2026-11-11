(function () {
  'use strict';
  const OUNCE = 31.1034768;
  const validTime=v=>typeof v==='string'&&/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(v)&&Number.isFinite(Date.parse(v));
  function calculate(ounce, bankSell, local24, local21) {
    if (![ounce, bankSell, local24].every(x => Number.isFinite(x) && x > 0)) return null;
    const gramUSD = ounce / OUNCE, globalEGP = gramUSD * bankSell;
    return { gramUSD, globalEGP, global21: globalEGP * 21 / 24,
      gapEGP: local24 - globalEGP, gapUSD: (local24 - globalEGP) / bankSell,
      gapPercent: (local24 / globalEGP - 1) * 100,
      implied: local24 / gramUSD, fxGap: local24 / gramUSD - bankSell,
      fxPercent: (local24 / gramUSD / bankSell - 1) * 100,
      drop24: Math.max(0, 7735 - local24), drop21: local21 > 0 ? Math.max(0, 6767 - local21) : null };
  }

  function assess(sources, now = Date.now()) {
    const quotes = [sources?.isagha, sources?.misr, sources?.gold];
    const times = quotes.map(q => validTime(q?.sourceTime)?Date.parse(q.sourceTime):NaN);
    if (quotes.some(q => q?.status !== 'available') || times.some(t => !Number.isFinite(t))) return {usable:false, fresh:false, reason:'مصدر أو وقت تسعير غير متاح؛ ستُستكمل المقارنة تلقائيًا عند وصوله.'};
    if (![sources.isagha?.['24']?.sell,sources.isagha?.['21']?.sell,sources.misr?.sell,sources.gold?.sell].every(v=>Number.isFinite(v)&&v>0)) return {usable:false,fresh:false,reason:'إحدى قيم الأسعار غير صالحة؛ المقارنة معلقة.'};
    if (times.some(t => t > now + 120000)) return {usable:false, fresh:false, reason:'توقيت أحد المصادر في المستقبل؛ المقارنة معلقة لحين التحقق.'};
    if (times.some(t => now-t > 24*3600000)) return {usable:false, fresh:false, reason:'إحدى القراءات تجاوزت 24 ساعة؛ المقارنة معلقة حتى يصل سعر أحدث.'};
    const fresh = times.every(t => now-t <= 300000) && Math.max(...times)-Math.min(...times) <= 300000;
    return {usable:true, fresh, reason:fresh ? 'أوقات المصادر حديثة ومتقاربة. الحساب قبل رسوم المنتج النهائي.' : 'حساب استرشادي من آخر أسعار منشورة؛ أوقات المصادر مختلفة أو تجاوز أحدها 5 دقائق. راجع الأوقات أدناه؛ ليست إشارة لحظية.'};
  }
  function quoteUsable(q,now=Date.now()) {const t=validTime(q?.sourceTime)?Date.parse(q.sourceTime):NaN;return q?.status==='available' && Number.isFinite(t) && t<=now+120000 && now-t<=86400000;}
  if (typeof module !== 'undefined') module.exports = {calculate, OUNCE, assess,quoteUsable};
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const state = {sources:{}, generatedAt:null, lastCheck:null, busy:false, dealerEdited:false};
  const number = v => { const s=String(v).replace(/[٠-٩]/g,d=>'٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/[٬,\s]/g,'').replace(/٫/g,'.'); return /^\d+(\.\d+)?$/.test(s)?Number(s):NaN; };
  const positive = v => Number.isFinite(v) && v>0;
  const fmt = (v,unit=' جنيه') => Number.isFinite(v)?v.toLocaleString('ar-EG',{maximumFractionDigits:2})+unit:'—';
  const time = v => Number.isFinite(Date.parse(v))?new Date(v).toLocaleString('ar-EG',{timeZone:'Africa/Cairo',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}):'غير متاح';
  const usable=quoteUsable;
  function cardPrice(id,quote,value,unit){const element=$(id);element.replaceChildren();if(!usable(quote)||!positive(value)){element.textContent='غير متاح';return;}element.appendChild(document.createTextNode(fmt(value,'')));const small=document.createElement('small');small.className='price-unit';small.textContent=unit;element.appendChild(small);}
  function calculator() {
    const budget=number($('budget').value), price=number($('dealer').value);
    $('grams').textContent=positive(budget)&&positive(price)?fmt(budget/price,' جرام'):'—';
    $('calculatorNote').textContent=state.dealerEdited?'الحساب بسعر التاجر الذي أدخلته؛ لا يشمل المصنعية.':'السعر من آخر قراءة آي صاغة؛ لا يشمل المصنعية.';
  }
  function row(label,q,buy,sell,unit,url) {
    const tr=document.createElement('tr');
    [label,usable(q)?fmt(buy,unit):'—',usable(q)?fmt(sell,unit):'—',time(q?.sourceTime),time(q?.fetchedAt),usable(q)?(Date.now()-Date.parse(q.sourceTime)<=300000?'قراءة حديثة':'آخر سعر منشور • أقدم من 5 دقائق'):(q?.reason||'بيانات غير متاحة أو أقدم من 24 ساعة')].forEach((value,i)=>{const td=document.createElement('td');if(i===0&&url){const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener';link.textContent=value+' ↗';td.appendChild(link);}else td.textContent=value;tr.appendChild(td)});
    return tr;
  }
  function render() {
    const a=state.sources.isagha,b=state.sources.misr,g=state.sources.gold;
    cardPrice('price24',a,a?.['24']?.sell,'جنيه / جرام');
    cardPrice('price21',a,a?.['21']?.sell,'جنيه / جرام');
    cardPrice('priceBank',b,b?.sell,'جنيه / دولار');
    cardPrice('priceOunce',g,g?.sell,'دولار / أونصة');
    $('time24').textContent=$('time21').textContent='آي صاغة • وقت المصدر '+time(a?.sourceTime);
    $('timeBank').textContent='بنك مصر • وقت المصدر '+time(b?.sourceTime);
    $('timeOunce').textContent=(g?.name||'gold-api.com')+' • آخر جلب لدى المزود '+time(g?.sourceTime);
    const quality=assess(state.sources);
    const result=quality.usable?calculate(g.sell,b.sell,a['24'].sell,a['21'].sell):null;
    const map={gapEGP:[result?.gapEGP],gapPercent:[result?.gapPercent,'%'],gapUSD:[result?.gapUSD,' دولار'],implied:[result?.implied],fxGap:[result?.fxGap],fxPercent:[result?.fxPercent,'%'],global24:[result?.globalEGP],global21:[result?.global21]};
    Object.entries(map).forEach(([id,args])=>$(id).textContent=fmt(...args));
    $('gapMeaning').textContent=result?(result.gapEGP>=0?'علاوة محلية فوق القيمة العالمية':'خصم محلي عن القيمة العالمية'):'انتظار بيانات صالحة للمقارنة — لا يلزم إدخال أسعار.';
    $('qualityBadge').textContent=result?(quality.fresh?'مقارنة حديثة ومتزامنة':'مقارنة استرشادية • آخر أسعار منشورة'):'المقارنة معلقة';
    $('qualityBadge').className='badge'+(result&&quality.fresh?' good':'');
    $('qualityText').textContent=quality.reason;
    $('collectedAt').textContent='جمع الأسعار المحلية والبنك: '+time(state.generatedAt);
    $('fetchStatus').textContent=state.busy?'جاري فحص المصادر…':state.lastCheck?'آخر فحص للصفحة: '+time(state.lastCheck):'تحميل الأسعار…';
    const table=$('sourceRows'); table.replaceChildren();
    table.append(row('آي صاغة • عيار 24',a,a?.['24']?.buy,a?.['24']?.sell,' جنيه','https://market.isagha.com/prices'),row('آي صاغة • عيار 21',a,a?.['21']?.buy,a?.['21']?.sell,' جنيه','https://market.isagha.com/prices'),row('بنك مصر • دولار نقدي',b,b?.buy,b?.sell,' جنيه','https://www.banquemisr.com/CAPITAL-MARKETS/Exchange-Rates-and-Currencies'),row(g?.name||'gold-api.com • أونصة',g,g?.buy,g?.sell,' دولار','https://api.gold-api.com/price/XAU'));
    ['nbe','cbe'].forEach(key=>{const q=state.sources[key];table.append(row(key==='nbe'?'البنك الأهلي • دولار':'البنك المركزي • مرجع السوق',q,q?.buy,q?.sell,' جنيه',q?.url||(key==='nbe'?'https://www.nbe.com.eg/NBE/E/#/EN/ExchangeRates':'https://www.cbe.org.eg/en/economic-research/statistics/exchange-rates')));});
    if (!state.dealerEdited) $('dealer').value=usable(a)?a['21'].sell:'';
    calculator();
    if($('reference24'))$('reference24').textContent=result?fmt(result.drop24)+' ('+fmt(result.drop24/7735*100,'%')+')':'—';
    if($('reference21'))$('reference21').textContent=result?fmt(result.drop21)+' ('+fmt(result.drop21/6767*100,'%')+')':'—';
    window.dispatchEvent(new CustomEvent('gold-board-updated',{detail:{sources:state.sources,quality,result}}));
  }
  async function json(url) {
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),15000);
    try {const r=await fetch(url,{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json();}finally{clearTimeout(timer);}
  }
  async function refresh() {
    if(state.busy)return;
    state.busy=true;$('refresh').disabled=true;render();
    const quotesURL=['127.0.0.1','localhost'].includes(location.hostname)?'https://ahmedmah1989.github.io/gold-board/data/quotes.json':'data/quotes.json';
    const [snapshot,global]=await Promise.allSettled([json(quotesURL+'?t='+Date.now()),json('https://api.gold-api.com/price/XAU')]);
    const previousGold=state.sources.gold;
    if(snapshot.status==='fulfilled'&&snapshot.value.schemaVersion===1) {
      state.sources=snapshot.value.sources||{};state.generatedAt=snapshot.value.generatedAt;
    } else {
      // Keep visible previous values and their real timestamps, never relabel as new.
      state.sources={...state.sources};
    }
    if(!state.sources.gold&&previousGold)state.sources.gold=previousGold;
    if(global.status==='fulfilled'&&global.value.symbol==='XAU'&&(!global.value.currency||global.value.currency==='USD')&&positive(Number(global.value.price))&&Number.isFinite(Date.parse(global.value.updatedAt))) {
      state.sources.gold={status:'available',sell:Number(global.value.price),sourceTime:global.value.updatedAt,fetchedAt:new Date().toISOString(),name:'gold-api.com',sourceTimeKind:'provider_upstream_fetch'};
    }
    state.lastCheck=new Date().toISOString();state.busy=false;$('refresh').disabled=false;render();
    if(snapshot.status==='rejected') $('fetchStatus').textContent+=' • تعذر جلب لقطة أحدث؛ المعروض يحتفظ بتوقيته الأصلي.';
  }
  $('refresh').addEventListener('click',refresh);
  $('budget').addEventListener('input',calculator);
  $('dealer').addEventListener('input',()=>{state.dealerEdited=true;calculator();});
  setInterval(refresh,60000);refresh();
})();
