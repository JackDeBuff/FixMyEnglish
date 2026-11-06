"""LLM client: one chat-completion call per fix, strict-JSON output.

Tries the primary provider (the Duke AI Gateway by default) and, if it fails
for any reason, the optional fallback provider (FALLBACK_* env vars). Both
must be OpenAI-compatible.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass

from openai import OpenAI, Timeout

from .modes import style_card_for

log = logging.getLogger("uvicorn.error")


@dataclass
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str
    # Provider-specific request params, e.g. {"reasoning_effort": "low"} for
    # reasoning models whose default effort turns a 5-second fix into 30.
    extra_body: dict
    timeout: Timeout  # short connect timeout on the primary so a dead host fails fast
    _client: OpenAI | None = None
    # After a failure, skip this provider until this monotonic time (only
    # applied when a fallback exists), so a dead primary doesn't add its
    # timeout to every request.
    skip_until: float = 0.0

    def client(self) -> OpenAI:
        if self._client is None:
            # no SDK retries: a dead primary must fail fast so the fallback can answer
            self._client = OpenAI(
                base_url=self.base_url, api_key=self.api_key,
                timeout=self.timeout, max_retries=0,
            )
        return self._client


def _providers() -> list[Provider]:
    providers = []
    key = os.environ.get("DUKE_AI_GATEWAY_KEY")
    if key:
        providers.append(Provider(
            name="primary",
            base_url=os.environ.get("GATEWAY_BASE_URL", "https://litellm.oit.duke.edu/v1"),
            api_key=key,
            model=os.environ.get("MODEL_NAME", "gpt-6-luna"),
            extra_body=json.loads(os.environ.get("LLM_EXTRA_BODY") or "{}"),
            timeout=Timeout(30.0, connect=5.0),
        ))
    fb_key, fb_url = os.environ.get("FALLBACK_API_KEY"), os.environ.get("FALLBACK_BASE_URL")
    if fb_key and fb_url:
        providers.append(Provider(
            name="fallback",
            base_url=fb_url,
            api_key=fb_key,
            model=os.environ.get("FALLBACK_MODEL", ""),
            extra_body=json.loads(os.environ.get("FALLBACK_EXTRA_BODY") or "{}"),
            timeout=Timeout(60.0, connect=10.0),
        ))
    return providers


PROVIDERS = _providers()
PRIMARY_COOLDOWN_S = float(os.environ.get("PRIMARY_COOLDOWN_S", "600"))


SYSTEM_PROMPT = """You are FixMyEnglish, an expert editor who rewrites text into a target register of English.

{style_card}

Rules:
- Produce exactly 3 alternative rewrites of the user's text, ranked best-fit-first for the target register and the given context.
- The three versions must be meaningfully different (e.g. more/less rewritten, different phrasing choices), not near-duplicates.
- Preserve the meaning and intent of the original. Never add information the user didn't write.
- If the text is already perfect for the register, version 1 may equal the input — say so in its note.
- Each rewrite gets a one-line note (max 20 words) explaining why it fits the register.
- Notes are written to the user ("keeps your...", "sounds more...").

Respond with ONLY this JSON, no markdown fences, no extra keys:
{{"results": [{{"text": "...", "why": "..."}}, {{"text": "...", "why": "..."}}, {{"text": "...", "why": "..."}}]}}"""


def _parse(raw: str) -> list[dict[str, str]]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("model returned no JSON")
        data = json.loads(match.group(0))
    results = [
        {"text": str(r["text"]), "why": str(r.get("why", ""))}
        for r in data["results"]
        if r.get("text")
    ]
    if not results:
        raise ValueError("model returned empty results")
    return results[:3]


def fix_text(
    text: str, mode_id: str, custom_style: str | None, context: str | None
) -> tuple[list[dict[str, str]], str]:
    """Return the ranked rewrites and the name of the provider that served them."""
    user_msg = f"Text to fix:\n{text}"
    if context and context.strip():
        user_msg = f"Context (who/what this is for): {context.strip()}\n\n{user_msg}"

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(style_card=style_card_for(mode_id, custom_style)),
        },
        {"role": "user", "content": user_msg},
    ]
    if not PROVIDERS:
        raise RuntimeError("no LLM provider configured: set DUKE_AI_GATEWAY_KEY")

    last_error: Exception | None = None
    for i, provider in enumerate(PROVIDERS):
        is_last = i == len(PROVIDERS) - 1
        if not is_last and time.monotonic() < provider.skip_until:
            continue
        try:
            response = provider.client().chat.completions.create(
                model=provider.model,
                messages=messages,
                response_format={"type": "json_object"},
                extra_body=provider.extra_body or None,
            )
            results = _parse(response.choices[0].message.content or "")
            log.info("fix served by %s (%s)", provider.name, provider.model)
            return results, provider.name
        except Exception as e:  # noqa: BLE001 — any primary failure should try the fallback
            log.warning("%s provider failed (%s): %r", provider.name, provider.model, e)
            if not is_last:
                provider.skip_until = time.monotonic() + PRIMARY_COOLDOWN_S
            last_error = e
    raise last_error  # type: ignore[misc]
