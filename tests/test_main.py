from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_returns_message():
    r = client.get("/")
    assert r.status_code == 200
    assert "msg" in r.json()


def test_health_is_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_reverse_reverses_text():
    r = client.post("/reverse", json={"text": "YouTube"})
    assert r.status_code == 200
    assert r.json()["reversed"] == "ebuTuoY"


def test_reverse_rejects_bad_payload():
    # This is the test to break on purpose during the demo.
    r = client.post("/reverse", json={"txt": "oops"})
    assert r.status_code == 422
