"""Collection heartbeat, separate from source-price freshness and accuracy."""
import json
from datetime import datetime, timezone
from pathlib import Path


def receipt(previous, quotes, offers, now=None):
    now = now or datetime.now(timezone.utc)
    def age(stamp):
        try:
            t = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            if t.tzinfo is None:
                return None
            seconds = (now-t).total_seconds()
            return round(seconds, 1) if seconds >= -120 else None
        except (TypeError, ValueError, AttributeError):
            return None
    gap = age(previous)
    qage, oage = age(quotes.get('generatedAt')), age(offers.get('checkedAt') or offers.get('generatedAt'))
    return {'schemaVersion': 1, 'checkedAt': now.isoformat(), 'targetIntervalSeconds': 300,
            'schedulerGuarantee': False, 'previousCollectionTime': previous,
            'secondsSincePreviousCollection': gap,
            'missedTargetSincePrevious': gap is None or gap > 600,
            'quotesAgeSeconds': qage, 'offersAgeSeconds': oage,
            'status': 'recent' if all(v is not None and -120 <= v <= 600 for v in (qage,oage)) else 'delayed',
            'note': 'Collection receipt only; each source/product keeps its own pricing and check timestamps. GitHub scheduled starts may be delayed or dropped.'}


def main():
    root = Path(__file__).resolve().parent/'data'
    q = json.loads((root/'quotes.json').read_text())
    o = json.loads((root/'offers.json').read_text())
    previous = (root/'previous-collection-time.txt').read_text().strip() if (root/'previous-collection-time.txt').exists() else None
    out = receipt(previous, q, o)
    (root/'collection-health.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print({k:out[k] for k in ('status','secondsSincePreviousCollection','missedTargetSincePrevious')})


if __name__ == '__main__':
    main()
