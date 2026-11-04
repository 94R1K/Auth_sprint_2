FROM python:3.14.7-slim-trixie AS builder

WORKDIR /build

ARG POETRY_VERSION=2.5.1

ENV POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
    && python -m venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root


FROM python:3.14.7-slim-trixie

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WEB_CONCURRENCY=2

COPY --from=builder /opt/venv /opt/venv
COPY src/ /app/

RUN chmod +x /app/start.sh
ENTRYPOINT ["/app/start.sh"]

CMD ["gunicorn", "main:fastapi_app", \
     "--bind", "0.0.0.0:8000", \
     "--worker-class", "uvicorn_worker.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
