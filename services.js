(function(){
 'use strict';
 const $=id=>document.getElementById(id);
 const f=v=>Number.isFinite(v)?v.toLocaleString('ar-EG',{maximumFractionDigits:2})+' جنيه':'غير متاح';
 const t=v=>Number.isFinite(Date.parse(v))?new Date(v).toLocaleString('ar-EG',{timeZone:'Africa/Cairo'}):'غير منشور';
 function validOffer(o,now=Date.now()){
  const stamp=Date.parse(o.sourceTime);
  return o.status==='observed'&&o.identityVerified===true&&o.inStock===true&&[o.manufacturingIncluded,o.taxIncluded,o.stampIncluded].every(x=>x===true)&&Number.isFinite(o.listedPrice)&&o.listedPrice>0&&typeof o.sourceTime==='string'&&/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(o.sourceTime)&&Number.isFinite(stamp)&&now-stamp<=300000&&stamp-now<=120000;
 }
 function displayable(o,now=Date.now()){
  const checked=Date.parse(o.checkedAt);
  return o.status==='observed'&&o.identityVerified===true&&Number.isFinite(o.listedPrice)&&o.listedPrice>0&&Number.isFinite(checked)&&now-checked<=86400000&&checked-now<=120000;
 }
 function productRows(data,id){return (data.offers||[]).filter(o=>o.productId===id);}
 if(typeof module!=='undefined')module.exports={validOffer,displayable,productRows};
 if(typeof document==='undefined')return;
 let catalogData=null,selected='pound';
 const element=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
 const weight=c=>c.kind==='ounce'?'أونصة ترويسية ≈ 31.1035 جرام':c.weight+' جرام';
 const stock=o=>o.inStock===true?'متاح حسب المصدر':o.inStock===false?'غير متوفر حسب المصدر':'التوافر غير مؤكد';
 async function load(path){const c=new AbortController(),timer=setTimeout(()=>c.abort(),15000);try{const r=await fetch(path+'?t='+Date.now(),{cache:'no-store',signal:c.signal});if(!r.ok)throw Error();return await r.json();}finally{clearTimeout(timer);}}
 function renderProduct(){
  if(!catalogData)return;
  const data=catalogData,c=data.catalog.find(c=>c.id===selected)||data.catalog.find(c=>c.id==='pound');selected=c.id;
  $('selectedProductName').textContent=c.name;
  $('selectedProductSpec').textContent=weight(c)+' • عيار '+c.karat+(c.kind==='ounce'?' • سعر منتج فعلي بالجنيه، مستقل عن سعر الأونصة العالمي بالدولار':'');
  document.querySelectorAll('[data-product-kind]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.productKind===c.kind)));
  $('barWeightControl').hidden=c.kind!=='bars';if(c.kind==='bars')$('barWeight').value=c.id;
  $('productPermalink').href='#products/'+c.id;
  const selectedRows=productRows(data,c.id),active=selectedRows.filter(o=>validOffer(o));
  $('offersStatus').textContent='العروض المنشورة لهذا المنتج: '+selectedRows.filter(o=>displayable(o)).length+' • المتاجر المستوفية للمقارنة النهائية: '+new Set(active.map(o=>o.store)).size+' • آخر فحص '+t(data.checkedAt);
  const cards=$('productOfferCards');cards.replaceChildren();
  selectedRows.forEach(o=>{
   const card=element('article','retail-card'),show=displayable(o);
   card.append(element('div','source-type',o.brand+' • '+stock(o)),element('h3','',o.store),element('p','retail-price',show?f(o.listedPrice):o.contentWarning?'السعر يحتاج مراجعة':'السعر غير متاح'));
   card.append(element('span','badge'+(validOffer(o)?' good':''),!show?'بيانات السعر غير معتمدة':validOffer(o)?'عرض مؤهل للمقارنة':'سعر منشور؛ التكلفة النهائية غير مؤكدة'));
   const facts=element('dl','retail-facts');
   const lines=[['المنتج',weight(c)+' • عيار '+c.karat],['المصنعية والضريبة',Number.isFinite(o.makingAndVAT)?f(o.makingAndVAT)+' ضمن الإجمالي المعلن':Number.isFinite(o.declaredMakingCharge)?'مصنعية معلنة '+f(o.declaredMakingCharge)+'؛ شمولها والضريبة في السعر غير مؤكد':o.manufacturingIncluded===true&&o.taxIncluded===true?'مشمولة وفق المصدر':'شمولها في السعر غير مؤكد'],['الدمغة والشحن','الدمغة: '+(o.stampIncluded===true?'مشمولة':'غير مؤكدة')+' • الشحن: '+(o.shippingIncluded===true?'مشمول':'غير مؤكد')],['وقت تسعير المنتج',t(o.sourceTime)],['آخر رصد للصفحة',t(o.checkedAt)]];
   lines.forEach(([label,value])=>{const item=element('div');item.append(element('dt','',label),element('dd','',value));facts.append(item);});card.append(facts);
   if(o.contentWarning)card.append(element('p','notice',o.contentWarning));
   if(show&&Date.now()-Date.parse(o.checkedAt)>300000)card.append(element('p','notice','آخر رصد أقدم من خمس دقائق؛ راجع السعر الحالي لدى المصدر.'));
   if(Number.isFinite(o.buybackPrice)){const details=element('details');details.append(element('summary','','إعادة الشراء المنشورة لدى المتجر'),element('p','','السعر المنشور لإعادة شراء هذا المنتج: '+f(o.buybackPrice)+'. شروط التغليف والفحص والسعر النهائي يحددها المتجر؛ هذا ليس عرض بيع مضمونًا.'));card.append(details);}
   const link=element('a','source-button','افتح صفحة المنتج والسعر ↗');link.href=o.url;link.target='_blank';link.rel='noopener';card.append(link);cards.append(card);
  });
  if(!selectedRows.length)cards.append(element('p','notice','لم تصل صفحة منتج موثقة لهذا الاختيار بعد.'));
  const rows=$('offerRows');rows.replaceChildren();
  selectedRows.forEach(o=>{
   const tr=document.createElement('tr');
   const fees=[['المصنعية',o.manufacturingIncluded],['الضريبة',o.taxIncluded],['الدمغة',o.stampIncluded]].map(([n,v])=>n+': '+(v===true?'مشمولة':v===false?'غير مشمولة':'غير مؤكدة')).join(' • ');
   const values=[o.store,c.name+' • '+o.brand+' • '+stock(o),displayable(o)?f(o.listedPrice):'غير متاح للاعتماد',fees,t(o.sourceTime),t(o.checkedAt),validOffer(o)?'صالح للمقارنة':o.reason||'غير مؤهل للمقارنة'];
   values.forEach((v,i)=>{const td=document.createElement('td');if(i===0){const a=document.createElement('a');a.href=o.url;a.target='_blank';a.rel='noopener';a.textContent=v+' ↗';td.append(a);}else td.textContent=v;tr.append(td);});rows.append(tr);
  });
 }
 function offers(data){
  if(data.schemaVersion!==2||!Array.isArray(data.catalog)||!data.catalog.length)throw Error('Missing product catalog');
  catalogData=data;
  const weights=$('barWeight');weights.replaceChildren();data.catalog.filter(c=>c.kind==='bars').forEach(c=>{const o=element('option','',c.weight+' جرام • عيار '+c.karat);o.value=c.id;weights.append(o);});
  weights.value='bar10';
  const summary=$('productSummary');summary.replaceChildren();
  ['quarter','half','pound','bar10','ounce'].forEach(id=>{
   const c=data.catalog.find(p=>p.id===id);if(!c)return;
   const representative=productRows(data,id).find(o=>displayable(o));
   const link=element('a','product-summary-card');link.href='#products/'+id;
   link.append(element('span','label',c.name),element('strong','summary-price',representative?f(representative.listedPrice):'غير متاح'),element('span','small',weight(c)+' • عيار '+c.karat),element('span','small',representative?'عرض منشور من '+representative.store:'انتظار عرض موثق'));
   if(representative)link.append(element('span','small','رصد الصفحة: '+t(representative.checkedAt)));
   link.append(element('span','summary-action','المتاجر وتفاصيل السعر ←'));
   link.addEventListener('click',()=>requestAnimationFrame(()=>window.scrollTo({top:document.querySelector('nav').offsetTop,behavior:'smooth'})));summary.append(link);
  });
  route();
 }
 function choose(id){if(catalogData?.catalog.some(c=>c.id===id)){selected=id;location.hash='products/'+id;renderProduct();}}
 function route(){const [panel,id]=location.hash.slice(1).split('/');if(panel==='products'&&catalogData?.catalog.some(c=>c.id===id))selected=id;renderProduct();}
 document.querySelectorAll('[data-product-kind]').forEach(b=>b.addEventListener('click',()=>choose(b.dataset.productKind==='bars'?$('barWeight').value||'bar10':b.dataset.productKind)));
 $('barWeight').addEventListener('change',()=>choose($('barWeight').value));
 window.addEventListener('hashchange',route);
 function telegram(data){
  const status=data.service?.status,checked=Date.parse(data.service?.checkedAt),recent=Number.isFinite(checked)&&Date.now()-checked<=30*60000;
  const names={awaiting_configuration:'المفاتيح غير موصولة',connection_needs_review:'الربط يحتاج مراجعة',waiting_for_fresh_synchronized_quotes:'انتظار أسعار محلية حديثة ومصادر صالحة للمقارنة',local_monitoring_gap_waiting:'مراقبة القمم والهبوط المحلي جاهزة؛ تنبيهات الفجوة تنتظر مصادر حديثة ومتزامنة',baseline_created:'الربط جاهز وتم إنشاء مرجع صامت للمقارنة',no_material_change:'لم يتحقق تغير مهم يستدعي رسالة',sent:'أُرسل تنبيه لتغير مهم',delivery_needs_review:'نتيجة إرسال سابق تحتاج مراجعة قبل إعادة المحاولة'};
  $('telegramStatus').textContent=(recent?'':'حالة محفوظة؛ لم يصل فحص خلال آخر 30 دقيقة. ')+(names[status]||'الحالة لم تصل بعد')+' • آخر فحص '+t(data.service?.checkedAt);
  $('telegramConnection').textContent=data.connection?.status==='confirmed'?'Telegram أكد إرسال رسالة تأكيد الربط؛ لا يثبت ذلك فتحها أو قراءتها.':'لا يوجد تأكيد موثق لرسالة الربط حتى الآن.';
 }
 function catalogError(message){
  if(catalogData){offers(catalogData);$('offersStatus').textContent=message+' المعروض يحتفظ بأوقات رصده الأصلية.';}
  else{$('offersStatus').textContent=message;$('productSummary').replaceChildren(element('p','notice',message));}
 }
 async function refresh(){
  const liveAlerts=['127.0.0.1','localhost'].includes(location.hostname)?'https://ahmedmah1989.github.io/gold-board/data/alert-state.json':'data/alert-state.json';
  const r=await Promise.allSettled([load('data/offers.json'),load(liveAlerts),load('data/audit.json')]);
  if(r[0].status==='fulfilled'){try{offers(r[0].value);}catch(_){catalogError('كتالوج المنتجات غير متاح حاليًا؛ لا نعتمد أسعارًا غير مكتملة.');}}else catalogError('تعذر تحميل أحدث فحص للمتاجر.');
  if(r[1].status==='fulfilled')telegram(r[1].value);else $('telegramStatus').textContent='تعذر جلب حالة خدمة التنبيهات؛ لا يمكن تأكيد التشغيل الحالي.';
  if(r[2].status==='fulfilled'){
   const a=r[2].value,s=a.manualSample,records=s.records||[],compared=records.filter(x=>typeof x.withinDailyRange==='boolean');
   $('historyAuditStatus').textContent='مراجعة يدوية بتاريخ '+s.reviewDate+': '+compared.filter(x=>x.withinDailyRange).length+' من '+compared.length+' عينات تقع داخل نطاق اليوم المنشور في Investing. هذا لا يثبت مطابقة سعر الإغلاق أو صحة كامل السلسلة. أيام الأسبوع الناقصة: '+(a.historyProfile.missingWeekdays.join('، ')||'لا توجد في نافذة الفحص')+'.';
  }else $('historyAuditStatus').textContent='تعذر جلب سجل التدقيق. المطابقة التاريخية الشاملة غير مكتملة.';
 }
 refresh();setInterval(refresh,60000);
})();
