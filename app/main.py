"""FixMyEnglish — FastAPI app: static UI + one fix endpoint."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # local dev; on HF Spaces the env comes from Space secrets

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import llm, ratelimit  # noqa: E402
from .modes import MODES  # noqa: E402

MAX_INPUT_CHARS = int(os.environ.get("MAX_INPUT_CHARS", "1000"))

log = logging.getLogger("uvicorn.error")
app = FastAPI(title="FixMyEnglish", docs_url=None, redoc_url=None)
STATIC = Path(__file__).parent / "static"


class FixRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_INPUT_CHARS)
    mode: str
    custom_style: str | None = Field(default=None, max_length=120)
    context: str | None = Field(default=None, max_length=200)


def _client_ip(request: Request) -> str:
    # HF Spaces sits behind a proxy; first hop of x-forwarded-for is the client
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/modes")
def modes() -> list[dict[str, str]]:
    return [{"id": m.id, "label": m.label, "blurb": m.blurb} for m in MODES.values()]


@app.post("/api/fix")
def fix(body: FixRequest, request: Request) -> JSONResponse:
    if body.mode not in MODES:
        return JSONResponse({"error": "Unknown mode."}, status_code=400)
    if body.mode == "custom" and not (body.custom_style or "").strip():
        return JSONResponse(
            {"error": "Describe your custom style first."}, status_code=400
        )

    refusal = ratelimit.check(_client_ip(request))
    if refusal:
        return JSONResponse({"error": refusal}, status_code=429)

    try:
        results = llm.fix_text(body.text, body.mode, body.custom_style, body.context)
    except Exception:
        log.exception("fix failed")
        return JSONResponse(
            {"error": "The model call failed — please try again in a moment."},
            status_code=502,
        )
    return JSONResponse({"results": results})
