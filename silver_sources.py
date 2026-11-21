"""Local silver prices from the iSagha silver page. Fails closed on a changed table, missing time or odd figures."""
import re
from datetime import datetime

OUNCE_G = 31.1034768
GRADES = ('999', '925', '900', '800', '600')

def parse_isagha_silver(html):
    stamp = re.search(r'<time\s+datetime="([^"]+)"\s+data-testid="prices-updated"', html)
    if not stamp: raise ValueError('Missing silver quote time')
    when = datetime.fromisoformat(stamp[1])
    if when.tzinfo is None: raise ValueError('Missing quote timezone')
    head = re.search(r'<thead\b[^>]*>(.*?)</thead>', html, re.S)
    labels = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x)).strip() for x in re.findall(r'<th\b[^>]*>(.*?)</th>', head[1], re.S)] if head else []
    # Column order is read from the page headers, never assumed: grade, sell, gap, buy.
    if len(labels) < 4 or not labels[1].startswith('بيع') or not labels[3].startswith('شراء'):
        raise ValueError('Unrecognized silver column order')
    def figures(unit, currency):
        row = re.search(r'<tr\b[^>]*data-unit="' + unit + r'"[^>]*>(.*?)</tr>', html, re.S)
        if not row: raise ValueError('Missing silver row')
        cells = re.findall(r'<td\b[^>]*>(.*?)</td>', row[1], re.S)
        out = []
        for i in (1, 3):
            # The figure must be a plain number followed by the expected currency label in the same cell.
            m = re.search(r'data-testid="price-figure"[^>]*>(\d+(?:\.\d+)?)</span>\s*([^\s<]+)\s*$', cells[i].strip()) if len(cells) > 3 else None
            if not m or m[2] != currency: raise ValueError('Missing silver buy/sell figure or currency')
            out.append(float(m[1]))
        return out
    grades = {}
    for g in GRADES:
        sell, buy = figures(g, 'ج.م')
        if not 1 < buy <= sell < 10000: raise ValueError('Invalid silver spread')
        grades[g] = {'sell': sell, 'buy': buy}
    # Purity ordering and ratios: sells strictly fall with purity and sit within 1.5 points of purity/999 (live ratios differ by at most 0.4 points).
    for a, b in zip(GRADES, GRADES[1:]):
        if not grades[a]['sell'] > grades[b]['sell'] or not grades[a]['buy'] > grades[b]['buy']: raise ValueError('Silver grades out of purity order')
    for g in GRADES[1:]:
        if abs(grades[g]['sell'] / grades['999']['sell'] - int(g) / 999) > .015: raise ValueError('Silver purity consistency check failed')
    osell, obuy = figures('s_ounce', '$')
    if not 1 < obuy <= osell < 1000: raise ValueError('Invalid silver ounce spread')
    # The page prints no unit on grade rows. The silver pound row on the same page is the independent check. Its weight and grade are not printed on the row; the same site's product pages 9042 and 9053 list 925 silver pounds with a net weight of 8 g:
    # its price must equal 8 times the 925 per-gram price, on both sides. A per-ounce or per-kilo price would break this.
    psell, pbuy = figures('pound', 'ج.م')
    for pound, gram in ((psell, grades['925']['sell']), (pbuy, grades['925']['buy'])):
        if abs(pound / 8 - gram) > .01 * gram: raise ValueError('Silver unit check failed against the pound row')
    # Scale guard. The same page's gold ticker gives a second USD/EGP-implied figure from independent products (24k gram and gold ounce).
    # The silver-implied figure must be close to it. This is a relative consistency check between two quotes of one page and not an FX range.
    # It rejects a uniform rescale of the whole silver table (x31.1035, /31.1035, x2), which the pound-row check cannot see.
    ticker = {}
    for a in re.findall(r'<a\b[^>]*data-testid="ticker-item"[^>]*>.*?</a>', html, re.S):
        unit, metal = re.search(r'data-unit="([^"]*)"', a), re.search(r'data-metal="([^"]*)"', a)
        # Figure plus its currency label inside the same item: gold 24 per gram in ج.م, gold ounce in $.
        fig = re.search(r'data-testid="price-figure"[^>]*>(\d+(?:\.\d+)?)</span>\s*<small[^>]*>\s*([^<\s]+)\s*</small>', a)
        if unit and metal and fig and metal[1] == 'gold' and unit[1] in ('24', 'ounce') and fig[2] == ('ج.م' if unit[1] == '24' else '$'): ticker.setdefault(unit[1], float(fig[1]))
    if set(ticker) != {'24', 'ounce'} or not all(v > 0 for v in ticker.values()): raise ValueError('Silver scale check failed: no gold ticker to compare')
    gold_fx = ticker['24'] / (ticker['ounce'] / OUNCE_G); silver_fx = grades['999']['sell'] / (osell / OUNCE_G)
    if abs(silver_fx / gold_fx - 1) > .10: raise ValueError('Silver scale check failed: silver and gold quotes on the page disagree by more than 10%')
    return {'source': 'iSagha local trader quote', 'unitBasis': 'per gram, not printed on the page; matches the silver pound row on the same page; the same site lists 925 silver pound products of 8 g (products 9042 and 9053), but the row itself does not state weight or grade', 'sourceTime': when.isoformat(), 'sourceTimeKind': 'published_price_update', 'unit': 'gram', 'currency': 'EGP', 'grades': grades, 'ounceUsd': {'sell': osell, 'buy': obuy}}
