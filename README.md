# FixMyEnglish

**Live demo:** <https://fixmyenglish.supawich.workers.dev>
*(if that URL shows "There is nothing here yet", Cloudflare is still
propagating the hostname — run it locally or with Docker below instead)*

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

No secrets in source. Locally they come from `.env` (gitignored); in the live
deployment, from a Cloudflare Worker secret passed into the container's env.

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

## Deployment — and why it's not a Hugging Face Space

The original plan was a Hugging Face **Docker Space** — same Dockerfile for
grading and hosting. That plan died on contact with reality: as of August 2026,
HF returns `402 Payment Required` on Space creation —

> "Static Spaces are free for everyone, but hosting Gradio and Docker Spaces
> on free cpu-basic requires a PRO subscription."

So the free tier that made Spaces the course-friendly default no longer covers
app Spaces at all. Instead, the live demo runs the **same unmodified
Dockerfile** on [Cloudflare Containers](https://developers.cloudflare.com/containers/):
a tiny Worker ([cloudflare/src/index.ts](cloudflare/src/index.ts)) routes
requests to one container instance, `DUKE_AI_GATEWAY_KEY` lives in a Worker
secret, and the container scales to zero when idle. Deploy is
`npx wrangler deploy` from [cloudflare/](cloudflare/).

## How it works

`app/static/index.html` (vanilla HTML/CSS/JS, no frameworks) → `POST /api/fix`
→ [app/main.py](app/main.py) validates + rate-limits ([app/ratelimit.py](app/ratelimit.py))
→ [app/llm.py](app/llm.py) makes one chat-completion call with a mode-specific
"style card" from [app/modes.py](app/modes.py) and strict-JSON output
→ three ranked results render as cards.

## AI Assistance

<!-- Written by me (Jack), per the course citation policy: tool, model,
     timestamp, what the AI did, and what I did/decided. -->
