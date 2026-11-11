"""Collect public quotes; fail closed on missing source time or changed HTML."""
import json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

URLS = {
    'isagha': 'https://market.isagha.com/prices',
    'misr': 'https://www.banquemisr.com/CAPITAL-MARKETS/Exchange-Rates-and-Currencies',
    'gold': 'https://api.gold-api.com/price/XAU',
}

def parse_isagha(html):
    stamp = re.search(r'<time\s+datetime="([^"]+)"\s+data-testid="prices-updated"', html)
    if not stamp: raise ValueError('Missing local quote time')
    result = {'sourceTime': datetime.fromisoformat(stamp[1]).isoformat()}
    for unit in ['24', '21']:
        row = re.search(r'<tr\b[^>]*data-unit="'+unit+r'"[^>]*>(.*?)</tr>', html, re.S)
        if not row: raise ValueError('Missing local quote row')
        cells = re.findall(r'<td\b[^>]*>(.*?)</td>', row[1], re.S)
        values = []
        for i in (1, 3):
            match = re.search(r'data-testid="price-figure"[^>]*>([\d.]+)</span>', cells[i])
            if not match: raise ValueError('Missing buy/sell figure')
            values.append(float(match[1]))
        sell, buy = values
        if not 100 < buy <= sell < 100000: raise ValueError('Invalid local spread')
        result[unit] = {'sell': sell, 'buy': buy}
    if abs(result['21']['sell'] / result['24']['sell'] - 21/24) > .02:
        raise ValueError('Purity consistency check failed')
    return result

def parse_misr(html):
    stamp = re.search(r'generic-details-title[^>]*>\s*<p>([^<]+)</p>', html)
    row = re.search(r'<tr>\s*<td>[^<]*(?:.*?US Dollar.*?)</tr>', html, re.S)
    # Restrict to the one row actually containing US Dollar.
    rows = [x for x in re.findall(r'<tr\b[^>]*>(.*?)</tr>', html, re.S) if 'US Dollar' in x]
    if not stamp or len(rows) != 1: raise ValueError('Missing bank quote or time')
    cells = re.findall(r'<td\b[^>]*>(.*?)</td>', rows[0], re.S)
    buy, sell = (float(re.sub(r'<[^>]+>', '', x).strip()) for x in cells[1:3])
    if not 1 < buy <= sell < 1000: raise ValueError('Invalid bank spread')
    when = datetime.strptime(stamp[1].strip(), '%d-%m-%Y %H:%M:%S').replace(tzinfo=ZoneInfo('Africa/Cairo'))
    return {'sourceTime': when.isoformat(), 'buy': buy, 'sell': sell, 'quoteType': 'notes'}

def fetch(name):
    now = datetime.now(timezone.utc).isoformat()
    try:
        req = urllib.request.Request(URLS[name], headers={'User-Agent': 'GoldBoard/1.0 public quote monitoring'})
        with urllib.request.urlopen(req, timeout=25) as response:
            html = response.read().decode('utf-8')
        if name == 'gold':
            raw = json.loads(html)
            price = float(raw['price'])
            if not 100 < price < 100000: raise ValueError('Invalid ounce price')
            data = {'sell': price, 'sourceTime': datetime.fromisoformat(raw['updatedAt'].replace('Z', '+00:00')).isoformat(), 'name': 'gold-api.com'}
        else:
            data = (parse_isagha if name == 'isagha' else parse_misr)(html)
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(data['sourceTime'])).total_seconds()
        if age < -120: raise ValueError('Source timestamp in future')
        return name, dict(data, status='available', fetchedAt=now, url=URLS[name])
    except Exception:
        return name, {'status': 'unavailable', 'fetchedAt': now, 'url': URLS[name], 'reason': 'تعذر توثيق السعر ووقت المصدر؛ لم يُستخدم سعر بديل'}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool: sources = dict(pool.map(fetch, URLS))
    sources['nbe'] = {'status': 'unavailable', 'reason': 'لم يُتحقق من قناة ربط مستقرة للبنك الأهلي'}
    sources['cbe'] = {'status': 'unavailable', 'reason': 'لم يُتحقق من قناة ربط مستقرة لمرجع البنك المركزي'}
    out = {'schemaVersion': 1, 'generatedAt': datetime.now(timezone.utc).isoformat(), 'sources': sources}
    Path('data').mkdir(exist_ok=True)
    Path('data/quotes.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print({name: value['status'] for name, value in sources.items()})
