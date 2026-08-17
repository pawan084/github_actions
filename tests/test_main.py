"""Tests for main.py — four small cases, each tied to a beat of the demo.

Import note: `from main import app` below resolves only because pyproject.toml
sets pythonpath = ["."]. Without that, the `pytest` console script puts tests/
on sys.path but *not* the project root, and collection dies with
`ModuleNotFoundError: No module named 'main'`. This is the single most common
way a green-looking FastAPI repo fails on its first CI run.
"""

from fastapi.testclient import TestClient

from main import app

# Built once at import time — safe here because the app keeps no state between
# requests, so tests cannot leak into each other. TestClient is backed by httpx,
# which is why httpx sits in requirements-dev.txt; installing only
# requirements.txt makes this line raise at import.
client = TestClient(app)


def test_root_returns_message():
    # Asserts the *shape* of the response, not the text, so editing the message
    # during demo beat 1 does not fail the suite. Breaking a test on purpose is
    # beat 2's job, and it should be the only thing that goes red.
    r = client.get("/")
    assert r.status_code == 200
    assert "msg" in r.json()


def test_health_is_ok():
    # The workflow's smoke test depends on this endpoint answering 200 with
    # status "ok", so a change that breaks the contract fails here in CI rather
    # than after deploying.
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_reverse_reverses_text():
    # Demo beat 2 breaks this one: swap req.text[::-1] for req.text in main.py
    # and this assertion fails with "YouTube" != "ebuTuoY", taking the deploy
    # job down with it.
    r = client.post("/reverse", json={"text": "YouTube"})
    assert r.status_code == 200
    assert r.json()["reversed"] == "ebuTuoY"


def test_reverse_rejects_bad_payload():
    # "txt" instead of "text": the required field is missing, so pydantic
    # rejects the body before the handler runs. Asserting 422 (not 500) proves
    # the validation layer is doing the work, not an unhandled exception.
    r = client.post("/reverse", json={"txt": "oops"})
    assert r.status_code == 422
