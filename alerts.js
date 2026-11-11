(function(){
  'use strict';
  function changes(previous,current){
    if(!previous)return [];
    const notices=[];
    if(Math.abs(current.gapEGP-previous.gapEGP)>=75 || Math.abs(current.gapPercent-previous.gapPercent)>=1.5)notices.push('تغيّر مهم في فجوة الذهب: 75 جنيهًا أو 1.5 نقطة مئوية من آخر تنبيه.');
    if(Math.abs(current.fxGap-previous.fxGap)>=1 || Math.abs(current.fxPercent-previous.fxPercent)>=2)notices.push('تغيّر مهم في فجوة الدولار الضمني: جنيه أو نقطتان مئويتان من آخر تنبيه.');
    if(current.local24>previous.peak24 || current.local21>previous.peak21)notices.push('قمة محلية جديدة ضمن القراءات المسجلة على هذا المتصفح.');
    const dd24=(previous.peak24-current.local24)/previous.peak24*100,dd21=(previous.peak21-current.local21)/previous.peak21*100;
    if(dd24-previous.dd24>=2 || dd21-previous.dd21>=2)notices.push('الهبوط من قمة مرصودة على هذا المتصفح تعمق بنقطتين مئويتين.');
    return notices;
  }
  if(typeof module!=='undefined')module.exports={changes};
  if(typeof document==='undefined')return;
  let previous=null;try{previous=JSON.parse(localStorage.getItem('gold-alert-baseline-v1'));}catch(_){}
  window.addEventListener('gold-board-updated',event=>{
    const box=document.getElementById('localAlerts'),status=document.getElementById('alertStatus');if(!box||!status)return;
    const s=event.detail.sources,q=event.detail.quality,r=event.detail.result;
    if(!q?.fresh||!r){status.textContent='التقييم معلق: يلزم وصول مصادر حديثة ومتزامنة. لا يُنشأ تنبيه من مقارنة استرشادية.';return;}
    const a=s.isagha,current={gapEGP:r.gapEGP,gapPercent:r.gapPercent,fxGap:r.fxGap,fxPercent:r.fxPercent,local24:a['24'].sell,local21:a['21'].sell};
    const notices=changes(previous,current);
    status.textContent=notices.length?'تحققت شروط تغير مهمة. التنبيهات تظهر هنا فقط.':previous?'لا تغير يحقق شروط التنبيه منذ آخر مرجع محفوظ.':'تم إنشاء أول مرجع للتنبيهات على هذا المتصفح.';
    if(!previous||notices.length){
      const peak24=Math.max(previous?.peak24||0,current.local24),peak21=Math.max(previous?.peak21||0,current.local21);
      previous={...current,peak24,peak21,dd24:(peak24-current.local24)/peak24*100,dd21:(peak21-current.local21)/peak21*100};
      try{localStorage.setItem('gold-alert-baseline-v1',JSON.stringify(previous));}catch(_){}
      notices.forEach(text=>{const li=document.createElement('li');li.textContent=new Date().toLocaleTimeString('ar-EG',{timeZone:'Africa/Cairo'})+' — '+text;box.prepend(li);});
      while(box.children.length>10)box.lastElementChild.remove();
    }
  });
})();
