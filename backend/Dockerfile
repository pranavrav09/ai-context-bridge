FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt greenlet

# Copy application
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY docker-entrypoint.sh .

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Expose port (Cloud Run will set $PORT)
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
