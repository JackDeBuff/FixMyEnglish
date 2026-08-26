# FixMyEnglish — CYBERSEC 590 Assignment 1

Paste English text → pick a register mode → one call to the Duke AI Gateway →
three ranked rewrites with why-notes and copy buttons. Graded artifact for a
Duke course (20 pts); also deployed live as a Hugging Face **Docker** Space.
[README.md](README.md) is the authority on running/config;
[assignment1.md](assignment1.md) is the rubric. Full decision history:
`~/.claude/plans/nevermind-i-have-my-bubbly-planet.md`.

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
- **AAVE mode is authentic-or-nothing.** It's a rule-governed variety; wording
  in `modes.py` was chosen to avoid caricature. Don't loosen it.

## Layout

One FastAPI app, no frameworks on the frontend:

| File | Job |
|---|---|
| `app/modes.py` | The 8 modes; each carries a `style_card` injected into the system prompt. Add a mode = add one entry here, nothing else. |
| `app/llm.py` | OpenAI client → `https://litellm.oit.duke.edu/v1`, strict-JSON prompt, fence-stripping parser. Model = `MODEL_NAME` env (default `gpt-5.6-luna`). |
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
- Deploy = push this same repo to both GitHub and the HF Space git remote.
  The README frontmatter (`sdk: docker`, `app_port: 7860`) **is** the Space
  config — don't strip it for GitHub aesthetics.

## Gotchas already paid for

- The Duke Gateway model catalog + pricing lives at OIT KB0038832 (NetID
  login may be required). `gpt-5.6-luna` = $1/$6 per 1M tokens; a fix costs
  ~$0.003. `duke-current` is an alias that tracks a current model.
- `uv init --bare` created a virtual (non-package) project — `uv sync`
  installs only deps, which is why the Dockerfile can `CMD` the venv's
  uvicorn directly without installing the project itself.
- RTK hook rewrites some shell commands (`git status` → `rtk git status`);
  don't parse its output in pipes.
