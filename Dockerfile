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

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libnss3 libnspr4 libdrm2 libdbus-1-3 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libxshmfence1 \
    libx11-xcb1 libxcb1 libxext6 libxfixes3 libxi6 libxrender1 \
    libgdk-pixbuf-2.0-0 xdg-utils \
    fonts-liberation fonts-noto-color-emoji fonts-unifont \
    libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 \
    libasound2t64 libatspi2.0-0t64 && \
    ldconfig && \
    python3 -c "
import ctypes, ctypes.util
for lib in ['glib-2.0', 'gobject-2.0', 'atk-1.0', 'atk-bridge-2.0', \
            'cups', 'asound', 'atspi', 'X11', 'xcb', 'Xcomposite', \
            'Xdamage', 'Xrandr', 'gbm', 'pango-1.0', 'cairo', \
            'nspr4', 'nss3', 'dbus-1', 'xkbcommon', 'Xext', \
            'Xfixes', 'Xi', 'Xrender', 'gdk_pixbuf-2.0', 'xshmfence']:
    path = ctypes.util.find_library(lib)
    status = 'OK' if path else 'MISSING'
    if status == 'MISSING':
        print(f'  {status}: lib{lib}.so')
" && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
