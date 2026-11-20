"""Optional free-tier Gold Timo cross-check. Never replaces dealer quotes.

GOLDTIMO_API_KEY stays server-side. Buy/sell fields retain provider names because
perspective has not yet been independently confirmed. History/snapshot are paid
and are deliberately never called by this adapter.
"""
import json
import math
import os
import urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

BASE = 'https://goldtimo.com/api/v1/price/XAU/EGP/'
KARATS = (24, 22, 21, 18)


def parse_price(raw, karat, now=None):
    now = now or datetime.now(timezone.utc)
    if raw.get('symbol') != 'XAU' or raw.get('currency') != 'EGP' or raw.get('karat') != karat or raw.get('unit') != 'oz':
        raise ValueError('identity_mismatch')
    for key in ('gram', 'gramBuy', 'gramSell', 'price'):
        v = raw.get(key)
        if type(v) not in (float, int) or not math.isfinite(v) or v <= 0:
            raise ValueError('invalid_price')
    stamp = datetime.fromisoformat(raw['updatedAt'].replace('Z', '+00:00'))
    if stamp.tzinfo is None or not -120 <= (now-stamp).total_seconds() <= 600:
        raise ValueError('invalid_or_old_timestamp')
    if not raw['gramSell'] <= raw['gram'] <= raw['gramBuy']:
        raise ValueError('invalid_provider_spread')
    return {k: raw[k] for k in ('symbol', 'currency', 'unit', 'karat', 'price', 'gram', 'gramBuy', 'gramSell', 'updatedAt')}


def crosscheck(key=None, opener=urllib.request.urlopen):
    key = key if key is not None else os.environ.get('GOLDTIMO_API_KEY', '')
    base = {'role': 'separate_local_reference_crosscheck_not_dealer_quote',
            'directionVerified': False, 'usedForPrimaryPrices': False,
            'sourceTimeKind': 'provider_reported_update_not_independently_verified',
            'documentation': 'https://goldtimo.com/eg/en/docs'}
    if not key:
        return dict(base, status='not_configured')
    def fetch(karat):
        try:
            req = urllib.request.Request(BASE+str(karat), headers={'x-api-key': key, 'User-Agent': 'GoldBoard/1.0'})
            with opener(req, timeout=15) as response:
                return str(karat), dict(parse_price(json.load(response), karat), status='available')
        except Exception:
            # Never persist exception text, request headers or credential-bearing URLs.
            return str(karat), {'status': 'unavailable', 'reason': 'crosscheck_failed'}
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = dict(pool.map(fetch, KARATS))
    return dict(base, status='available' if all(x['status']=='available' for x in values.values()) else 'incomplete',
                checkedAt=datetime.now(timezone.utc).isoformat(), karats=values)
