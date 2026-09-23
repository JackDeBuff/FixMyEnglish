# FixMyEnglish — CYBERSEC 590 Assignment 1

Paste English text → pick a register mode → one call to an OpenAI-compatible
LLM endpoint (Duke AI Gateway by design) → three ranked rewrites with why-notes
and copy buttons. Graded artifact for a Duke course (20 pts), **submitted
2026-08-27**; deployed live at fixmyenglish.supawich.workers.dev as a Cloudflare
Container running the same Dockerfile. [README.md](README.md) is the authority
on running/config; [assignment1.md](assignment1.md) is the rubric. Full
decision history: `~/.claude/plans/nevermind-i-have-my-bubbly-planet.md`.

## Where things stand (update this when it changes)

- **Assignment: submitted and graded-as-is.** Any change now is maintenance,
  not rubric work — keep the graded surface (lockfile, Dockerfile, app) stable.
- **Duke AI Gateway: unreachable from off-campus since the 2026-09-07 outage.**
  Dashboard works, keys regenerate fine, but `litellm.oit.duke.edu` TCP-times-
  out from home and from Cloudflare. Three fresh keys changed nothing — it is
  network reachability, not auth. OIT never posted a restoration notice.
- **Live demo runs on Cloudflare Workers AI** (`@cf/zai-org/glm-5.3-flash`)
  as a stand-in — details under Run / verify. Local dev still defaults to Duke.
- **Next step (planned 2026-09-24):** Jack tests the Gateway from campus Wi-Fi:
  `uv run python scripts/probe_gateway.py` — a `200` on campus but a timeout at
  home means the API is now Duke-network-only; a timeout on campus too means
  it is still down. Either way he then emails **aisuitesupport@duke.edu**
  (draft already given). Don't re-diagnose from scratch — run the probe.

## Standing rules (owner's instructions — do not drift)

- **No AI co-author trailers on commits. Ever.** No `Co-Authored-By: Claude`,
  no "Generated with Claude Code" lines. Jack documents the AI/human split
  himself in the README's **AI Assistance** section — leave that section to him.
- **The key never enters source or shell commands.** `DUKE_AI_GATEWAY_KEY`
  lives in `.env` (gitignored) locally and in Space secrets in production.
  Before any push: `git grep sk-` may match only the `.env.example`
  placeholder and this line — anything else is a leak. Don't paste the key
  into curl commands either — write a script that reads the env instead.
- **Casual/Gen Z modes must NOT "correct" texting style.** Lowercase,
  missing periods, abbreviations are the register, not errors — this is the
  owner's original spec and the app's whole point. Any prompt edit must keep it.
- **AAVE mode is expressive-but-authentic** (owner's spec, revised 2026-08-26:
  he asked for more colorful, bolder output). The hard lines that remain: no
  slurs ever (n-word in any form), no eye-dialect respellings, no minstrel
  phrasing — fluent-speaker-with-personality, not costume. LinkedIn mode is
  deliberately full satire (same-day decision); don't "professionalize" it back.

## Layout

One FastAPI app, no frameworks on the frontend:

| File | Job |
|---|---|
| `app/modes.py` | The 8 modes; each carries a `style_card` injected into the system prompt. Add a mode = add one entry here, nothing else. |
| `app/llm.py` | OpenAI client → `GATEWAY_BASE_URL` (default Duke `litellm.oit.duke.edu/v1`), strict-JSON prompt, fence-stripping parser. `MODEL_NAME` env (default `gpt-5.6-luna`); `LLM_EXTRA_BODY` JSON is merged into each request (used for `reasoning_effort`). Provider-agnostic on purpose. |
| `app/ratelimit.py` | In-memory per-IP 10/min + global 300/day. Public Space, metered key — that's why it exists. |
| `app/main.py` | Routes: `/` (static), `/api/modes`, `POST /api/fix`. Client IP = first hop of `x-forwarded-for` (HF proxy). |
| `app/static/index.html` | The whole UI, inline CSS/JS. Icons are inlined Lucide SVGs — no emoji as UI glyphs. |

## Run / verify

```bash
uv run uvicorn app.main:app --port 7860        # local
docker build -t fixmyenglish . && docker run --env-file .env -p 7860:7860 fixmyenglish
```

- `uv sync --frozen` must succeed on a clean machine — the lockfile is a
  5-point rubric line; commit `uv.lock` with any dependency change.
- The Dockerfile must keep working with plain `docker build` + `docker run`
  (another 5 points): port **7860**, non-root user (HF requirement),
  `.env` never baked into the image (`.dockerignore` handles it).
- Deploy = GitHub for the graded repo + **Cloudflare Containers** for the live
  demo (`cd cloudflare && npx wrangler deploy` — builds the same root
  Dockerfile; secret via `wrangler secret put`). HF Spaces was the original
  plan and is dead: Docker/Gradio Spaces on free CPU now require PRO (402) —
  the README documents this. Live URL: fixmyenglish.supawich.workers.dev.
- **Live demo provider (since 2026-09-23): Cloudflare Workers AI**, not Duke.
  Duke's LiteLLM host has been unreachable off-campus since the Sept 7 outage
  (dashboard works, API host TCP-times-out from home AND from Cloudflare).
  The switch is deploy-config only: `cloudflare/wrangler.jsonc` vars
  `GATEWAY_BASE_URL` (Workers AI OpenAI-compatible endpoint), `MODEL_NAME`
  (`@cf/zai-org/glm-5.3-flash`), `LLM_EXTRA_BODY` (`reasoning_effort: low` —
  without it a fix takes ~30s of thinking instead of 5-12s), plus Worker
  secret `LLM_API_KEY` (a Workers-AI-Read API token; the Worker maps it into
  the container's `DUKE_AI_GATEWAY_KEY`). Free tier: 10k Neurons/day ≈ 690
  fixes on this model; `DAILY_CAP=300` keeps it unbillable. To go back to
  Duke: delete the vars + secret, redeploy. Check the OIT alert page before
  re-diagnosing "gateway broken".
- **Never verify a workers.dev URL with curl from this sandbox** — the
  sandbox egress proxy sits on Cloudflare and every `*.workers.dev` request
  returns 404 `error code: 1042` regardless of the site's real state. Use the
  Browser pane. (Cost an hour and a false "your subdomain is broken" claim.)

## Gotchas already paid for

- The Duke Gateway model catalog + pricing lives at OIT KB0038832 (NetID
  login may be required). `gpt-5.6-luna` = $1/$6 per 1M tokens; a fix costs
  ~$0.003. `duke-current` is an alias that tracks a current model.
- `uv init --bare` created a virtual (non-package) project — `uv sync`
  installs only deps, which is why the Dockerfile can `CMD` the venv's
  uvicorn directly without installing the project itself.
- RTK hook rewrites some shell commands (`git status` → `rtk git status`);
  don't parse its output in pipes.
