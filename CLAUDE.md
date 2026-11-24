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
- **Duke AI Gateway: down again as of 2026-11-24**, from home Wi-Fi too (TCP
  timeout, WARP off), while status.oit.duke.edu says "operational", the same
  mismatch as September. Even when it's up, it times out from Cloudflare's
  server network (Worker fetch got 522, 2026-11-06), so the live demo can't use
  it either way. Local/Docker runs are broken until Duke is back; no code fix.
- **The app is Duke-first with a fallback** (`app/llm.py`, 2026-11-06): primary
  = Duke (`gpt-6-luna`, 5s connect timeout, no retries); on any failure it tries
  `FALLBACK_*` and skips Duke for `PRIMARY_COOLDOWN_S` (600s). The API response
  carries `"provider"`.
- **Live demo fallback = Workers AI `@cf/zai-org/glm-5.3` via a Worker relay**
  (2026-11-24). Root cause that day, confirmed in the container logs
  (dashboard → Containers → app → Logs): Workers AI returned **410 "Model has
  been deprecated: glm-5.3-flash was deprecated on 2026-11-20"**. The container's
  network was fine. I first misread instant failures as "container egress is
  broken"; those were requests still served by the **old instance** during a
  rollout (stale env). The relay was built on that wrong theory, but it's kept
  because it works and is safer: the container calls `http://fallback.relay`,
  and the Worker's `outboundByHost` forwards to `FALLBACK_BASE_URL` with the
  real key (needs `@cloudflare/containers` ≥0.3 and `export { ContainerProxy }`),
  so the Workers AI key never enters the container. Owner uses it ~5–6×/day;
  `DAILY_CAP=30` keeps a full capped day inside the free 10k Neurons (glm-5.3 ≈
  130–300 Neurons per fix). Owner's rule: best model that costs $0.
- **Diagnose the live demo from the container logs first.** The Cloudflare
  dashboard has them (Containers → fixmyenglish-fixmyenglishcontainer → Logs;
  filter message "provider failed"). Jack has to be signed in to Cloudflare in
  Chrome. Before trusting any live test after a deploy, confirm the instance's
  CREATED time is newer than the deploy.

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
| `app/llm.py` | Primary provider (`GATEWAY_BASE_URL`, default Duke; `MODEL_NAME`, default `gpt-6-luna`) then optional fallback (`FALLBACK_*`), with a cooldown on primary failure. Strict-JSON prompt, fence-stripping parser. `LLM_EXTRA_BODY` / `FALLBACK_EXTRA_BODY` are JSON merged into requests (used for `reasoning_effort`). `fix_text` returns `(results, provider_name)`. |
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
- **Live demo config:** `cloudflare/wrangler.jsonc` vars `FALLBACK_BASE_URL`
  (Workers AI OpenAI-compatible endpoint, used by the Worker relay only),
  `FALLBACK_MODEL` (`@cf/zai-org/glm-5.3`), `FALLBACK_EXTRA_BODY`
  (`reasoning_effort: low`), `DAILY_CAP` (`30`), plus Worker secrets
  `DUKE_AI_GATEWAY_KEY` and `FALLBACK_API_KEY` (Cloudflare token
  `fixmyenglish-workers-ai`, Workers-AI-Read, rolled 2026-11-06). Workers AI
  retires models: if the live demo 502s in under a second, run
  `npx wrangler ai models | grep <model>` before anything else.
- **A deploy that only changes the Worker does not restart the running
  container**, so the container keeps its old env vars and its in-memory Duke
  cooldown. To force a fresh instance, change container config (e.g. flip
  `max_instances`) or the image. Check with `npx wrangler containers instances
  <app-id>`: look at the CREATED column.
- **Container stdout doesn't show up in `wrangler tail`**; only Worker logs do.
  To see which provider served a live request, read `"provider"` in the
  `/api/fix` response.
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
