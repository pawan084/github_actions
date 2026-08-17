# FastAPI CI/CD Demo — GitHub Actions

A minimal FastAPI service with a real pipeline: **lint → test (matrix) → deploy → smoke test**.
Tests gate the deploy, so a broken commit never reaches production.

## Setup (10 minutes)

```bash
git init && git add . && git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<you>/fastapi-cicd-demo.git
git push -u origin main
```

Run locally first:

```bash
pip install -r requirements-dev.txt
pytest -q
uvicorn main:app --reload      # http://localhost:8000/docs
```

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

Both are optional — without them the deploy job logs a warning and skips, so the
workflow still runs green for a pure-CI demo.

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
