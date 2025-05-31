#!/usr/bin/env python3
"""
S3 Metrics Exporter for Prometheus

Fetches S3 CloudWatch metrics and exposes them as Prometheus gauges:
- S3_STORAGE_BYTES: Current bucket size in bytes
- S3_EGRESS_BYTES: Monthly egress (downloaded bytes)

Usage:
    python s3_metrics_exporter.py

Environment Variables:
    AWS_REGION: AWS region (default: us-east-1)
    AWS_ACCESS_KEY_ID: AWS access key
    AWS_SECRET_ACCESS_KEY: AWS secret key
    S3_BUCKET: S3 bucket name to monitor
    ENV: Environment name (dev/staging/prod)
    EXPORTER_PORT: Port to serve metrics on (default: 9100)
    SCRAPE_INTERVAL: How often to fetch CloudWatch metrics in seconds (default: 300)
"""

import os
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from prometheus_client import Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'clips')
ENV = os.getenv('ENV', 'dev')
EXPORTER_PORT = int(os.getenv('EXPORTER_PORT', '9100'))
SCRAPE_INTERVAL = int(os.getenv('SCRAPE_INTERVAL', '300'))  # 5 minutes

# AWS endpoint URL for local development (MinIO)
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL')

# Prometheus metrics
registry = CollectorRegistry()

# S3 storage bytes gauge (current bucket size)
s3_storage_bytes = Gauge(
    'S3_STORAGE_BYTES',
    'S3 bucket storage size in bytes',
    ['bucket', 'env'],
    registry=registry
)

# S3 egress bytes gauge (monthly download total)
s3_egress_bytes = Gauge(
    'S3_EGRESS_BYTES',
    'S3 bucket egress (downloaded bytes) over the last 30 days',
    ['bucket', 'env'],
    registry=registry
)

# Metric collection status
metrics_last_updated = Gauge(
    'S3_METRICS_LAST_UPDATED_TIMESTAMP',
    'Unix timestamp when S3 metrics were last successfully updated',
    ['bucket', 'env'],
    registry=registry
)

# Error tracking
metrics_collection_errors = Gauge(
    'S3_METRICS_COLLECTION_ERRORS_TOTAL',
    'Total number of errors encountered while collecting S3 metrics',
    ['bucket', 'env', 'error_type'],
    registry=registry
)


