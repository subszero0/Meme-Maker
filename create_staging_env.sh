#!/bin/bash
set -e

echo "🔧 Creating missing .env.monitoring.staging file..."

# Create the missing environment file
cat > .env.monitoring.staging << 'EOF'
# Staging Monitoring Environment
ENVIRONMENT=staging
GRAFANA_ADMIN_PASSWORD=staging_admin_2025_secure
GRAFANA_SECRET_KEY=da8f9a7b6c5e4d3f2a1b9c8d7e6f5a4b3c2d1e9f8a7b6c5d4e3f2a1b9c8d7e6f5a4b3c2d1e
PROMETHEUS_RETENTION_TIME=15d
PROMETHEUS_RETENTION_SIZE=5GB
GRAFANA_LOG_LEVEL=warn
MONITORING_NETWORK_SUBNET=172.21.0.0/16
EOF

echo "✅ Environment file created!"
echo "📋 Grafana credentials: admin / staging_admin_2025_secure" 