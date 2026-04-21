# syntax=docker/dockerfile:1
# install dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# lean runtime image
FROM python:3.11-slim
WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app --no-create-home app

COPY --from=builder /install /usr/local
COPY worker.py .

RUN chown -R app:app /app
USER app

# Health check: confirm the python process is alive
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD pgrep -f "python worker.py" > /dev/null || exit 1

CMD ["python", "worker.py"]
