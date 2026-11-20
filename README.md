# لوحة متابعة الذهب

واجهة عربية لحساب القيمة العالمية المحولة، العلاوة المحلية والدولار الضمني.

## حالة المصادر

- الأونصة: gold-api.com؛ updatedAt هو وقت جلب المزود من مصدره وفق توثيقه، وليس توقيت صفقة بورصة.
- السوق المحلي: صفحة أسعار آي صاغة، بيع التاجر للعميل وشراؤه منه منفصلان.
- الدولار: سعر النقد المنشور لبنك مصر؛ ليس متوسط السوق ولا سعر البنك المركزي.
- الأهلي والمركزي: يجري فحص الصفحات الرسمية؛ لم تصل قراءة USD مؤرخة صالحة. صفحة الأهلي واجهة محملة بالسكربت، والمركزي يرفض القراءة. لا نعتبر تاريخ صيانة الصفحة تاريخ السعر، ولا ننسب بديلًا إليهما.
- الأرقام الواردة من النسخة السابقة لتوقعات البنوك لم يُعَد توثيقها في هذا التحديث، ولا تدخل خطة شراء تلقائية.

التجميع المجدول مستهدف كل خمس دقائق وقد تتأخر مهام GitHub. فحص الصفحة للملف كل دقيقة لا يعني سعرًا جديدًا من المصدر. ليست هذه خدمة بث لحظي.

الفجوة تُحسب تلقائيًا من آخر أسعار منشورة، ووقت كل مصدر يظهر تلقائيًا بتوقيت القاهرة. تُوصف بأنها متزامنة فقط إذا كانت القراءات في آخر خمس دقائق والفارق بينها لا يتجاوز خمس دقائق. خلاف ذلك تُعرض كحساب استرشادي مع تنبيه واضح لاختلاف التوقيت. تُحجب عند فقد سعر أو وقت مصدر أو تجاوز عمر أي قراءة 24 ساعة أو وجود توقيت مستقبلي بأكثر من دقيقتين. لا تُرسل تنبيهات الفجوة من الحساب الاسترشادي. تنبيهات القمم والهبوط المحلي مستقلة وتحتاج آي صاغة حديثة فقط. هذه فحوص تشغيلية وليست ضمانًا لصحة المصدر الخارجي.

التصميم يحافظ على لوحة الأسعار والفجوة ويعيد قسم التحليل الأصلي: الرسم اليومي، متوسطات 50 و200 قراءة، مقارنة الفترات، الهبوط والتذبذب والسيناريوهات والتوقعات والمنهجية. التوثيق منفصل لكل مصدر. لا توجد خانة وقت يدوي؛ ويُملأ سعر عيار 21 في الحاسبة تلقائيًا ويمكن تغييره لعرض تاجر.

دُققت معادلات المتوسطات والهبوط باختبارات مستقلة. لا تُحذف قراءة يوم عمل بسبب تساوي سعرها مع اليوم السابق، وتُستبعد النقاط التاريخية المتباعدة من متوسطات وعوائد الفترة الحديثة. سلسلة currency-api مرجعية وليست إغلاقات بورصة موثقة؛ يتم استبعاد عطلة نهاية الأسبوع فقط.

مراجعة التوقعات في 11 نوفمبر 2026: صفحة UBS الرسمية تؤكد مستهدف سبتمبر 2027 وبعض التفسير العام، ولا توثق بقية سلم الأرقام القديم؛ تقرير Kitco يطابق أرقام BofA مع تمييزه كمصدر ثانوي. مستندا رويترز وGoldman تعذر الوصول إليهما وقت المراجعة، والأرقام محفوظة بعلامة قيد التحقق.

## التحقق

`python -m unittest discover -p 'test_*.py'`

`node monitor.test.js`

`node analytics.test.js`

`python collect.py`

Python 3.12+ وقاعدة توقيت IANA (حزمة tzdata مطلوبة على Windows). لا تُخزن مفاتيح أو بيانات حسابات في الموقع.

## ما لم يُفعّل

المقارنة النهائية لثلاثة متاجر وتغذية عالمية مرخصة من TickerChart غير مكتملتين. Telegram موصول عبر أسرار GitHub، وتُعرض حالته من data/alert-state.json. القمم المرصودة منذ أول سعر محلي حديث فقط؛ مرجعا 7735 و6767 واردان من المستخدم وغير مثبتين كتاريخ قياسي للسوق.

## تدقيق 11 نوفمبر 2026

- history_collect.py يجمع السلسلة مرة يوميًا ويستخدم مسار Cloudflare الرسمي الاحتياطي للمزود عند الحاجة؛ ليس مصدرًا مستقلاً ثانيًا. تُراجع قيمة date داخل كل ملف قبل قبوله، وتُسجل الأيام الناقصة. لا توجد 377 قراءة شبكية جديدة لكل زائر.
- data/audit.json يحفظ مقارنة Decimal للحسابات على لقطة محددة، وعينة يدوية من خمسة أيام مع نطاق Investing اليومي. وقوع العينة داخل النطاق لا يعني تطابق الإغلاق أو التحقق الشامل. مراجعة العينة مؤرخة ولا تُعاد تسميتها كمراجعة مباشرة مع كل تشغيل.
- لا يدخل توقع غير موثق في حسابات السيناريوهات. المتوسط يحتاج عدد القراءات المعلن كاملاً؛ والتذبذب يحتاج 60 عائدًا بين أيام أسبوع متتالية، دون افتراض تقويم بورصة غير متحقق منه.
- store_offers.py يسجل صفحات منتجات 8 و4 جرامات كما تنشرها المتاجر؛ لا يخمن المصنعية أو الدمغة أو تاريخ السعر. العروض ذات الرسوم أو التوقيت المجهول لا تدخل ترتيب الأرخص.
- بيانات التشغيل العامة لا تحتوي token أو chat ID؛ تفاصيل المراقبة في دليل الذهب يوضح أن Telegram مخصص لمحادثة المالك وليس اشتراكًا عامًا للزوار.


