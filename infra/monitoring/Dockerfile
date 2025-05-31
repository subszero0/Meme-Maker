FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the exporter script
COPY s3_metrics_exporter.py .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash exporter
USER exporter

# Expose metrics port
EXPOSE 9100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9100/health')" || exit 1

# Set default environment variables
ENV EXPORTER_PORT=9100
ENV SCRAPE_INTERVAL=300
ENV AWS_REGION=us-east-1

# Run the exporter
CMD ["python", "s3_metrics_exporter.py"] 