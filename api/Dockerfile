FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.11-alpine AS builder

RUN apk update && apk upgrade && rm -rf /var/cache/apk/*
RUN apk add build-base

ENV UV_LINK_MODE=copy

RUN --mount=from=uv,source=/uv,target=/opt/uv \
    /opt/uv venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=from=uv,source=/uv,target=/opt/uv \
    /opt/uv pip install -r pyproject.toml

FROM python:3.11-alpine AS final

WORKDIR /app

COPY . /app

COPY --from=builder /opt/venv /opt/venv

RUN --mount=from=uv,source=/uv,target=/tmp/uv \
    cp /tmp/uv /opt/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PATH="/opt/uv:$PATH"

EXPOSE 1338

CMD ["/opt/venv/bin/python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "1338", "--loop", "asyncio"]