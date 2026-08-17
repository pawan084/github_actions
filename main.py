"""FastAPI service for the GitHub Actions CI/CD demo.

The app is deliberately tiny so the interesting part of this repo stays the
pipeline in .github/workflows/ci-cd.yml rather than the application code:

    GET  /         a message you edit live to prove a deploy actually landed
    GET  /health   what the pipeline's smoke test polls after deploying
    POST /reverse  has real behaviour, so a test can meaningfully fail
"""

import os

from fastapi import FastAPI
from pydantic import BaseModel

# These are read from the environment of whatever runs the app — nothing in this
# repo sets them, so today they always read "dev" / "local", including on Render.
# Injecting the real commit as GIT_SHA is what would let /health identify which
# build is live, and in turn let the smoke test tell a fresh deploy from the
# previous one still serving traffic. See "Known gaps" in the README.
APP_VERSION = os.getenv("APP_VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "local")

app = FastAPI(title="FastAPI CI/CD Demo", version=APP_VERSION)


class ReverseRequest(BaseModel):
    # Required, with no default. That is what makes FastAPI reject a malformed
    # body with 422 instead of raising a 500, which test_reverse_rejects_bad_payload
    # pins down.
    text: str


class ReverseResponse(BaseModel):
    reversed: str


@app.get("/")
def root() -> dict[str, str]:
    # Demo beat 1 (green baseline): edit this string, push, and watch the new
    # text appear on the live URL once the deploy job finishes.
    return {"msg": "Deployed by GitHub Actions"}


@app.get("/health")
def health() -> dict[str, str]:
    # The workflow's smoke test polls this after triggering a deploy. Keep it
    # free of database or network calls so it can still answer while the rest
    # of the app is degraded — a health check that depends on everything else
    # tells you nothing useful when something breaks.
    return {"status": "ok", "version": APP_VERSION, "sha": GIT_SHA}


@app.post("/reverse", response_model=ReverseResponse)
def reverse(req: ReverseRequest) -> ReverseResponse:
    # Demo beat 2 (break it on purpose): change req.text[::-1] to req.text.
    # test_reverse_reverses_text then fails, the test job goes red, and the
    # deploy job is skipped by `needs: test` — that gate is the whole point
    # of the demo. The live site stays untouched.
    return ReverseResponse(reversed=req.text[::-1])
