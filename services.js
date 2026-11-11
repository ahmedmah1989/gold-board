(function(){
 'use strict';
 const $=id=>document.getElementById(id);
 const f=v=>Number.isFinite(v)?v.toLocaleString('ar-EG',{maximumFractionDigits:2})+' جنيه':'غير متاح';
 const t=v=>Number.isFinite(Date.parse(v))?new Date(v).toLocaleString('ar-EG',{timeZone:'Africa/Cairo'}):'غير منشور';
 function validOffer(o,now=Date.now()){
  const stamp=Date.parse(o.sourceTime);
  return o.status==='observed'&&o.inStock===true&&[o.manufacturingIncluded,o.taxIncluded,o.stampIncluded].every(x=>x===true)&&Number.isFinite(o.listedPrice)&&o.listedPrice>0&&Number.isFinite(stamp)&&now-stamp<=300000&&stamp-now<=120000;
 }
 if(typeof module!=='undefined')module.exports={validOffer};
 if(typeof document==='undefined')return;
 async function load(path){const c=new AbortController(),timer=setTimeout(()=>c.abort(),15000);try{const r=await fetch(path+'?t='+Date.now(),{cache:'no-store',signal:c.signal});if(!r.ok)throw Error();return await r.json();}finally{clearTimeout(timer);}}
 function offers(data){
  const rows=$('offerRows');rows.replaceChildren();
  const active=(data.offers||[]).filter(o=>validOffer(o));
  $('offersStatus').textContent='متاجر مستوفية للشروط الآن: '+new Set(active.map(x=>x.store)).size+' • آخر فحص '+t(data.checkedAt)+'. لا يظهر ترتيب الأرخص إلا للعروض النهائية الموثقة والمتزامنة لنفس الوزن.';
  (data.offers||[]).forEach(o=>{
   const tr=document.createElement('tr');
   const fees=[['المصنعية',o.manufacturingIncluded],['الضريبة',o.taxIncluded],['الدمغة',o.stampIncluded]].map(([n,v])=>n+': '+(v===true?'مشمولة':v===false?'غير مشمولة':'غير مؤكدة')).join(' • ');
   const stock=o.inStock===true?'متاح':o.inStock===false?'غير متوفر':'التوافر غير مؤكد';
   const values=[o.store,(o.weight===8?'جنيه 8 جم • '+o.brand:'نصف جنيه 4 جم • '+o.brand)+' • '+stock,o.status==='observed'?f(o.listedPrice):'غير متاح',fees,t(o.sourceTime),t(o.checkedAt),validOffer(o)?'صالح للمقارنة':o.reason||'غير مؤهل للمقارنة'];
   values.forEach((v,i)=>{const td=document.createElement('td');if(i===0){const a=document.createElement('a');a.href=o.url;a.target='_blank';a.rel='noopener';a.textContent=v+' ↗';td.append(a);}else td.textContent=v;tr.append(td);});rows.append(tr);
  });
 }
 function telegram(data){
  const status=data.service?.status,checked=Date.parse(data.service?.checkedAt),recent=Number.isFinite(checked)&&Date.now()-checked<=30*60000;
  const names={awaiting_configuration:'المفاتيح غير موصولة',connection_needs_review:'الربط يحتاج مراجعة',waiting_for_fresh_synchronized_quotes:'الربط جاهز؛ تنبيهات السوق تنتظر أسعارًا حديثة ومتزامنة',baseline_created:'الربط جاهز وتم إنشاء مرجع صامت للمقارنة',no_material_change:'لم يتحقق تغير مهم يستدعي رسالة',sent:'أُرسل تنبيه لتغير مهم',delivery_needs_review:'نتيجة إرسال سابق تحتاج مراجعة قبل إعادة المحاولة'};
  $('telegramStatus').textContent=(recent?'':'حالة محفوظة؛ لم يصل فحص خلال آخر 30 دقيقة. ')+(names[status]||'الحالة لم تصل بعد')+' • آخر فحص '+t(data.service?.checkedAt);
  $('telegramConnection').textContent=data.connection?.status==='confirmed'?'Telegram أكد إرسال رسالة تأكيد الربط؛ لا يثبت ذلك فتحها أو قراءتها.':'لا يوجد تأكيد موثق لرسالة الربط حتى الآن.';
 }
 async function refresh(){
  const liveAlerts=['127.0.0.1','localhost'].includes(location.hostname)?'https://ahmedmah1989.github.io/gold-board/data/alert-state.json':'data/alert-state.json';
  const r=await Promise.allSettled([load('data/offers.json'),load(liveAlerts),load('data/audit.json')]);
  if(r[0].status==='fulfilled')offers(r[0].value);else $('offersStatus').textContent='تعذر تحميل أحدث فحص للمتاجر؛ لا توجد مقارنة موثقة متاحة.';
  if(r[1].status==='fulfilled')telegram(r[1].value);else $('telegramStatus').textContent='تعذر جلب حالة خدمة التنبيهات؛ لا يمكن تأكيد التشغيل الحالي.';
  if(r[2].status==='fulfilled'){
   const a=r[2].value,s=a.manualSample,records=s.records||[],compared=records.filter(x=>typeof x.withinDailyRange==='boolean');
   $('historyAuditStatus').textContent='مراجعة يدوية بتاريخ '+s.reviewDate+': '+compared.filter(x=>x.withinDailyRange).length+' من '+compared.length+' عينات تقع داخل نطاق اليوم المنشور في Investing. هذا لا يثبت مطابقة سعر الإغلاق أو صحة كامل السلسلة. أيام الأسبوع الناقصة: '+(a.historyProfile.missingWeekdays.join('، ')||'لا توجد في نافذة الفحص')+'.';
  }else $('historyAuditStatus').textContent='تعذر جلب سجل التدقيق. المطابقة التاريخية الشاملة غير مكتملة.';
 }
 refresh();setInterval(refresh,60000);
})();
