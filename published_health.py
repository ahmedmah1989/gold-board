"""Post-publication freshness proof, then a private external dead-man heartbeat.
Never treats an HTTP200 or a workflow-dispatch204 as proof of fresh quotes.
"""
import json, math, os, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from pathlib import Path

BASE = 'https://ahmedmah1989.github.io/gold-board/data/'

def recent(value, now, seconds=600):
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if t.tzinfo is None: return False
        return -120 <= (now-t).total_seconds() <= seconds
    except (TypeError, ValueError, AttributeError): return False

def validate(quotes, offers, now, expected=None):
    if not recent(quotes.get('generatedAt'), now): return False
    if expected and quotes.get('generatedAt') != expected: return False
    if not recent(offers.get('checkedAt'), now): return False
    local = quotes.get('sources', {}).get('isagha', {})
    if local.get('status') != 'available' or not recent(local.get('sourceTime'), now): return False
    if not recent(local.get('fetchedAt'), now): return False
    for karat in ('21', '24'):
        p = local.get(karat, {})
        if not all(isinstance(p.get(k), (float,int)) and not isinstance(p[k],bool) and math.isfinite(p[k]) and p[k]>0 for k in ('buy','sell')): return False
        if p['buy'] > p['sell']: return False
    return isinstance(offers.get('offers'), list) and bool(offers['offers'])

def get_json(name):
    # Public Pages read, no account cookies or private response data.
    url = BASE + name + '?freshness=' + str(int(time.time()))
    with urlopen(Request(url, headers={'Cache-Control':'no-cache', 'User-Agent':'Dahabology-Freshness/1.0'}), timeout=20) as r:
        return json.load(r)

def ping(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != 'hc-ping.com' or parsed.query or parsed.fragment:
        raise ValueError('Invalid heartbeat destination')
    with urlopen(Request(url, data=b'', method='POST'), timeout=15) as r:
        if not 200 <= r.status < 300: raise ValueError('Heartbeat rejected')

def main():
    destination = os.environ.get('FRESHNESS_HEARTBEAT_URL', '')
    if not destination:
        print('Freshness heartbeat not configured; no external monitor was signaled.')
        return
    expected = json.loads(Path('data/quotes.json').read_text())['generatedAt']
    for attempt in range(6):
        try:
            if validate(get_json('quotes.json'), get_json('offers.json'), datetime.now(timezone.utc), expected):
                ping(destination)
                print('Published primary quote freshness verified; external heartbeat accepted.')
                return
        except Exception:
            pass  # Never include private heartbeat URLs in workflow errors.
        if attempt < 5: time.sleep(20)
    print('Published freshness could not be proved; no success heartbeat sent.')
    raise SystemExit(1)

if __name__ == '__main__': main()
