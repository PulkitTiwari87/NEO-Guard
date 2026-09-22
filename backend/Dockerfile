# NEO-Guard backend image. Build context is the REPOSITORY ROOT (the API imports the `ml` package):
#   docker build -f backend/Dockerfile -t neoguard-backend .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY ml ml
COPY backend backend
COPY docs/EXPERIMENTS.md docs/EXPERIMENTS.md

# Model artifacts (*.joblib) are git-ignored (see .gitignore) and not committed, so train
# fresh at build time instead (Phase 6 deployment decision, docs/DEPLOYMENT.md). Needs network
# access to the NASA/JPL APIs during the build. Clears the tracked metadata-only version dirs
# first (their model.joblib was never committed) so version numbering starts clean and every
# listed artifact is actually loadable.
RUN rm -rf ml/artifacts/*/v* \
    && python -m ml.ingestion \
    && python -m ml.validation \
    && python -m ml.preprocessing \
    && python -m ml.training \
    && python -m ml.evaluation \
    && python -m ml.explainability

# Non-root runtime user.
RUN useradd --system --no-create-home --uid 10001 neoguard
USER neoguard

WORKDIR /app/backend
EXPOSE 8000

# Real dependency check: /api/health returns 503 when the database is unreachable.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

# Run `alembic upgrade head` (see docker-compose.yml `migrate`) before serving.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
