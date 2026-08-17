# Optional container path for the demo.
#
# NOTE: no job in .github/workflows/ci-cd.yml builds this image, so unlike the
# app code it is NOT covered by CI — it can rot without anything going red.
# Render deploys from source via the deploy hook and never reads this file.
# Add a `docker build` job if you want it actually verified.

FROM python:3.12-slim

WORKDIR /app

# Copy the requirements file on its own, before the source, so Docker caches the
# pip layer and reinstalls dependencies only when requirements.txt itself
# changes — not on every edit to main.py.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime dependencies only: pytest, httpx and ruff live in requirements-dev.txt
# and have no business in a production image.
#
# There is no .dockerignore, so this also copies tests/, .github/ and the README
# into the image. Harmless for a demo, wasteful for real work.
COPY . .

# 10000 is Render's default port and matches the start command in the README.
# Render injects the real port as $PORT; if you ever see it assign something
# else, switch to a shell-form CMD so ${PORT:-10000} gets expanded.
EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
