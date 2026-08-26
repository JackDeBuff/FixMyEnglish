---
title: FixMyEnglish
emoji: ✨
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# FixMyEnglish

Paste any English text, pick the register you need, and get **three ranked
rewrites** — each with a one-line note on why it fits — plus one-click copy.

Because "correct English" depends on where you're typing. A LinkedIn post, an
IELTS essay, and a 2 a.m. group-chat message are all English, and fixing them
all the same way is itself a mistake: in a casual text, adding capital letters
and full stops makes it *worse*. FixMyEnglish knows the difference.

**Modes:** Casual (default) · LinkedIn · IELTS Band 9 · Gen Z · Professional ·
Black English (AAVE) · Academic · Custom (describe your own target style).
An optional context field ("replying to my landlord about a broken heater")
steers all three versions.

Built for **CYBERSEC 590, Assignment 1** at Duke. One model call per fix
through the [Duke AI Gateway](https://oit.duke.edu/service/ai-gateway/)
(OpenAI-compatible), default model `gpt-5.6-luna`.

## Run it

Local (needs [uv](https://docs.astral.sh/uv/)):

```bash
cp .env.example .env   # put your real Duke AI Gateway key in it
uv sync
uv run uvicorn app.main:app --port 7860
```

Docker:

```bash
docker build -t fixmyenglish .
docker run --env-file .env -p 7860:7860 fixmyenglish
```

Then open <http://localhost:7860>.

## Configuration — environment only

No secrets in source. Locally they come from `.env` (gitignored); on the
Hugging Face Space, from Space secrets.

| Variable | Default | Purpose |
|---|---|---|
| `DUKE_AI_GATEWAY_KEY` | — (required) | API key from the Duke AI Dashboard |
| `MODEL_NAME` | `gpt-5.6-luna` | Any model the Gateway serves |
| `GATEWAY_BASE_URL` | `https://litellm.oit.duke.edu/v1` | OpenAI-compatible endpoint |
| `RATE_LIMIT_PER_MIN` | `10` | Per-IP sliding-window limit |
| `DAILY_CAP` | `300` | Global rolling-24h request cap |
| `MAX_INPUT_CHARS` | `1000` | Input length limit |

The rate limit and daily cap exist because this is a public app fronting a
metered key — a small abuse-protection layer suited to a security course.

## How it works

`app/static/index.html` (vanilla HTML/CSS/JS, no frameworks) → `POST /api/fix`
→ [app/main.py](app/main.py) validates + rate-limits ([app/ratelimit.py](app/ratelimit.py))
→ [app/llm.py](app/llm.py) makes one chat-completion call with a mode-specific
"style card" from [app/modes.py](app/modes.py) and strict-JSON output
→ three ranked results render as cards.

## AI Assistance

<!-- Written by me (Jack), per the course citation policy: tool, model,
     timestamp, what the AI did, and what I did/decided. -->
