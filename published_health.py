"""Post-publication freshness proof, then a private external dead-man heartbeat.
Never treats an HTTP200 or a workflow-dispatch204 as proof of fresh quotes.
The proof covers the pipeline: this run collected and its files were published.
Local-source quietness is reported through source_state() and a workflow warning;
an old but displayable price is never treated as fresh, and an unusable one still
fails closed.
"""
import json, math, os, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from pathlib import Path

BASE = 'https://ahmedmah1989.github.io/gold-board/data/'

SOURCE_DISPLAY_LIMIT = 86400  # Board display rule: readings older than 24h are shown as unavailable.

def recent(value, now, seconds=600):
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if t.tzinfo is None: return False
        return -120 <= (now-t).total_seconds() <= seconds
    except (TypeError, ValueError, AttributeError): return False

def source_state(local, now):
    """'fresh': the source published inside the 600 second freshness window.
    'quiet': the source's last published price is older than that but still inside the
    board's 24 hour display rule, so it is shown as the last published price.
    None: the observation cannot be represented at all (unavailable, unparsable time,
    future time, older than 24 hours, or invalid prices)."""
    if local.get('status') != 'available': return None
    value = local.get('sourceTime')
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if t.tzinfo is None: return None
        age = (now - t).total_seconds()
    except (TypeError, ValueError, AttributeError): return None
    if age < -120 or age > SOURCE_DISPLAY_LIMIT: return None
    for karat in ('21', '24'):
        p = local.get(karat, {})
        if not all(isinstance(p.get(k), (float,int)) and not isinstance(p[k],bool) and math.isfinite(p[k]) and p[k]>0 for k in ('buy','sell')): return None
        if p['buy'] > p['sell']: return None
    return 'fresh' if age <= 600 else 'quiet'

def validate(quotes, offers, now, expected=None):
    # Proves this run's collection was published. Source quietness never fails the
    # pipeline proof here; it is reported by source_state() and surfaced as a warning.
    if not recent(quotes.get('generatedAt'), now): return False
    if expected and quotes.get('generatedAt') != expected: return False
    if not recent(offers.get('checkedAt'), now): return False
    local = quotes.get('sources', {}).get('isagha', {})
    if source_state(local, now) is None: return False
    if not recent(local.get('fetchedAt'), now): return False
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

POLL_SECONDS = 20

def wait_for_publication(fetch, check, expected, now=lambda: datetime.now(timezone.utc), sleep=time.sleep, window=600, poll=POLL_SECONDS):
    """Poll until the published files prove a fresh run or the wall-clock window closes.
    The window is the same 600 seconds validate() allows for every timestamp, measured from the
    expected generation time, so waiting longer never accepts data older than that limit."""
    try: start = datetime.fromisoformat(expected.replace('Z', '+00:00'))
    except (AttributeError, ValueError): return False
    if start.tzinfo is None: return False
    while True:
        current = now()
        try:
            if check(fetch('quotes.json'), fetch('offers.json'), current, expected): return True
        except Exception:
            pass  # Never include private heartbeat URLs in workflow errors.
        if (current - start).total_seconds() + poll > window: return False
        sleep(poll)

def main():
    destination = os.environ.get('FRESHNESS_HEARTBEAT_URL', '')
    if not destination:
        print('Freshness heartbeat not configured; no external monitor was signaled.')
        return
    expected = os.environ.get('EXPECTED_GENERATED_AT') or json.loads(Path('data/quotes.json').read_text())['generatedAt']
    quiet_reported = []
    def check(quotes, offers, at, exp):
        if not validate(quotes, offers, at, exp): return False
        local = quotes.get('sources', {}).get('isagha', {})
        if source_state(local, at) == 'quiet' and not quiet_reported:
            quiet_reported.append(True)
            print('::warning::Local source is quiet: last published price time '
                  + str(local.get('sourceTime'))
                  + '. Accepted under the 24-hour display rule as the last published price, not as a fresh quote.')
        return True
    if wait_for_publication(get_json, check, expected):
        ping(destination)
        print('Published primary quote freshness verified; external heartbeat accepted.')
        return
    print('Published freshness could not be proved within the 10 minute wall-clock limit; no success heartbeat sent.')
    raise SystemExit(1)

if __name__ == '__main__': main()
