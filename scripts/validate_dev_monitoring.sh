#!/bin/bash
echo "🔍 Validating Development Monitoring Stack..."

# Test all endpoints with development settings
echo "Testing Prometheus health..."
curl -f http://localhost:9090/-/healthy || { echo "❌ Dev Prometheus failed"; exit 1; }

echo "Testing Grafana health..."
curl -f http://localhost:3001/api/health || { echo "❌ Dev Grafana failed"; exit 1; }

echo "Testing backend metrics..."
curl -f http://localhost:8000/metrics | grep -q "clip_jobs_queued_total" || { echo "❌ Dev metrics failed"; exit 1; }

# Test development-specific features
echo "Testing Prometheus query API..."
curl -f "http://localhost:9090/api/v1/query?query=up" | jq '.data.result | length' || { echo "❌ Dev Prometheus query failed"; exit 1; }

echo "Testing Redis exporter..."
curl -f http://localhost:9121/metrics | grep -q "redis_up" || { echo "❌ Redis exporter failed"; exit 1; }

echo "Testing Node exporter..."
curl -f http://localhost:9100/metrics | grep -q "node_up" || { echo "❌ Node exporter failed"; exit 1; }

echo "Testing cAdvisor..."
curl -f http://localhost:8081/metrics | grep -q "container_cpu_usage_seconds_total" || { echo "❌ cAdvisor failed"; exit 1; }

echo "✅ Development monitoring stack validated!"
echo "🎯 Development URLs:"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana: http://localhost:3001 (admin/dev_admin_2025)"
echo "  Redis Exporter: http://localhost:9121/metrics"
echo "  Node Exporter: http://localhost:9100/metrics"
echo "  cAdvisor: http://localhost:8081/metrics" 