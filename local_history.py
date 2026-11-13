"""Archive the local gold price: one record per Cairo day in data/local-history.json.

Runs after collect.py. Reads data/quotes.json and, when the isagha quote is available and its
published time is new, updates today's record (open / high / low / close of the sell price,
the closing buy price, the bank dollar). Nothing is estimated: a day with no reading has no record.
"""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CAIRO = ZoneInfo('Africa/Cairo')
QUOTES = Path('data/quotes.json')
HISTORY = Path('data/local-history.json')
KARATS = ('24', '21')


def update(history, quotes):
    """Return (history, changed). Pure: no file access."""
    days = history.setdefault('days', [])
    sources = quotes.get('sources', {})
    local = sources.get('isagha') or {}
    if local.get('status') != 'available' or not local.get('sourceTime'):
        return history, False
    stamp = datetime.fromisoformat(local['sourceTime'])
    if stamp.tzinfo is None:
        return history, False
    day = stamp.astimezone(CAIRO).date().isoformat()
    for k in KARATS:
        q = local.get(k) or {}
        if not all(isinstance(q.get(x), (int, float)) and q[x] > 0 for x in ('sell', 'buy')):
            return history, False
    last = days[-1] if days else None
    if last and day < last['d']:
        return history, False                      # an older reading never rewrites a later day
    if last and last['d'] == day:
        record = last
        if datetime.fromisoformat(record['lastSourceTime']) >= stamp:
            return history, False                  # same or older published time: nothing new
    else:
        record = {'d': day, 'readings': 0}
        days.append(record)
    for k in KARATS:
        sell, buy = float(local[k]['sell']), float(local[k]['buy'])
        box = record.setdefault(k, {'open': sell, 'high': sell, 'low': sell})
        box['high'] = max(box['high'], sell)
        box['low'] = min(box['low'], sell)
        box['close'] = sell
        box['closeBuy'] = buy
    bank = sources.get('misr') or {}
    if bank.get('status') == 'available' and isinstance(bank.get('sell'), (int, float)):
        record['usd'] = float(bank['sell'])
    record['readings'] += 1
    record['lastSourceTime'] = stamp.isoformat()
    return history, True


if __name__ == '__main__':
    history = json.loads(HISTORY.read_text(encoding='utf-8')) if HISTORY.exists() else {
        'schemaVersion': 1,
        'note': 'Daily local gold readings from isagha as published; sell price open/high/low/close per Cairo day.',
        'days': [],
    }
    history, changed = update(history, json.loads(QUOTES.read_text(encoding='utf-8')))
    if changed:
        HISTORY.write_text(json.dumps(history, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print({'changed': changed, 'days': len(history['days'])})
