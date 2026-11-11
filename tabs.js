(function(){
  'use strict';
  const links=Array.from(document.querySelectorAll('nav a[data-tab]'));
  const panels=Array.from(document.querySelectorAll('[data-panel]'));
  let loadedChart=false;
  function loadChart(){
    if(loadedChart)return;loadedChart=true;
    const script=document.createElement('script');
    script.src='https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async=true;
    script.textContent=JSON.stringify({autosize:true,symbol:'OANDA:XAUUSD',interval:'5',timezone:'Africa/Cairo',theme:'dark',style:'1',locale:'ar',allow_symbol_change:false,calendar:false,hide_volume:true,hide_side_toolbar:false,withdateranges:true,backgroundColor:'#111f35',gridColor:'rgba(180,197,220,0.07)',support_host:'https://www.tradingview.com'});
    script.onerror=()=>{document.getElementById('liveChartStatus').textContent='تعذر تحميل الرسم المضمّن. افتح المصدر مباشرة بالرابط أدناه.';};
    document.getElementById('liveChartEmbed').appendChild(script);
    document.getElementById('liveChartStatus').textContent='رسم مضمّن من TradingView • الذهب مقابل الدولار OANDA:XAUUSD • الإطار الافتراضي 5 دقائق. حالة السوق وتأخر البيانات كما تظهر داخل الرسم.';
  }
  function select(name,focus=false){
    if(!links.some(l=>l.dataset.tab===name))name='market';
    panels.forEach(p=>p.hidden=p.dataset.panel!==name);
    links.forEach(l=>{const on=l.dataset.tab===name;l.setAttribute('aria-selected',String(on));l.tabIndex=on?0:-1;});
    if(name==='live')loadChart();
    if(focus)links.find(l=>l.dataset.tab===name)?.focus();
  }
  const aliases={prices:'market',comparison:'market',analysis:'analysis',calculator:'calculator',sources:'sources',faq:'guide',coverage:'guide',method:'guide',live:'live'};
  function route(){const id=location.hash.slice(1).split('/')[0];select(aliases[id]||id||'market');}
  links.forEach((l,i)=>{l.addEventListener('click',()=>{select(l.dataset.tab);window.scrollTo({top:document.querySelector('nav').offsetTop,behavior:'smooth'});});l.addEventListener('keydown',e=>{let index=i;if(e.key==='ArrowRight')index=(i-1+links.length)%links.length;else if(e.key==='ArrowLeft')index=(i+1)%links.length;else if(e.key==='Home')index=0;else if(e.key==='End')index=links.length-1;else return;e.preventDefault();location.hash=links[index].getAttribute('href').slice(1);select(links[index].dataset.tab,true);});});
  window.addEventListener('hashchange',route);route();
})();
