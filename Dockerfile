FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

WORKDIR /app

# System deps required by Playwright Chromium and python-pptx/Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright Chromium runtime deps
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libxshmfence1 \
    # Fonts for slide rendering
    fonts-liberation fonts-noto-core fonts-inter \
    # Build tools for lxml/Pillow wheels
    gcc libxml2-dev libxslt1-dev zlib1g-dev libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Install Playwright Chromium into a fixed path
RUN python -m playwright install chromium && \
    python -m playwright install-deps chromium 2>/dev/null || true

# App code
COPY . .

# Output directory (mount a volume here to persist generated files)
RUN mkdir -p /app/output /app/.cache

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

CMD ["gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "600", \
     "--keep-alive", "65", \
     "app:app"]
