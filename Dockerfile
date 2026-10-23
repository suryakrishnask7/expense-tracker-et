# Production Dockerfile for Expense Tracker ET
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    DATABASE_PATH=/app/data/expense_tracker.db

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure data directory exists for persistent SQLite database
RUN mkdir -p /app/data

# Expose HTTP port
EXPOSE 5000

# Container Healthcheck using Python's built-in urllib (no external curl/apt dependencies)
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1

# Launch production Gunicorn WSGI server
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "wsgi:application"]
