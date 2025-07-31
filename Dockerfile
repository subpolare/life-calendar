FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Install system dependencies for Node canvas
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
    build-essential libcairo2-dev libjpeg-dev libpango1.0-dev libgif-dev librsvg2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python and Node dependencies
COPY requirements.txt package.json ./
RUN pip install --no-cache-dir -r requirements.txt && \
    npm install --production && \
    rm -rf /root/.npm

# Copy application files
COPY . .
RUN chown -R app:app /app

USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s CMD pgrep -f bot.py || exit 1

CMD ["python", "bot.py"]
