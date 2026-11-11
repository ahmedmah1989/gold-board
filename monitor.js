/* Local calculations only. No bank connection or automatic notification is claimed. */
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
  if (typeof module !== 'undefined') module.exports = { calculate, OUNCE };
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const n = value => { const s = String(value).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/[٬,\s]/g, '').replace(/٫/g, '.'); return /^\d+(\.\d+)?$/.test(s) ? Number(s) : NaN; };
  const fmt = (x, unit = ' جنيه') => Number.isFinite(x) ? x.toLocaleString('ar-EG', { maximumFractionDigits: 2 }) + unit : '—';
  let snapshot = null;
  const time = value => Number.isFinite(Date.parse(value)) ? new Date(value).toLocaleString('ar-EG', {timeZone:'Africa/Cairo'}) + ' بتوقيت القاهرة' : 'غير متاح';
  function verified() {
    if (!snapshot || $('quoteMode').value !== 'auto') return false;
    const a = snapshot.sources.isagha, b = snapshot.sources.misr;
    const times = [a.sourceTime, b.sourceTime, $('oz').dataset.sourceTime].map(Date.parse);
    return a.status === 'available' && b.status === 'available' && times.every(t => Number.isFinite(t) && Date.now()-t >= -120000 && Date.now()-t <= 5*60000) && Math.max(...times)-Math.min(...times) <= 5*60000;
  }
  function render() {
    const auto = $('quoteMode').value === 'auto';
    const r = (!auto || verified()) ? calculate(n($('oz').value), n($('bankSell').value), n($('local24').value), n($('local21').value)) : null;
    const values = r ? [fmt(r.globalEGP), fmt(r.global21), fmt(r.gapEGP), fmt(r.gapUSD, ' دولار'), fmt(r.gapPercent, '%'), fmt(r.implied), fmt(r.fxGap), fmt(r.fxPercent, '%'), fmt(r.drop24) + ' (' + fmt(r.drop24 / 7735 * 100, '%') + ')', r.drop21 === null ? '—' : fmt(r.drop21) + ' (' + fmt(r.drop21 / 6767 * 100, '%') + ')'] : Array(10).fill('—');
    values.forEach((v, i) => $('metric' + i).textContent = v);
    $('gapMeaning').textContent = r ? (r.gapEGP >= 0 ? 'علاوة محلية فوق القيمة العالمية' : 'خصم محلي عن القيمة العالمية') : 'أدخل الأسعار لحساب الفجوة.';
    const t = Date.parse($('quoteTime').value), age = Date.now() - t;
    $('monitorQuality').textContent = auto ? (r ? 'اجتازت فحوص الاكتمال والتوقيت؛ الأسعار المنقولة لا تضمن تنفيذ صفقة' : 'المقارنة معلقة: نحتاج أسعارًا موثقة خلال 5 دقائق وفارق توقيت لا يتجاوز 5 دقائق') : !r ? 'البيانات غير مكتملة' : !Number.isFinite(t) ? 'حساب يدوي غير موثق: وقت التسعير غير محدد' : age < 0 ? 'وقت التسعير في المستقبل؛ راجع الإدخال' : age > 5 * 60000 ? 'اللقطة اليدوية أقدم من 5 دقائق؛ لا تستخدم لتنبيه لحظي' : 'لقطة يدوية حديثة؛ لم يتم التحقق من تزامنها مع المصدر العالمي';
  }
  function applySnapshot() {
    const auto = $('quoteMode').value === 'auto';
    ['bankSell','local24','local21','quoteTime'].forEach(id => $(id).disabled = auto);
    if (auto) {
      const sources = snapshot && snapshot.sources, a = sources && sources.isagha, b = sources && sources.misr;
      $('local24').value = a && a.status === 'available' ? a['24'].sell : '';
      $('local21').value = a && a.status === 'available' ? a['21'].sell : '';
      $('bankSell').value = b && b.status === 'available' ? b.sell : '';
      $('quoteTime').value = '';
    }
    render();
  }
  async function refresh() {
    try {
      const response = await fetch('data/quotes.json?t='+Date.now(), {cache:'no-store'});
      if (!response.ok) throw Error('Unavailable');
      const value = await response.json();
      if (value.schemaVersion !== 1 || !value.sources) throw Error('Unsupported quote schema');
      snapshot = value;
      const a = value.sources.isagha, b = value.sources.misr;
      $('feedStatus').textContent = 'آخر جمع: '+time(value.generatedAt)+' | آي صاغة: '+(a.status==='available' ? 'بيع 24: '+fmt(a['24'].sell)+'، شراء: '+fmt(a['24'].buy)+'؛ بيع 21: '+fmt(a['21'].sell)+'، شراء: '+fmt(a['21'].buy)+'؛ وقت المصدر '+time(a.sourceTime) : 'غير متاح')+' | بنك مصر: '+(b.status==='available' ? 'شراء '+fmt(b.buy)+'، بيع '+fmt(b.sell)+'؛ وقت المصدر '+time(b.sourceTime) : 'غير متاح')+' | الأهلي والمركزي: الربط غير متاح';
    } catch (_) { snapshot = null; $('feedStatus').textContent = 'تعذر تحميل آخر لقطة موثقة. المقارنة التلقائية معلقة.'; }
    applySnapshot();
  }
  $('quoteMode').addEventListener('change', applySnapshot);
  ['bankSell', 'local24', 'local21', 'bankChoice', 'quoteTime'].forEach(id => $(id).addEventListener('input', render));
  $('oz').addEventListener('input', render);
  new MutationObserver(render).observe($('stamp'), { childList: true, subtree: true, characterData: true });
  setInterval(render, 60000); setInterval(refresh, 60000);
  refresh();
})();
