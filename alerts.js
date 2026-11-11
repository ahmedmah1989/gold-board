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
  function localUsable(a,now=Date.now()){
    const t=Date.parse(a?.sourceTime);
    return a?.status==='available'&&Number.isFinite(t)&&now-t<=300000&&t-now<=120000&&[a?.['24']?.sell,a?.['21']?.sell].every(v=>Number.isFinite(v)&&v>0);
  }
  if(typeof module!=='undefined')module.exports={changes,localUsable};
  if(typeof document==='undefined')return;
  let previousLocal=null,previousComparison=null;try{const saved=JSON.parse(localStorage.getItem('gold-alert-state-v2'));previousLocal=saved?.local||null;previousComparison=saved?.comparison||null;}catch(_){}
  window.addEventListener('gold-board-updated',event=>{
    const box=document.getElementById('localAlerts'),status=document.getElementById('alertStatus');if(!box||!status)return;
    const s=event.detail.sources,q=event.detail.quality,r=event.detail.result;
    if(!localUsable(s.isagha)){status.textContent='انتظار آي صاغة حديثة لمتابعة القمم والهبوط. تنبيهات الفجوة تحتاج كل مصادرها حديثة ومتزامنة.';return;}
    const a=s.isagha,gapReady=q?.fresh&&r,current={gapEGP:gapReady?r.gapEGP:NaN,gapPercent:gapReady?r.gapPercent:NaN,fxGap:gapReady?r.fxGap:NaN,fxPercent:gapReady?r.fxPercent:NaN,local24:a['24'].sell,local21:a['21'].sell};
    const previous=previousLocal?{...previousLocal,gapEGP:previousComparison?.gapEGP,gapPercent:previousComparison?.gapPercent,fxGap:previousComparison?.fxGap,fxPercent:previousComparison?.fxPercent}:null;
    const notices=changes(previous,current);
    status.textContent=notices.length?'تحققت شروط تغير مهمة؛ تظهر هنا بصورة مستقلة عن رسائل Telegram.':gapReady?'لا تغير مهم؛ أول مرجع لكل نوع يُنشأ صامتًا.':'المراقبة المحلية جاهزة؛ تنبيهات الفجوة تنتظر مصادر حديثة ومتزامنة.';
    if(!previousLocal||notices.length){
      const peak24=Math.max(previousLocal?.peak24||0,current.local24),peak21=Math.max(previousLocal?.peak21||0,current.local21);
      previousLocal={local24:current.local24,local21:current.local21,peak24,peak21,dd24:(peak24-current.local24)/peak24*100,dd21:(peak21-current.local21)/peak21*100};
      notices.forEach(text=>{const li=document.createElement('li');li.textContent=new Date().toLocaleTimeString('ar-EG',{timeZone:'Africa/Cairo'})+' — '+text;box.prepend(li);});
      while(box.children.length>10)box.lastElementChild.remove();
    }
    if(gapReady&&(!previousComparison||notices.length))previousComparison={gapEGP:r.gapEGP,gapPercent:r.gapPercent,fxGap:r.fxGap,fxPercent:r.fxPercent};
    try{localStorage.setItem('gold-alert-state-v2',JSON.stringify({local:previousLocal,comparison:previousComparison}));}catch(_){}
  });
})();
