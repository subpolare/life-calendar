FROM python:3.11-slim

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .
RUN chown -R app:app /app

USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s CMD pgrep -f bot.py || exit 1

CMD ["python", "bot.py"]
