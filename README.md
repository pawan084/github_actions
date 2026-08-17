# FastAPI CI/CD Demo — GitHub Actions

[![CI/CD](https://github.com/pawan084/github_actions/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/pawan084/github_actions/actions/workflows/ci-cd.yml)

A minimal FastAPI service with a real pipeline: **lint → test (matrix) → deploy → smoke test**.
Tests gate the deploy, so a broken commit never reaches production.

Repo: <https://github.com/pawan084/github_actions>

## Run it locally

```bash
git clone git@github.com:pawan084/github_actions.git
cd github_actions
pip install -r requirements-dev.txt
pytest -q                      # 4 passed
ruff check .                   # what CI lints with
uvicorn main:app --reload      # http://localhost:8000/docs
```

## Setup (10 minutes)

Already wired up in this repo — these are the steps if you are rebuilding it
somewhere else:

```bash
git init && git add . && git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<you>/<your-repo>.git
git push -u origin main
```

> **Keep the app at the repository root.** GitHub only reads workflows from
> `.github/workflows/` at the *root* — nest the project one directory deeper and
> the pipeline silently never runs, with an empty Actions tab as the only clue.
> If you must keep it in a subdirectory, move the workflow to the root and add a
> `defaults.run.working-directory` block plus a `cache-dependency-path`.

### Deploy target (Render, free tier)

1. render.com → **New + → Web Service** → connect the repo
2. Build: `pip install -r requirements.txt`
   Start: `uvicorn main:app --host 0.0.0.0 --port 10000`
3. Service → **Settings → Deploy Hooks** → copy the URL

### Wire it into GitHub

| Where | Name | Value |
|---|---|---|
| Settings → Secrets and variables → Actions → **Secrets** | `RENDER_DEPLOY_HOOK` | the Render hook URL |
| Settings → Secrets and variables → Actions → **Variables** | `APP_URL` | `https://<your-app>.onrender.com` |

Both are optional. Without `RENDER_DEPLOY_HOOK` the deploy job still **runs and
succeeds** — only its hook *step* exits early with a warning annotation, so the
run stays green for a pure-CI demo. (Don't confuse that with the *skipped* deploy
job in beat 2 below; a skipped job is what a failing test produces.) Without
`APP_URL` the smoke-test step is skipped by its `if:` condition.

For the manual-approval beat: Settings → **Environments** → `production` →
add yourself as a required reviewer. The deploy job then pauses until approved.

## Demo script

1. **Green baseline.** Push a trivial change to the message in `main.py`.
   Show the Actions tab: two Python versions run in parallel, then deploy fires.
   Refresh the live URL — new text.
2. **Break it on purpose.** Change `req.text[::-1]` to `req.text` and push.
   `test_reverse_reverses_text` fails → deploy job shows as *skipped*, not run.
   Live site is untouched. This is the point of the whole demo.
3. **Fix forward.** Revert, push, watch it go green and redeploy.
4. **Pull request flow.** Open a PR from a branch: tests run, deploy does not
   (guarded by `if: github.event_name == 'push'`).
5. **Extras if you have time:** the job summary, the uploaded `results.xml`
   artifact, `concurrency` cancelling a superseded run, and the `/health`
   smoke test catching a bad deploy.

## Files

```
main.py                       app (3 endpoints)
tests/test_main.py            4 tests
requirements.txt              runtime deps, pinned
requirements-dev.txt          + pytest, httpx, ruff
pyproject.toml                pytest config (puts the root on sys.path)
Dockerfile                    optional container path
.github/workflows/ci-cd.yml   the pipeline
```

## Notes on the workflow

- `needs: test` is the gate. Without it you have CD, not CI/CD.
- `concurrency` cancels superseded runs so rapid demo pushes don't queue up.
- Actions are pinned to major tags (`@v4`, `@v5`); pin to SHAs for real work.
- Deploy hooks are fire-and-forget — the hook returns 200 before the build
  finishes, which is why the smoke-test loop polls `/health`.
- `pyproject.toml` sets `pythonpath = ["."]`. Drop it and CI fails on the first
  run: the `pytest` console script puts `tests/` on `sys.path` but not the
  project root, so `from main import app` raises `ModuleNotFoundError`.
- CI installs `requirements-dev.txt`, not `requirements.txt`. `TestClient` is
  backed by `httpx`, which is a dev dependency — install only the runtime file
  and collection fails before a single test runs.

## Known gaps

Deliberately left in, and worth saying out loud if you present this:

- **The smoke test can report a false green.** The old version keeps serving
  `/health` while Render builds, so the first poll may succeed against the
  *previous* deploy. Fixing it properly means asserting `/health`'s `sha`
  equals `github.sha` — which needs the next item first.
- **`APP_VERSION` / `GIT_SHA` are never injected.** `main.py` reads them, but
  nothing sets them, so `/health` always reports `dev` / `local`.
- **A skipped deploy still gets a green smoke test.** If the hook secret is
  missing, the deploy step exits early but the smoke test still health-checks
  the untouched live app, and the summary claims a deploy that never happened.
- **No `permissions:` block**, so `GITHUB_TOKEN` inherits the repository
  default. `permissions: contents: read` at the top level is the least-privilege
  setting for this pipeline.
- **The Dockerfile is never built by CI**, so it can rot without anything going
  red. There's also no `.dockerignore`, and the container runs as root.
