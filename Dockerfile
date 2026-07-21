FROM ghcr.io/astral-sh/uv:0.11.30-python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --locked \
    --no-install-project

COPY . .

RUN uv sync --locked

RUN useradd \
        --create-home \
        --uid 10001 \
        appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["sh", "-c", "uv run alembic upgrade head && exec uv run python main.py"]