## كتالوج المنتجات والعرض العام

الواجهة تعرض ربع الجنيه 2 جرام ونصفه 4 جرامات والجنيه 8 جرامات عيار 21، وسبائك 1 و2.5 و5 و10 و20 و50 و100 جرام عيار 24، وأونصة فعلية ترويسية كمنتج مستقل. data/offers.json يستخدم schemaVersion=2 مع catalog وproductId، و21 ملاحظة من صفحات منتجات مباشرة؛ لا تستخدم صفحة متجر عامة كعرض منتج.

فحص هوية الجلا يطابق عنوان المنتج. فحص دهب زمان يطابق الوزن والعيار والمعدن والماركة وعنوان الصفحة من بيانات Product المنظمة. أي تعارض وزن في وصف المنتج يحجب السعر عن الاعتماد. لا تكفي إيجاد عبارة وزن في المنتجات المقترحة أسفل الصفحة. لا يرفض السعر الصحيح لمجرد تجاوزه 200 ألف جنيه؛ فحص الوحدة مرتبط بوزن المنتج.

تحتفظ الواجهة بمنتج واحد مختار ومقارنة مصادره، بروابط #products/quarter و#products/half و#products/pound و#products/bar10 و#products/ounce، والأوزان الأخرى من القائمة. لكل عرض سعره المعلن ورسومه المعروفة والتوافر ووقت الرصد ورابطه. أسعار إعادة الشراء لا تُعرض إلا إذا وردت مباشرة في الصفحة وتطابقت مكوناتها.

العرض المنشور ليس بالضرورة عرضًا نهائيًا مؤهلاً لترتيب الأرخص؛ أهلية المقارنة تحتاج هوية مؤكدة وتوافرًا وشمول كل الرسوم ووقت تسعير حديثًا. مصدر بلا وقت سعر لا يأخذ وقت الجمع بدلاً منه. لا تظهر أسعار المنتجات إذا تجاوز رصد الصفحة 24 ساعة.

Telegram الحالي قناة إدارية للمالك، ولا يمثل اشتراكًا عامًا للزوار. الرابط مذكور ضمن تفاصيل حالة المراقبة فقط. أضيفت إيضاحات قبل الشراء، وبيان نطاق حفظ البيانات في المتصفح والاتصال بالرسم الخارجي، ورابط بلاغات GitHub العامة، ووصف مشاركة ومحركات بحث دون ادعاء لحظية كاملة.

التوقعات التي لم يكتمل توثيقها محفوظة في تفاصيل قابلة للفتح أسفل المصادر الموثقة جزئيًا؛ لا تُحذف ولا تدخل الحسابات، ولا تظهر مستهدفاتها كعناوين جاهزة للاعتماد.


## Freshness follow-up, 20 November 2026

The five-minute GitHub Actions cron is a target, not a guarantee. Actual scheduled starts on this audit day were roughly hourly, while executions took under one minute. GitHub documents delayed and dropped scheduled events: https://docs.github.com/en/actions/how-tos/troubleshoot-workflows . Moving the cron off minute zero reduces avoidable contention; it cannot guarantee delivery. The primary free recommendation is an independent cron-job.org trigger plus an independent heartbeat check, as FRESHNESS-SETUP.md details. No external account or job is provisioned by this PR. Neither cron-job.org nor GitHub guarantees punctuality; this free plan must not be described as a guaranteed five-minute service.

Current-price publication now precedes historical backfill, so history maintenance cannot hold up a new retail snapshot. `data/collection-health.json` records previous collection gap independently of source-price timestamps. It does not certify accuracy or change source times. Its `checkedAt` must itself be checked by a consumer: a stalled collector cannot update its own heartbeat. Tests also run on pull requests without publishing or reading production secrets.

Gold Timo is an OPTIONAL free-tier cross-check enabled only by server-side GitHub Actions secret `GOLDTIMO_API_KEY`. No key belongs in source, browser JavaScript, fixtures, public JSON or PR text. Without it, collection works as before and records `not_configured`. Four karat reads per five-minute cycle consume48 of100 free requests/hour. No paid history or snapshot endpoint is called. API results retain `gramBuy` and `gramSell` exactly as named by the provider; their customer/dealer perspective and upstream independence are not confirmed. Results live under `crosschecks.goldtimo`, never replace primary iSagha/dealer prices and never drive alerts, comparisons or calculators. Provider `updatedAt` is not independently proved to be an underlying market-change time. The live four-karat trial succeeded, but one snapshot is not an uptime or accuracy guarantee.


### Verified marketplace seller

The added10g24kBTC listing at https://market.isagha.com/products/171 belongs to آل حسن عبر آي صاغة, not to every seller on the platform. Its schema, visible product price and product-table price must agree within one response. Seller, SKU171, direct URL,10g weight,24k purity and BTC brand must all match. Full fees and product-pricing time remain unknown, so it is a listed observation only and cannot qualify as the guaranteed lowest all-in offer. Other marketplace sellers require their own separately verified listing.
