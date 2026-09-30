FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install dependencies first so this layer is cached when only source changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY main.py config.py db.py templates.py ratelimit.py ./
COPY templates ./templates
COPY static ./static
RUN uv sync --frozen --no-dev

RUN useradd --create-home appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    DATABASE_PATH=/data/contacts.db

EXPOSE 8008

CMD ["python", "main.py"]
