"""Duke AI Gateway client: one chat-completion call per fix, strict-JSON output."""

import json
import os
import re

from openai import OpenAI

from .modes import style_card_for

GATEWAY_BASE_URL = os.environ.get("GATEWAY_BASE_URL", "https://litellm.oit.duke.edu/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-5.6-luna")

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        key = os.environ.get("DUKE_AI_GATEWAY_KEY")
        if not key:
            raise RuntimeError("DUKE_AI_GATEWAY_KEY is not set")
        _client = OpenAI(base_url=GATEWAY_BASE_URL, api_key=key)
    return _client


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
) -> list[dict[str, str]]:
    user_msg = f"Text to fix:\n{text}"
    if context and context.strip():
        user_msg = f"Context (who/what this is for): {context.strip()}\n\n{user_msg}"

    response = client().chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    style_card=style_card_for(mode_id, custom_style)
                ),
            },
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        timeout=60,
    )
    return _parse(response.choices[0].message.content or "")
