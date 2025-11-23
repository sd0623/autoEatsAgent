# Use official lightweight Python image
FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install build dependencies and cleanup to keep image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for efficient caching
COPY requirements.txt /app/requirements.txt

# Install Python deps
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Use a non-root user (optional but good practice)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run uses port 8080 by convention
ENV PORT=8080

# Expose port
EXPOSE 8080

# Start the app with uvicorn. Use shell form so ${PORT} expands.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
