FROM python:3.13-slim AS python-base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM python-base AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv venv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --no-dev
COPY README.md ./
COPY tickets/ ./tickets/
RUN uv pip install --no-deps .

FROM builder AS migrate
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"
CMD ["python", "-m", "tickets", "migrate", "--noinput"]

FROM builder AS testing
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"
RUN uv sync --no-install-project --group test
COPY tests/ ./tests/
COPY deployment/docker/run-tests.sh ./run-tests.sh
RUN sed -i 's/\r$//' ./run-tests.sh && chmod +x ./run-tests.sh
CMD ["sh", "-c", "python -m tickets migrate --noinput && ./run-tests.sh"]

FROM python-base AS runtime

RUN apt-get update && apt-get install -y curl

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"
COPY deployment/docker/docker-entrypoint.sh ./docker-entrypoint.sh
RUN sed -i 's/\r$//' ./docker-entrypoint.sh && chmod +x ./docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "tickets", "runserver", "0.0.0.0:8000"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=2s --start-interval=2s --retries=10 \
  CMD curl -f http://localhost:8000/health/ || exit 1

