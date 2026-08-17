import os

from fastapi import FastAPI
from pydantic import BaseModel

APP_VERSION = os.getenv("APP_VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "local")

app = FastAPI(title="FastAPI CI/CD Demo", version=APP_VERSION)


class ReverseRequest(BaseModel):
    text: str


class ReverseResponse(BaseModel):
    reversed: str


@app.get("/")
def root() -> dict[str, str]:
    # Change this string live during the demo to prove the pipeline works.
    return {"msg": "Deployed by GitHub Actions"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION, "sha": GIT_SHA}


@app.post("/reverse", response_model=ReverseResponse)
def reverse(req: ReverseRequest) -> ReverseResponse:
    return ReverseResponse(reversed=req.text[::-1])
