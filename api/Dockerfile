# syntax=docker/dockerfile:1
# install dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
# Install into an isolated prefix so we can copy only the result
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# lean runtime image
FROM python:3.11-slim
WORKDIR /app

# Non-root user (FIX: security requirement)
RUN addgroup --system app && adduser --system --ingroup app --no-create-home app

# Copy installed packages from builder — no pip/build tools in final image
COPY --from=builder /install /usr/local

# Copy only application source — never copy .env files
COPY main.py .

RUN chown -R app:app /app
USER app

EXPOSE 8000

# Health check hits the /health endpoint added in FIX-05
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
