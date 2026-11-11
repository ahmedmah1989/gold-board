(function(){
  var OZ=31.1034768, K21=0.875, EVERY=5*60*1000, FC_REVIEWED="2026-11-11";
  var HBASE="https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@";
  var SERIES=null, M=null;

  function $(i){return document.getElementById(i)}
  function num(v){
    v=String(v==null?"":v).replace(/[٠-٩]/g,function(d){return "٠١٢٣٤٥٦٧٨٩".indexOf(d)}).replace(/٫/g,".").replace(/[٬,\s]/g,"");
    var n=parseFloat(v); return isFinite(n)?n:NaN;
  }
  function fmt(n,d){return n.toLocaleString("en-US",{maximumFractionDigits:d||0,minimumFractionDigits:d||0})}
  function sg(v,d){return (v>=0?"+":"−")+fmt(Math.abs(v),d==null?1:d)+"%"}
  function store(k,v){try{ if(v===undefined) return localStorage.getItem(k); localStorage.setItem(k,v);}catch(e){return null}}
  function tag(el,cls,txt){el.className="tag "+cls; el.textContent=txt}
  function iso(d){return d.toISOString().slice(0,10)}
  function addDays(d,n){var x=new Date(d.getTime()); x.setUTCDate(x.getUTCDate()+n); return x}
  function days(a,b){return Math.round((Date.parse(b)-Date.parse(a))/864e5)}
  function nextWeekday(a,b){var d=addDays(new Date(a+'T00:00:00Z'),1);while(d.getUTCDay()===0||d.getUTCDay()===6)d=addDays(d,1);return iso(d)===b;}
  function k21(oz,usd){return oz*usd/OZ*K21}
  async function getJSON(u){var r=await fetch(u,{cache:"no-store"}); if(!r.ok) throw new Error(r.status); return r.json()}

  /* ===== البيانات اليومية ===== */
  async function dayPoint(date){
    var k="gd_"+date, c=store(k);
    if(c){ if(c==="x") return null; try{return JSON.parse(c)}catch(e){} }
    try{
      var r=await fetch(HBASE+date+"/v1/currencies/xau.json");
      if(r.status===404){ if(days(date,iso(new Date()))>3) store(k,"x"); return null; }
      if(!r.ok) return null;
      var j=await r.json(), p={d:date,usd:num(j.xau.usd),egp:num(j.xau.egp)};
      if(p.usd>0&&p.egp>0){store(k,JSON.stringify(p)); return p}
    }catch(e){}
    return null;
  }
  async function loadSeries(){
    var raw=await getJSON('data/history.json?t='+Date.now());
    var seen=new Set(),out=(raw.points||[]).filter(function(p){
      if(!/^\d{4}-\d{2}-\d{2}$/.test(p.d)||!Number.isFinite(p.usd)||!Number.isFinite(p.egp)||p.usd<=0||p.egp<=0||p.d>=iso(new Date())||seen.has(p.d))return false;
      seen.add(p.d);return true;
    });
    if($("historyQuality"))$("historyQuality").textContent='آخر قراءة: '+(raw.profile?.lastReferenceDate||'غير متاحة')+' • '+(raw.profile?.availableWeekdays||0)+' قراءة من '+(raw.profile?.expectedWeekdays||0)+' يوم عمل متوقع. '+(raw.profile?.missingWeekdays?.length?'توجد أيام ناقصة؛ التفاصيل في ملف البيانات.':'لا توجد أيام أسبوع ناقصة ضمن نافذة الجمع.')+' استبعاد السبت والأحد لا يثبت مطابقة تقويم التداول.';
    out.sort(function(a,b){return a.d<b.d?-1:1});
    // أيام التداول بس: من غير السبت والأحد، ومن غير قيم مكررة حرفيًا (عطلات)
    var tr=[];
    out.forEach(function(p){
      var wd=new Date(p.d+"T00:00:00Z").getUTCDay(); if(wd===0||wd===6) return;
      // Do not delete a trading date merely because its price equals the previous date.
      tr.push(p);
    });
    return tr;
  }

  function metrics(S){
    var last=S[S.length-1], today=last.d;
    var recent=S.filter(function(p){return days(p.d,today)<=372}); var lastN=function(n){return recent.slice(Math.max(0,recent.length-n))};
    var mean=function(a,n){return a.length===n?a.reduce(function(s,p){return s+p.usd},0)/a.length:null};
    var y=S.filter(function(p){return days(p.d,today)<=365});
    var hi=y[0],lo=y[0]; y.forEach(function(p){if(p.usd>hi.usd)hi=p; if(p.usd<lo.usd)lo=p});
    var peak=y[0].usd, mdd=0, pk=y[0], tr=y[0], curPk=y[0];
    y.forEach(function(p){ if(p.usd>peak){peak=p.usd; curPk=p} var dd=(peak-p.usd)/peak; if(dd>mdd){mdd=dd; pk=curPk; tr=p} });
    var r60=lastN(61), rets=[];
    for(var i=1;i<r60.length;i++) if(nextWeekday(r60[i-1].d,r60[i].d))rets.push(Math.log(r60[i].usd/r60[i-1].usd));
    var mu=rets.reduce(function(s,v){return s+v},0)/rets.length;
    var sd=rets.length===60?Math.sqrt(rets.reduce(function(s,v){return s+(v-mu)*(v-mu)},0)/(rets.length-1)):null;
    var a50=lastN(50), a200=lastN(200);
    return {last:last, sma50:mean(a50,50), n50:a50.length, sma200:mean(a200,200), n200:a200.length,
      hi:hi, lo:lo, mdd:mdd, mddPk:pk, mddTr:tr, sdD:sd, volA:sd===null?null:sd*Math.sqrt(252), year:y};
  }
  function asOf(S,target){var best=null; S.forEach(function(p){ if(p.d<=target) best=p }); return best&&days(best.d,target)<=6?best:null}

  /* ===== العرض ===== */
  function cell(v,c){var td=document.createElement("td"); td.textContent=v; if(c) td.className=c; return td}

  function drawMarket(){
    var S=SERIES, m=M, L=m.last, f=function(p){return p.egp/OZ*K21};
    var tb=$("perBody"); tb.textContent="";
    [["أسبوع",7],["شهر",30],["3 شهور",91],["6 شهور",182],["سنة",365],["سنتين",730]].forEach(function(x){
      var p=asOf(S,iso(addDays(new Date(L.d+"T00:00:00Z"),-x[1]))); if(!p) return;
      var tr=document.createElement("tr"), a=(L.usd/p.usd-1)*100, b=(f(L)/f(p)-1)*100;
      tr.appendChild(cell(x[0]+" ("+p.d+")"));
      tr.appendChild(cell(fmt(p.usd)+" $")); tr.appendChild(cell(sg(a),a>=0?"up":"dn"));
      tr.appendChild(cell(fmt(f(p))+" ج")); tr.appendChild(cell(sg(b),b>=0?"up":"dn"));
      tb.appendChild(tr);
    });
    $("perNote").textContent="المقارنة كلها بآخر سعر يومي متاح ("+L.d+"): الأونصة "+fmt(L.usd)+" دولار، وعيار 21 بالقيمة العالمية "+fmt(f(L))+" جنيه. عمود عيار 21 بيشمل أثر تغير الدولار.";

    $("iA50").textContent=m.sma50===null?'غير متاح — أقل من 50 قراءة':fmt(m.sma50)+" دولار ("+(L.usd>m.sma50?"السعر فوقه":"السعر تحته")+")";
    $("iA200").textContent=m.sma200===null?'غير متاح — أقل من 200 قراءة':fmt(m.sma200)+" دولار ("+(L.usd>m.sma200?"السعر فوقه":"السعر تحته")+")";
    $("iHL").textContent="من "+fmt(m.lo.usd)+" لـ "+fmt(m.hi.usd)+" دولار";
    var nowP=L.usd; $("iDD").textContent="−"+fmt(Math.max(0,(m.hi.usd-nowP)/m.hi.usd*100),1)+"% عن قمة "+fmt(m.hi.usd)+" دولار يوم "+m.hi.d;
    $("iMDD").textContent="−"+fmt(m.mdd*100,1)+"% (من "+m.mddPk.d+" لـ "+m.mddTr.d+")";
    $("iVol").textContent=m.volA===null?'غير متاح — عوائد يومية ناقصة':fmt(m.volA*100,1)+"% سنويًا";
    drawChart();
  }

  function rollMean(arr,i,n){ if(i+1<n || days(arr[i-n+1].d,arr[i].d)>n*2) return null; var s=0; for(var k=i-n+1;k<=i;k++) s+=arr[k].usd; return s/n }
  function drawChart(){
    var S=SERIES, y=M.year, start=S.indexOf(y[0]);
    var pts=y.map(function(p,i){var gi=start+i; return {v:p.usd, m200:rollMean(S,gi,200), m50:rollMean(S,gi,50)}});
    var all=[]; pts.forEach(function(p){all.push(p.v); if(p.m200) all.push(p.m200); if(p.m50) all.push(p.m50)});
    var W=660,H=240,Lm=56,R=12,T=14,B=30, mn=Math.min.apply(null,all), mx=Math.max.apply(null,all), pad=(mx-mn)*0.06; mn-=pad; mx+=pad;
    if(mx===mn){mn-=1;mx+=1;}
    var X=function(i){return Lm+(W-Lm-R)*days(y[0].d,y[i].d)/Math.max(1,days(y[0].d,M.last.d))}, Y=function(v){return T+(H-T-B)*(1-(v-mn)/(mx-mn))};
    var NS="http://www.w3.org/2000/svg", svg=document.createElementNS(NS,"svg");
    svg.setAttribute("viewBox","0 0 "+W+" "+H); svg.setAttribute("role","img");
    svg.setAttribute("aria-label","سعر الأونصة اليومي خلال 12 شهر من "+fmt(y[0].usd)+" إلى "+fmt(M.last.usd)+" دولار، وأعلى سعر مرجعي يومي "+fmt(M.hi.usd));
    var cs=getComputedStyle($("chart").closest('.chart')), C=function(n){return cs.getPropertyValue(n).trim()};
    function line(x1,y1,x2,y2,st){var l=document.createElementNS(NS,"line"); l.setAttribute("x1",x1); l.setAttribute("x2",x2); l.setAttribute("y1",y1); l.setAttribute("y2",y2); l.setAttribute("stroke",st); svg.appendChild(l)}
    function text(x,y,t,anc){var e=document.createElementNS(NS,"text"); e.setAttribute("x",x); e.setAttribute("y",y); e.setAttribute("text-anchor",anc); e.setAttribute("font-size","12"); e.setAttribute("fill",C("--ink")); e.textContent=t; svg.appendChild(e)}
    for(var g=0;g<=3;g++){var v=mn+(mx-mn)*g/3; line(Lm,Y(v),W-R,Y(v),C("--line")); text(Lm-6,Y(v)+4,fmt(v),"end")}
    function path(key,color,w,dash){
      var d="",on=false; pts.forEach(function(p,i){var v=p[key]; if(v==null){on=false;return} d+=(on?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)+" "; on=true});
      if(!d) return; var e=document.createElementNS(NS,"path"); e.setAttribute("d",d); e.setAttribute("fill","none"); e.setAttribute("stroke",color); e.setAttribute("stroke-width",w); if(dash) e.setAttribute("stroke-dasharray",dash); e.setAttribute("stroke-linejoin","round"); svg.appendChild(e);
    }
    path("m200",C("--teal"),2,"7 5"); path("m50",C("--bad"),2,"2 4"); path("v",C("--gold"),2.5);
    text(X(0),H-8,y[0].d,"start"); text(X(pts.length-1),H-8,M.last.d,"end");
    var box=$("chart"); box.textContent=""; box.appendChild(svg);
  }

  function drawRanges(){
    var usd=num($("usd").value); if(!(usd>0)) usd=M.last.egp/M.last.usd;
    var oz=num($("oz").value); if(!(oz>0)) oz=M.last.usd;
    var sm=M.sdD===null?null:M.sdD*Math.sqrt(21);
    var a1=oz*Math.exp(-sm), b1=oz*Math.exp(sm), a2=oz*Math.exp(-2*sm), b2=oz*Math.exp(2*sm);
    var stress=oz*(1-M.mdd);
    var box=$("rngBox"); box.textContent="";
    function item(title,lines,src){
      var li=document.createElement("li"), h=document.createElement("h3"); h.textContent=title; li.appendChild(h);
      lines.forEach(function(t,i){var d=document.createElement("div"); if(i===0) d.className="v"; d.textContent=t; li.appendChild(d)});
      var s=document.createElement("span"); s.className="ev"; s.textContent=src; li.appendChild(s); box.appendChild(li);
    }
    var basis='الأونصة المستخدمة '+fmt(oz)+' دولار، والدولار '+fmt(usd,2)+' جنيه. '+(num($("oz").value)>0&&num($("usd").value)>0?'آخر قراءات صالحة من بطاقات السوق؛ راجع حالة تزامنها.':'مرجع يومي '+M.last.d+'، وسعر صرف ضمني من نفس السلسلة؛ ليس سعر بنك مصر الحالي.')+' السعر المحوّل ليس سعر منتج محلي نهائي.';
    if(sm!==null)item("1) سيناريو تذبذب لشهر — ليس توقعًا مضمونًا",
      ["القيمة العالمية المحوّلة لجرام 21 بين "+fmt(k21(a1,usd))+" و"+fmt(k21(b1,usd))+" جنيه (الأونصة "+fmt(a1)+"–"+fmt(b1)+" $)",
       "نطاق ±انحراف معياري للعوائد اللوغاريتمية، بصفر انجراف وثبات الدولار والتذبذب؛ ليس احتمالًا مُعايرًا لنتيجة السوق. نطاق ±انحرافين: "+fmt(k21(a2,usd))+"–"+fmt(k21(b2,usd))+" جنيه."],basis);
    else item('1) سيناريو التذبذب غير متاح',['يلزم 60 عائدًا يوميًا دون فجوات طويلة. لم يُستبدل النقص بقيمة صفرية.'],basis);
    item("2) توقعات الجهات — راجع كل أجل منفصلًا",
      ["الأرقام غير الموثقة لا تدخل الحسابات. توقع UBS لسبتمبر 2027 محفوظ في سجل المصادر أدناه؛ لا يُجمع مع متوسط BofA لربع أو سنة مختلفة في نطاق واحد."],"آراء مؤرخة وليست إجماعًا أو توصية شراء");
    item("3) اختبار ضغط: لو تكرر أسوأ هبوط في السنة",
      ["عيار 21 ممكن يوصل حوالي "+fmt(k21(stress,usd))+" جنيه (الأونصة "+fmt(stress)+" $، −"+fmt(M.mdd*100,1)+"%)",
       "إعادة تطبيق نسبة الهبوط المرصودة في السلسلة المرجعية بين "+M.mddPk.d+" و"+M.mddTr.d+". قد تكون الخسارة الفعلية أكبر، والمطابقة التاريخية المستقلة لم تكتمل."],basis);
  }

  /* ===== القرار ===== */
  function render(){
    var oz=num($("oz").value), usd=num($("usd").value), loc=num($("loc").value), bud=num($("bud").value);
    var sig=$("signal"), plan=$("plan"); sig.className="signal"; plan.textContent="";
    var f21=(oz>0&&usd>0)?k21(oz,usd):NaN, pr=NaN;
    $("f21").textContent=f21>0?fmt(f21)+" جنيه":"—";
    if(loc>0&&f21>0){ var d=loc-f21; pr=d/f21*100; $("diff").textContent=(d>=0?"أغلى بـ":"أرخص بـ")+fmt(Math.abs(d))+" ج ("+fmt(Math.abs(pr),1)+"%)"; }
    else $("diff").textContent="—";
    $("gramsLegacy").textContent=(bud>0&&loc>0)?fmt(bud/loc,2)+" جرام":"—";

    // فحص 1
    var r1=null;
    if(pr===pr){ r1=pr<=2?"good":pr<=4?"warn":"bad"; tag($("t1"),r1,pr<0?'خصم':pr<=2?'علاوة حتى 2%':pr<=4?'علاوة 2–4%':'علاوة فوق 4%');
      $("c1").textContent=(pr<0?"السعر المحلي أقل من القيمة العالمية المحوّلة بـ":"السعر المحلي أعلى من القيمة العالمية المحوّلة بـ")+fmt(Math.abs(pr),1)+"%. هذه مقارنة للجرام قبل رسوم المنتج؛ حدود 2% و4% وصفية ولا تثبت أن العرض مناسب للشراء.";
    } else { tag($("t1"),"none","انتظار أسعار صالحة"); $("c1").textContent='المقارنة تُستكمل تلقائيًا عندما تصل مصادر صالحة وبأوقاتها الأصلية.'; }

    // فحص 2
    var up=null;
    if(M&&M.sma50!==null&&M.sma200!==null){ var L=M.last.usd, a=L>M.sma50, b=L>M.sma200; up=a&&b;
      var r2=up?"good":"warn"; tag($("t2"),r2,up?"طالع":(!a&&!b?"نازل":"متذبذب"));
      $("c2").textContent=(up?"السعر ("+fmt(L)+") فوق متوسط 50 يوم ("+fmt(M.sma50)+") وفوق متوسط 200 يوم ("+fmt(M.sma200)+"). الاتجاه طالع على المدى القريب والطويل."
        :(!a&&!b)?"السعر ("+fmt(L)+") تحت متوسط 50 يوم ("+fmt(M.sma50)+") وتحت متوسط 200 يوم ("+fmt(M.sma200)+"). السوق في موجة نزول، ومحدش يعرف القاع فين."
        :b?"الاتجاه الطويل طالع (فوق متوسط 200 يوم "+fmt(M.sma200)+")، لكن القريب نازل (تحت متوسط 50 يوم "+fmt(M.sma50)+")."
          :"الاتجاه القريب بدأ يطلع (فوق متوسط 50 يوم "+fmt(M.sma50)+")، لكن الطويل لسه نازل (تحت متوسط 200 يوم "+fmt(M.sma200)+"). الاتجاه لسه مأكدش إنه قلب.");
    } else { tag($("t2"),"none","بيتحسب"); $("c2").textContent="بحمّل البيانات اليومية عشان أحسب المتوسطات."; }

    // فحص 3
    var cu=null;
    tag($("t3"),"warn","توثيق منفصل لكل جهة");
    $("c3").textContent="لا يوجد رقم إجماع معتمد في الحسابات. راجع سجل التوقعات: المصدر وتاريخ النشر وأجل المستهدف وحالة التحقق لكل جهة.";

    // القرار
    var H=$("sigHead"), T=$("sigText");
    function step(t){var li=document.createElement("li"); li.textContent=t; plan.appendChild(li)}
    var part=function(n){return (bud>0)?" ("+fmt(bud/n)+" جنيه"+(loc>0?" ≈ "+fmt(bud/n/loc,2)+" جرام":"")+")":""};
    if(!(oz>0&&usd>0)){ sig.classList.add("info"); H.textContent="حسابات السعر الحالي معلقة"; T.textContent="انتظار مصادر صالحة تلقائيًا. الرسم والمؤشرات اليومية يحتفظان بتاريخ آخر قراءة مرجعية؛ لا يُعاد وصفها كأسعار حالية."; return; }
    sig.classList.add("info"); H.textContent="قراءة وصفية للمؤشرات — بدون قرار شراء آلي";
    T.textContent="التحليل الحالي يستخدم سعر بيع بنك مصر المنشور. اتجاه السعر والتذبذب أوصاف حسابية، والتوقعات آراء مؤرخة بحالات توثيق مستقلة؛ لا تتجمع تلقائيًا في توصية شراء."; return;
  }


  if(typeof module !== 'undefined') {module.exports={metrics:metrics,asOf:asOf,rollMean:rollMean,nextWeekday:nextWeekday};return;}
  window.addEventListener('gold-board-updated',function(event){
    var s=event.detail.sources, g=s.gold, b=s.misr, a=s.isagha;
    var ready=event.detail.quality.usable;
    $("oz").value=ready?g.sell:'';
    $("usd").value=ready?b.sell:'';
    $("loc").value=ready?a['21'].sell:'';
    $("bud").value=document.getElementById('budget').value;
    if(M){drawMarket();drawRanges();}render();
  });
  $("fcAge").textContent='مراجعة المصادر: 11 نوفمبر 2026. تحقق جزئي موضح بجوار كل جهة؛ التوقعات ذات آجال مختلفة ولا تُجمع كنطاق موحد.';
  render();
  loadSeries().then(function(S){
    if(S.length<220){ $("chart").textContent="البيانات التاريخية ناقصة دلوقتي ("+S.length+" يوم). جرّب «حدّث الآن» بعد شوية."; $("rngBox").textContent=""; return; }
    SERIES=S; M=metrics(S); window.__GOLD={S:S,M:M}; drawMarket(); drawRanges(); render();
  }).catch(function(){ $("chart").textContent="معرفتش أجيب البيانات التاريخية دلوقتي."; });
})();
