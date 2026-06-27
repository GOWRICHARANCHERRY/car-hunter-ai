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

RUN apt-get update && \
    DEBIAN_VERSION=$(cat /etc/debian_version 2>/dev/null || echo "unknown") && \
    echo "Debian version: $DEBIAN_VERSION" && \
    if echo "$DEBIAN_VERSION" | grep -q "^13\|^trixie" || [ "$(cat /etc/os-release 2>/dev/null | grep VERSION_CODENAME | cut -d= -f2)" = "trixie" ]; then \
        SUFFIX="t64"; \
    else \
        SUFFIX=""; \
    fi && \
    apt-get install -y --no-install-recommends \
    ca-certificates libnss3 libnspr4 \
    libatk1.0-0${SUFFIX} libatk-bridge2.0-0${SUFFIX} \
    libcups2${SUFFIX} libdrm2 libdbus-1-3 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 \
    libasound2${SUFFIX} libatspi2.0-0${SUFFIX} \
    libxshmfence1 libglib2.0-0${SUFFIX} \
    libx11-xcb1 libxcb1 libxext6 libxfixes3 libxi6 libxrender1 \
    libgdk-pixbuf-2.0-0 xdg-utils \
    fonts-liberation fonts-noto-color-emoji fonts-unifont fonts-ubuntu && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