class S3MetricsCollector:
    """Collects S3 metrics from CloudWatch and caches them"""
    
    def __init__(self):
        self.last_update = 0
        self.cached_metrics = {}
        self._setup_aws_clients()
    
    def _setup_aws_clients(self):
        """Initialize AWS clients"""
        try:
            session_kwargs = {'region_name': AWS_REGION}
            
            # For local development with MinIO, we skip CloudWatch
            if AWS_ENDPOINT_URL:
                logger.info(f"Using MinIO endpoint: {AWS_ENDPOINT_URL}")
                logger.info("Skipping CloudWatch metrics collection for local development")
                self.cloudwatch = None
                return
            
            self.cloudwatch = boto3.client('cloudwatch', **session_kwargs)
            logger.info(f"Initialized CloudWatch client for region: {AWS_REGION}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self.cloudwatch = None
            self._record_error('aws_client_init')
    
    def _record_error(self, error_type: str):
        """Record an error in Prometheus metrics"""
        metrics_collection_errors.labels(
            bucket=S3_BUCKET,
            env=ENV,
            error_type=error_type
        ).inc()
    
    def _should_update_metrics(self) -> bool:
        """Check if metrics should be updated based on cache interval"""
        current_time = time.time()
        return (current_time - self.last_update) >= SCRAPE_INTERVAL
    
    def _get_cloudwatch_metric(self, metric_name: str, statistic: str = 'Maximum', 
                              days_back: int = 1) -> Optional[float]:
        """Fetch a single metric from CloudWatch"""
        if not self.cloudwatch:
            return None
        
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days_back)
            
            # For storage metrics, get the latest daily value
            # For egress metrics, get the sum over the period
            if metric_name == 'BucketSizeBytes':
                period = 86400  # Daily
                statistic = 'Maximum'  # Latest value
            else:  # BucketBytesDownloaded
                period = 86400  # Daily 
                statistic = 'Sum'  # Sum of downloads
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'BucketName',
                        'Value': S3_BUCKET
                    },
                    {
                        'Name': 'StorageType',
                        'Value': 'StandardStorage'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=[statistic]
            )
            
            datapoints = response.get('Datapoints', [])
            if not datapoints:
                logger.warning(f"No CloudWatch data found for metric {metric_name}")
                return None
            
            # Sort by timestamp and get the most recent value
            datapoints.sort(key=lambda x: x['Timestamp'])
            latest_value = datapoints[-1][statistic]
            
            logger.debug(f"CloudWatch {metric_name}: {latest_value}")
            return float(latest_value)
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"CloudWatch API error for {metric_name}: {error_code} - {e}")
            self._record_error(f'cloudwatch_{error_code.lower()}')
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {metric_name}: {e}")
            self._record_error('cloudwatch_unexpected')
            return None
    
    def _get_storage_bytes(self) -> Optional[float]:
        """Get current bucket storage size in bytes"""
        return self._get_cloudwatch_metric('BucketSizeBytes', 'Maximum', days_back=2)
    
    def _get_egress_bytes(self) -> Optional[float]:
        """Get total egress (download) bytes over the last 30 days"""
        if not self.cloudwatch:
            # For local development, return mock data
            return 1024 * 1024 * 50  # 50 MB
        
        # Sum up daily download totals over the last 30 days
        total_egress = 0
        
        try:
            for days_back in range(1, 31):  # Last 30 days
                daily_egress = self._get_cloudwatch_metric(
                    'BucketBytesDownloaded', 
                    'Sum', 
                    days_back=days_back
                )
                if daily_egress:
                    total_egress += daily_egress
                    
            return total_egress
            
        except Exception as e:
            logger.error(f"Error calculating total egress: {e}")
            self._record_error('egress_calculation')
            return None
    
    def update_metrics(self):
        """Update all S3 metrics from CloudWatch"""
        if not self._should_update_metrics():
            logger.debug("Skipping metrics update (cache still valid)")
            return
        
        logger.info("Updating S3 metrics from CloudWatch...")
        
        try:
            # For local development with MinIO, use mock data
            if AWS_ENDPOINT_URL:
                logger.info("Using mock data for local development")
                storage_bytes = 1024 * 1024 * 100  # 100 MB
                egress_bytes = 1024 * 1024 * 50    # 50 MB
            else:
                # Fetch real CloudWatch metrics
                storage_bytes = self._get_storage_bytes()
                egress_bytes = self._get_egress_bytes()
            
            # Update Prometheus gauges
            if storage_bytes is not None:
                s3_storage_bytes.labels(bucket=S3_BUCKET, env=ENV).set(storage_bytes)
                logger.info(f"Updated storage bytes: {storage_bytes:,.0f}")
            else:
                logger.warning("Failed to update storage bytes metric")
            
            if egress_bytes is not None:
                s3_egress_bytes.labels(bucket=S3_BUCKET, env=ENV).set(egress_bytes)
                logger.info(f"Updated egress bytes: {egress_bytes:,.0f}")
            else:
                logger.warning("Failed to update egress bytes metric")
            
            # Update last successful update timestamp
            current_timestamp = time.time()
            metrics_last_updated.labels(bucket=S3_BUCKET, env=ENV).set(current_timestamp)
            self.last_update = current_timestamp
            
            logger.info("S3 metrics update completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to update S3 metrics: {e}")
            self._record_error('metrics_update')


class MetricsHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for serving Prometheus metrics"""
    
    def __init__(self, collector: S3MetricsCollector, *args, **kwargs):
        self.collector = collector
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/metrics':
            # Update metrics on each scrape
            self.collector.update_metrics()
            
            # Generate Prometheus metrics
            metrics_data = generate_latest(registry)
            
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(metrics_data)
            
        elif self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "s3-metrics-exporter"}')
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")


def create_handler(collector: S3MetricsCollector):
    """Create HTTP handler with collector dependency injection"""
    def handler(*args, **kwargs):
        return MetricsHTTPHandler(collector, *args, **kwargs)
    return handler


def main():
    """Main entry point"""
    logger.info("Starting S3 Metrics Exporter")
    logger.info(f"Configuration:")
    logger.info(f"  AWS Region: {AWS_REGION}")
    logger.info(f"  S3 Bucket: {S3_BUCKET}")
    logger.info(f"  Environment: {ENV}")
    logger.info(f"  Port: {EXPORTER_PORT}")
    logger.info(f"  Scrape Interval: {SCRAPE_INTERVAL}s")
    
    if AWS_ENDPOINT_URL:
        logger.info(f"  AWS Endpoint: {AWS_ENDPOINT_URL} (Local Development)")
    
    # Initialize metrics collector
    collector = S3MetricsCollector()
    
    # Perform initial metrics collection
    collector.update_metrics()
    
    # Start HTTP server
    handler = create_handler(collector)
    server = HTTPServer(('0.0.0.0', EXPORTER_PORT), handler)
    
    logger.info(f"S3 Metrics Exporter listening on port {EXPORTER_PORT}")
    logger.info(f"Metrics endpoint: http://0.0.0.0:{EXPORTER_PORT}/metrics")
    logger.info(f"Health endpoint: http://0.0.0.0:{EXPORTER_PORT}/health")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down S3 Metrics Exporter")
        server.shutdown()


if __name__ == '__main__':
    main() 