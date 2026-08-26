"""In-memory abuse protection for a public Space fronting a metered API key:
a per-IP sliding-window limit plus a global rolling daily cap."""

import os
import time
from collections import defaultdict, deque

RATE_LIMIT_PER_MIN = int(os.environ.get("RATE_LIMIT_PER_MIN", "10"))
DAILY_CAP = int(os.environ.get("DAILY_CAP", "300"))

_per_ip: dict[str, deque[float]] = defaultdict(deque)
_global: deque[float] = deque()


def _prune(window: deque[float], horizon: float) -> None:
    now = time.monotonic()
    while window and now - window[0] > horizon:
        window.popleft()


def check(ip: str) -> str | None:
    """Return an error message if this request should be refused, else None."""
    _prune(_global, 86400)
    if len(_global) >= DAILY_CAP:
        return (
            "FixMyEnglish has hit its daily usage cap (it runs on a student's "
            "API budget). Please come back tomorrow!"
        )
    bucket = _per_ip[ip]
    _prune(bucket, 60)
    if len(bucket) >= RATE_LIMIT_PER_MIN:
        return "Whoa, slow down — you can fix up to %d texts per minute. Give it a few seconds." % RATE_LIMIT_PER_MIN
    now = time.monotonic()
    bucket.append(now)
    _global.append(now)
    # keep the per-IP table from growing unboundedly
    if len(_per_ip) > 10000:
        for key in [k for k, v in _per_ip.items() if not v]:
            del _per_ip[key]
    return None
