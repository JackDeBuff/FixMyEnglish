"""Is the LLM endpoint reachable with the key in .env? Prints statuses, never the key.

    uv run python scripts/probe_gateway.py            # default: Duke Gateway from .env
    GATEWAY_BASE_URL=... MODEL_NAME=... uv run python scripts/probe_gateway.py
"""

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()
KEY = os.environ.get("DUKE_AI_GATEWAY_KEY", "")
BASE = os.environ.get("GATEWAY_BASE_URL", "https://litellm.oit.duke.edu/v1")
MODEL = os.environ.get("MODEL_NAME", "gpt-5.6-luna")


def call(path: str, body: dict | None = None) -> tuple[int, str]:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST" if body else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:  # noqa: BLE001 — we want the raw failure mode printed
        return -1, repr(e)


print(f"endpoint: {BASE}  key: {'loaded' if KEY else 'MISSING'} ({len(KEY)} chars)")
status, body = call("/models")
print(f"GET /models -> {status}", f"({len(json.loads(body)['data'])} models)" if status == 200 else body)
status, body = call("/chat/completions", {"model": MODEL, "messages": [{"role": "user", "content": "Say OK."}], "max_tokens": 5})
print(f"POST chat/completions ({MODEL}) -> {status}", json.loads(body)["choices"][0]["message"]["content"] if status == 200 else body)
