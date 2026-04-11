# Dockerfile
# Copyright @YourChannel
# ─────────────────────────────────────────────────────────────
# Build:  docker build -t course_bot .
# Run:    docker run --env-file .env course_bot
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libssl-dev \
        && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies first (layer cache) ──────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ────────────────────────────────────────
COPY . .

# ── Non-root user for security ────────────────────────────────
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# ── Start the bot ─────────────────────────────────────────────
CMD ["python", "main.py"]
