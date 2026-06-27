FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install playwright && \
    playwright install chromium

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

RUN PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright playwright install-deps chromium && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
