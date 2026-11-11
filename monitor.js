(function () {
  'use strict';
  const OUNCE = 31.1034768;
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
    const times = quotes.map(q => Date.parse(q?.sourceTime));
    if (quotes.some(q => q?.status !== 'available') || times.some(t => !Number.isFinite(t))) return {usable:false, fresh:false, reason:'مصدر أو وقت تسعير غير متاح؛ ستُستكمل المقارنة تلقائيًا عند وصوله.'};
    if (![sources.isagha?.['24']?.sell,sources.isagha?.['21']?.sell,sources.misr?.sell,sources.gold?.sell].every(v=>Number.isFinite(v)&&v>0)) return {usable:false,fresh:false,reason:'إحدى قيم الأسعار غير صالحة؛ المقارنة معلقة.'};
    if (times.some(t => t > now + 120000)) return {usable:false, fresh:false, reason:'توقيت أحد المصادر في المستقبل؛ المقارنة معلقة لحين التحقق.'};
    if (times.some(t => now-t > 24*3600000)) return {usable:false, fresh:false, reason:'إحدى القراءات تجاوزت 24 ساعة؛ المقارنة معلقة حتى يصل سعر أحدث.'};
    const fresh = times.every(t => now-t <= 300000) && Math.max(...times)-Math.min(...times) <= 300000;
    return {usable:true, fresh, reason:fresh ? 'أوقات المصادر حديثة ومتقاربة. الحساب قبل رسوم المنتج النهائي.' : 'حساب استرشادي من آخر أسعار منشورة؛ أوقات المصادر مختلفة أو تجاوز أحدها 5 دقائق. راجع الأوقات أدناه؛ ليست إشارة لحظية.'};
  }
  if (typeof module !== 'undefined') module.exports = {calculate, OUNCE, assess};
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const state = {sources:{}, generatedAt:null, lastCheck:null, busy:false, dealerEdited:false};
  const number = v => { const s=String(v).replace(/[٠-٩]/g,d=>'٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/[٬,\s]/g,'').replace(/٫/g,'.'); return /^\d+(\.\d+)?$/.test(s)?Number(s):NaN; };
  const positive = v => Number.isFinite(v) && v>0;
  const fmt = (v,unit=' جنيه') => Number.isFinite(v)?v.toLocaleString('ar-EG',{maximumFractionDigits:2})+unit:'—';
  const time = v => Number.isFinite(Date.parse(v))?new Date(v).toLocaleString('ar-EG',{timeZone:'Africa/Cairo',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}):'غير متاح';
  function usable(q) {const t=Date.parse(q?.sourceTime);return q?.status==='available' && Number.isFinite(t) && t<=Date.now()+120000 && Date.now()-t<=86400000;}
  function calculator() {
    const budget=number($('budget').value), price=number($('dealer').value);
    $('grams').textContent=positive(budget)&&positive(price)?fmt(budget/price,' جرام'):'—';
    $('calculatorNote').textContent=state.dealerEdited?'الحساب بسعر التاجر الذي أدخلته؛ لا يشمل المصنعية.':'السعر من آخر قراءة آي صاغة؛ لا يشمل المصنعية.';
  }
  function row(label,q,buy,sell,unit) {
    const tr=document.createElement('tr');
    [label,fmt(buy,unit),fmt(sell,unit),time(q?.sourceTime),time(q?.fetchedAt)].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.appendChild(td)});
    return tr;
  }
  function render() {
    const a=state.sources.isagha,b=state.sources.misr,g=state.sources.gold;
    $('price24').textContent=usable(a)?fmt(a['24'].sell):'غير متاح';
    $('price21').textContent=usable(a)?fmt(a['21'].sell):'غير متاح';
    $('priceBank').textContent=usable(b)?fmt(b.sell):'غير متاح';
    $('priceOunce').textContent=usable(g)?fmt(g.sell,' دولار'):'غير متاح';
    $('time24').textContent=$('time21').textContent='آي صاغة • وقت المصدر '+time(a?.sourceTime);
    $('timeBank').textContent='بنك مصر • وقت المصدر '+time(b?.sourceTime);
    $('timeOunce').textContent=(g?.name||'gold-api.com')+' • وقت المصدر '+time(g?.sourceTime);
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
    table.append(row('آي صاغة • عيار 24',a,a?.['24']?.buy,a?.['24']?.sell,' جنيه'),row('آي صاغة • عيار 21',a,a?.['21']?.buy,a?.['21']?.sell,' جنيه'),row('بنك مصر • دولار نقدي',b,b?.buy,b?.sell,' جنيه'),row(g?.name||'gold-api.com • أونصة',g,g?.buy,g?.sell,' دولار'));
    if (!state.dealerEdited) $('dealer').value=usable(a)?a['21'].sell:'';
    calculator();
  }
  async function json(url) {
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),15000);
    try {const r=await fetch(url,{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json();}finally{clearTimeout(timer);}
  }
  async function refresh() {
    if(state.busy)return;
    state.busy=true;$('refresh').disabled=true;render();
    const [snapshot,global]=await Promise.allSettled([json('data/quotes.json?t='+Date.now()),json('https://api.gold-api.com/price/XAU')]);
    const previousGold=state.sources.gold;
    if(snapshot.status==='fulfilled'&&snapshot.value.schemaVersion===1) {
      state.sources=snapshot.value.sources||{};state.generatedAt=snapshot.value.generatedAt;
    } else {
      // Keep visible previous values and their real timestamps, never relabel as new.
      state.sources={...state.sources};
    }
    if(!state.sources.gold&&previousGold)state.sources.gold=previousGold;
    if(global.status==='fulfilled'&&positive(Number(global.value.price))&&Number.isFinite(Date.parse(global.value.updatedAt))) {
      state.sources.gold={status:'available',sell:Number(global.value.price),sourceTime:global.value.updatedAt,fetchedAt:new Date().toISOString(),name:'gold-api.com'};
    }
    state.lastCheck=new Date().toISOString();state.busy=false;$('refresh').disabled=false;render();
    if(snapshot.status==='rejected') $('fetchStatus').textContent+=' • تعذر جلب لقطة أحدث؛ المعروض يحتفظ بتوقيته الأصلي.';
  }
  $('refresh').addEventListener('click',refresh);
  $('budget').addEventListener('input',calculator);
  $('dealer').addEventListener('input',()=>{state.dealerEdited=true;calculator();});
  setInterval(refresh,60000);refresh();
})();
