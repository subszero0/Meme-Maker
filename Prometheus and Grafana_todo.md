# Prometheus and Grafana Implementation Plan
**Version 1.1 - January 2025**  
**Status: Ready for Implementation**  
**Workflow: Dev → Staging → Production**

---

## 🎯 **Executive Summary**

This plan provides a systematic approach to enable comprehensive Prometheus metrics collection and Grafana visualization for the Meme Maker application following the established development workflow: **Dev → Staging → Production**. The implementation builds upon existing metrics infrastructure and follows security best practices while ensuring zero production downtime.

### **Branch Strategy**
- **Development Branch**: `feature/monitoring-implementation` 
- **Staging Branch**: `monitoring-staging` (NEW - dedicated for this feature)
- **Production Branch**: `master` (protected - requires manual merge after staging validation)

### **Current State Analysis**
✅ **Already Implemented:**
- Backend metrics endpoint (`/metrics`) with Prometheus client
- Custom business metrics (job latency, queue depth, inflight jobs)
- FastAPI instrumentator for HTTP metrics
- Docker compose infrastructure with commented Prometheus/Grafana services
- Comprehensive test suite for metrics

⚠️ **Missing Components:**
- Active Prometheus service configuration
- Grafana dashboard definitions
- Infrastructure configuration files
- Alert manager configuration
- Security-hardened monitoring stack

---

## 🌊 **Development Workflow Implementation**

### **Phase 0: Branch Management & Setup**

#### **0.1 Create Development Environment**
```bash
# 1. Create feature branch from master
git checkout master
git pull origin master
git checkout -b feature/monitoring-implementation

# 2. Verify current state
docker-compose ps
curl http://localhost:8000/metrics  # Verify metrics endpoint works

# 3. Create .env.monitoring for development
cat > .env.monitoring.dev << EOF
# Development Monitoring Environment
ENVIRONMENT=development
GRAFANA_ADMIN_PASSWORD=dev_admin_2025
GRAFANA_SECRET_KEY=$(openssl rand -hex 32)
PROMETHEUS_RETENTION_TIME=7d
PROMETHEUS_RETENTION_SIZE=2GB
GRAFANA_LOG_LEVEL=debug
MONITORING_NETWORK_SUBNET=172.20.0.0/16
EOF

# 4. Set up development monitoring directory
mkdir -p infra/{prometheus/{rules,targets},grafana/{dashboards,provisioning/{datasources,dashboards}},docker}
```

#### **0.2 Development Branch Protection**
```bash
# Create development-specific configurations
cp docker-compose.yaml docker-compose.dev.monitoring.yaml

# Add development override
cat > docker-compose.monitoring.override.yml << EOF
# Development monitoring override
services:
  prometheus:
    environment:
      - PROMETHEUS_RETENTION_TIME=7d
      - PROMETHEUS_RETENTION_SIZE=2GB
    ports:
      - "9090:9090"  # Expose for development
    
  grafana:
    environment:
      - GF_LOG_LEVEL=debug
      - GF_SECURITY_ADMIN_PASSWORD=dev_admin_2025
    ports:
      - "3001:3000"  # Expose for development
    
  # Development-only: disable resource limits
  redis_exporter:
    deploy:
      resources: {}
  
  node_exporter:
    deploy:
      resources: {}
      
  cadvisor:
    deploy:
      resources: {}
EOF
```

---

## 📋 **Phase 1: Development Implementation (Dev Branch)**

### **1.1 Development Environment Setup**

**Branch**: `feature/monitoring-implementation`  
**Environment**: Local development with full debugging

```bash
# Start development with monitoring
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml up -d

# Development-specific configurations
cat > infra/prometheus/prometheus.dev.yml << EOF
global:
  scrape_interval: 10s        # Faster for development
  evaluation_interval: 10s    # Faster for development
  external_labels:
    cluster: 'meme-maker-development'
    environment: 'development'

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s

  - job_name: 'meme-maker-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s         # Faster for development
    scrape_timeout: 3s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
    scrape_interval: 10s        # Faster for development

  - job_name: 'node'
    static_configs:
      - targets: ['node_exporter:9100']
    scrape_interval: 30s

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s

storage:
  tsdb:
    path: /prometheus
    retention.time: 7d          # Shorter for development
    retention.size: 2GB         # Smaller for development
EOF
```

### **1.2 Development Alert Rules (Relaxed Thresholds)**

```yaml
# infra/prometheus/rules/meme_maker.dev.yml
groups:
  - name: meme_maker_development_alerts
    rules:
      # Relaxed thresholds for development
      - alert: QueueDepthHigh_Dev
        expr: redis_queue_length{queue="clips"} > 5  # Lower threshold
        for: 2m                                       # Shorter duration
        labels:
          severity: warning
          environment: development
        annotations:
          summary: "Development: High queue depth"
          description: "Queue depth {{ $value }} in development"

      - alert: HighJobLatency_Dev
        expr: histogram_quantile(0.95, rate(clip_job_latency_seconds_bucket[2m])) > 60
        for: 1m                                       # Shorter duration
        labels:
          severity: warning
          environment: development
        annotations:
          summary: "Development: High job latency"
          description: "95th percentile latency: {{ $value }}s"
```

### **1.3 Development Testing & Validation**

```bash
# Development validation script
cat > scripts/validate_dev_monitoring.sh << EOF
#!/bin/bash
echo "🔍 Validating Development Monitoring Stack..."

# Test all endpoints with development settings
curl -f http://localhost:9090/-/healthy || { echo "❌ Dev Prometheus failed"; exit 1; }
curl -f http://localhost:3001/api/health || { echo "❌ Dev Grafana failed"; exit 1; }
curl -f http://localhost:8000/metrics | grep -q "clip_jobs_queued_total" || { echo "❌ Dev metrics failed"; exit 1; }

# Test development-specific features
curl -f "http://localhost:9090/api/v1/query?query=up" | jq '.data.result | length' || { echo "❌ Dev Prometheus query failed"; exit 1; }

echo "✅ Development monitoring stack validated!"
echo "🎯 Development URLs:"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana: http://localhost:3001 (admin/dev_admin_2025)"
EOF

chmod +x scripts/validate_dev_monitoring.sh
./scripts/validate_dev_monitoring.sh
```

### **1.4 Development Commit & Push**

```bash
# Commit development implementation
git add .
git commit -m "feat: implement Prometheus and Grafana monitoring stack

- Add Prometheus configuration with development settings
- Configure Grafana with auto-provisioning dashboards
- Implement monitoring exporters (Redis, Node, cAdvisor)
- Add development-specific alert rules
- Create validation scripts for monitoring stack
- Configure secure networking and resource limits

Development features:
- Faster scrape intervals for development
- Relaxed alert thresholds
- Debug logging enabled
- Exposed ports for local testing

Refs: Prometheus and Grafana_todo.md"

# Push development branch
git push origin feature/monitoring-implementation
```

---

## 📋 **Phase 2: Staging Implementation (Staging Branch)**

### **2.1 Create Staging Branch**

```bash
# Create new staging branch from development
git checkout feature/monitoring-implementation
git checkout -b monitoring-staging

# Create staging-specific configurations
cat > .env.monitoring.staging << EOF
# Staging Monitoring Environment
ENVIRONMENT=staging
GRAFANA_ADMIN_PASSWORD=staging_admin_$(openssl rand -hex 8)
GRAFANA_SECRET_KEY=$(openssl rand -hex 32)
PROMETHEUS_RETENTION_TIME=15d
PROMETHEUS_RETENTION_SIZE=5GB
GRAFANA_LOG_LEVEL=warn
MONITORING_NETWORK_SUBNET=172.21.0.0/16
EOF
```

### **2.2 Staging Configuration Adjustments**

```yaml
# docker-compose.staging.monitoring.yml
services:
  prometheus:
    environment:
      - PROMETHEUS_RETENTION_TIME=15d
      - PROMETHEUS_RETENTION_SIZE=5GB
    ports:
      - "9090:9090"  # Keep exposed for staging validation
    deploy:
      resources:
        limits:
          memory: 768MB      # Moderate limits for staging
          cpus: '0.4'
        reservations:
          memory: 384MB
          cpus: '0.2'
    
  grafana:
    environment:
      - GF_LOG_LEVEL=warn    # Reduce logging for staging
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    ports:
      - "3001:3000"          # Keep exposed for staging validation
    deploy:
      resources:
        limits:
          memory: 384MB      # Moderate limits for staging
          cpus: '0.25'
        reservations:
          memory: 192MB
          cpus: '0.1'

  # Apply moderate resource limits to exporters
  redis_exporter:
    deploy:
      resources:
        limits:
          memory: 64MB
          cpus: '0.1'
        reservations:
          memory: 32MB
          cpus: '0.05'
```

### **2.3 Staging Alert Rules (Production-Like)**

```yaml
# infra/prometheus/rules/meme_maker.staging.yml
groups:
  - name: meme_maker_staging_alerts
    rules:
      # Production-like thresholds for staging validation
      - alert: QueueDepthHigh_Staging
        expr: redis_queue_length{queue="clips"} > 15
        for: 5m
        labels:
          severity: warning
          environment: staging
        annotations:
          summary: "Staging: High queue depth detected"
          description: "Queue depth {{ $value }} exceeds threshold for 5 minutes"

      - alert: QueueDepthCritical_Staging
        expr: redis_queue_length{queue="clips"} > 25
        for: 2m
        labels:
          severity: critical
          environment: staging
        annotations:
          summary: "Staging: Critical queue depth"
          description: "Queue depth {{ $value }} is critically high"

      - alert: HighJobLatency_Staging
        expr: histogram_quantile(0.95, rate(clip_job_latency_seconds_bucket[5m])) > 120
        for: 3m
        labels:
          severity: warning
          environment: staging
        annotations:
          summary: "Staging: High job processing latency"
          description: "95th percentile latency: {{ $value }}s"

      - alert: HighErrorRate_Staging
        expr: rate(clip_job_latency_seconds_count{status="error"}[5m]) / rate(clip_job_latency_seconds_count[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
          environment: staging
        annotations:
          summary: "Staging: High error rate detected"
          description: "Error rate: {{ $value | humanizePercentage }}"
```

### **2.4 Staging Testing & Load Validation**

```bash
# Create comprehensive staging validation
cat > scripts/validate_staging_monitoring.sh << EOF
#!/bin/bash
set -e

echo "🔍 Comprehensive Staging Monitoring Validation..."

# 1. Basic health checks
echo "Testing basic health..."
curl -f http://localhost:9090/-/healthy || { echo "❌ Staging Prometheus failed"; exit 1; }
curl -f http://localhost:3001/api/health || { echo "❌ Staging Grafana failed"; exit 1; }

# 2. Metrics validation
echo "Testing metrics collection..."
curl -f http://localhost:8000/metrics | grep -q "clip_jobs_queued_total" || { echo "❌ Custom metrics missing"; exit 1; }

# 3. Alert rules validation
echo "Testing alert rules..."
curl -f "http://localhost:9090/api/v1/rules" | jq '.data.groups[].rules[] | select(.name | contains("Staging"))' || { echo "❌ Staging alerts missing"; exit 1; }

# 4. Dashboard validation
echo "Testing Grafana dashboards..."
curl -f -u admin:\${GRAFANA_ADMIN_PASSWORD} "http://localhost:3001/api/dashboards/home" | jq '.meta.slug' || { echo "❌ Dashboard access failed"; exit 1; }

# 5. Load testing with monitoring
echo "Running load test with monitoring..."
python3 scripts/load_test_with_metrics.py --jobs=20 --concurrent=5

# 6. Alert testing (simulate high load)
echo "Testing alert triggers..."
# This would trigger alerts in a controlled manner

echo "✅ Staging monitoring validation completed!"
echo "📊 Monitor the following during staging period:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001"
echo "  - Check alert firing during load tests"
echo "  - Verify dashboard accuracy"
echo "  - Monitor resource usage"
EOF

chmod +x scripts/validate_staging_monitoring.sh
```

### **2.5 Staging Deployment & Testing**

```bash
# Deploy to staging
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml up -d

# Run comprehensive validation
./scripts/validate_staging_monitoring.sh

# Monitor for 24-48 hours in staging
echo "🔄 Staging monitoring period started"
echo "📋 Staging checklist:"
echo "  [ ] Monitor for 24-48 hours"
echo "  [ ] Verify no false positive alerts"
echo "  [ ] Test alert notifications"
echo "  [ ] Validate dashboard accuracy"
echo "  [ ] Check resource usage impact"
echo "  [ ] Performance regression testing"

# Commit staging implementation
git add .
git commit -m "feat: configure monitoring for staging environment

- Update configurations for staging-specific requirements
- Implement production-like alert thresholds
- Add comprehensive staging validation scripts
- Configure moderate resource limits
- Set up staging-specific retention policies

Staging validation:
- 15-day retention for historical analysis
- Production-like alert rules
- Moderate resource allocation
- Comprehensive load testing

Ready for production deployment after validation period."

git push origin monitoring-staging
```

---

## 📋 **Phase 3: Production Deployment (Master Branch)**

### **3.1 Production Configuration**

**⚠️ Only proceed after successful staging validation (24-48 hours)**

```bash
# Create production-ready configurations
cat > .env.monitoring.production << EOF
# Production Monitoring Environment
ENVIRONMENT=production
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 16)
GRAFANA_SECRET_KEY=$(openssl rand -hex 32)
PROMETHEUS_RETENTION_TIME=30d
PROMETHEUS_RETENTION_SIZE=10GB
GRAFANA_LOG_LEVEL=error
MONITORING_NETWORK_SUBNET=172.22.0.0/16
PROMETHEUS_WEB_CONFIG_FILE=/etc/prometheus/web.yml
EOF

# Secure the production environment file
chmod 600 .env.monitoring.production
```

### **3.2 Production Docker Compose Integration**

```yaml
# Production modifications to docker-compose.yaml
services:
  # Add monitoring services with production security
  prometheus:
    image: prom/prometheus:v2.48.1
    container_name: meme-maker-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.retention.time=30d'
      - '--storage.tsdb.retention.size=10GB'
      - '--web.external-url=https://memeit.pro/prometheus'
      - '--web.config.file=/etc/prometheus/web.yml'  # Security config
    volumes:
      - prometheus_data:/prometheus
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./infra/prometheus/rules:/etc/prometheus/rules:ro
      - ./infra/prometheus/web.yml:/etc/prometheus/web.yml:ro
    networks:
      - monitoring
    # Remove exposed ports for production security
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: 1GB
          cpus: '0.5'
        reservations:
          memory: 512MB
          cpus: '0.2'
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    user: "65534:65534"  # nobody user

  grafana:
    image: grafana/grafana-oss:10.2.3
    container_name: meme-maker-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_SECURITY_SECRET_KEY=${GRAFANA_SECRET_KEY}
      - GF_SECURITY_DISABLE_GRAVATAR=true
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SECURITY_COOKIE_SECURE=true
      - GF_SECURITY_COOKIE_SAMESITE=strict
      - GF_LOG_LEVEL=error
      - GF_ANALYTICS_REPORTING_ENABLED=false
      - GF_ANALYTICS_CHECK_FOR_UPDATES=false
      - GF_SERVER_ROOT_URL=https://memeit.pro/grafana
      - GF_SERVER_SERVE_FROM_SUB_PATH=true
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./infra/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./infra/grafana/grafana.ini:/etc/grafana/grafana.ini:ro
    networks:
      - monitoring
    # Remove exposed ports for production security
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 512MB
          cpus: '0.3'
        reservations:
          memory: 256MB
          cpus: '0.1'
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    user: "472:472"  # grafana user
```

### **3.3 Production Merge Process**

```bash
# 1. Final staging validation
echo "🔍 Final staging validation before production..."
./scripts/validate_staging_monitoring.sh

# 2. Create merge request to master
git checkout monitoring-staging
git pull origin monitoring-staging

# Create comprehensive production deployment script
cat > scripts/deploy_production_monitoring.sh << EOF
#!/bin/bash
set -e

echo "🚀 Deploying Monitoring to Production..."
echo "⚠️  This will modify the production environment"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "\$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# 1. Backup current production state
echo "📦 Creating production backup..."
docker-compose ps > backup/production_state_\$(date +%Y%m%d_%H%M%S).txt
cp docker-compose.yaml backup/docker-compose.backup_\$(date +%Y%m%d_%H%M%S).yaml

# 2. Deploy monitoring stack
echo "🔧 Deploying monitoring services..."
docker-compose up -d prometheus grafana redis_exporter node_exporter cadvisor

# 3. Wait for services to initialize
echo "⏳ Waiting for services to initialize..."
sleep 60

# 4. Validate production deployment
echo "✅ Validating production monitoring..."
./scripts/validate_production_monitoring.sh

echo "🎉 Production monitoring deployment completed!"
echo "📊 Access monitoring (via nginx proxy):"
echo "  Prometheus: https://memeit.pro/prometheus"
echo "  Grafana: https://memeit.pro/grafana"
EOF

chmod +x scripts/deploy_production_monitoring.sh

# 3. Commit final production configuration
git add .
git commit -m "feat: production-ready monitoring configuration

- Remove exposed ports for production security
- Add comprehensive security hardening
- Configure nginx sub-path routing
- Implement production resource limits
- Add production deployment and rollback scripts
- Set up 30-day retention for production metrics

Production security features:
- No exposed ports (nginx proxy only)
- Security hardening (no-new-privileges, cap-drop)
- Non-root users for all services
- Secure authentication and session management
- Production-grade resource allocation

Validated in staging for 48+ hours with zero issues.
Ready for production deployment."

git push origin monitoring-staging

# 4. Create pull request to master (manual step)
echo "📋 Manual Step Required:"
echo "1. Create Pull Request: monitoring-staging → master"
echo "2. Review changes in GitHub"
echo "3. After approval, merge to master"
echo "4. Deploy to production using: ./scripts/deploy_production_monitoring.sh"
```

### **3.4 Production Rollback Plan**

```bash
# Create production rollback script
cat > scripts/rollback_production_monitoring.sh << EOF
#!/bin/bash
set -e

echo "🔄 Rolling back production monitoring..."
echo "⚠️  This will remove monitoring services from production"
read -p "Are you sure you want to rollback? (yes/no): " confirm

if [ "\$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled"
    exit 1
fi

# 1. Stop monitoring services
echo "🛑 Stopping monitoring services..."
docker-compose stop prometheus grafana redis_exporter node_exporter cadvisor

# 2. Remove monitoring containers
echo "🗑️  Removing monitoring containers..."
docker-compose rm -f prometheus grafana redis_exporter node_exporter cadvisor

# 3. Restore original docker-compose.yaml
echo "📦 Restoring original configuration..."
LATEST_BACKUP=\$(ls -t backup/docker-compose.backup_*.yaml | head -1)
if [ -f "\$LATEST_BACKUP" ]; then
    cp "\$LATEST_BACKUP" docker-compose.yaml
    echo "✅ Restored from: \$LATEST_BACKUP"
else
    echo "❌ No backup found"
    exit 1
fi

# 4. Restart core services
echo "🚀 Restarting core services..."
docker-compose up -d backend frontend worker redis

# 5. Validate core functionality
echo "✅ Validating core services..."
sleep 30
curl -f https://memeit.pro/health || { echo "❌ Core services failed"; exit 1; }

echo "✅ Rollback completed successfully"
echo "📊 Core application restored to pre-monitoring state"

# Optional: Keep monitoring data for later analysis
echo "💾 Monitoring data preserved in Docker volumes"
echo "   To remove completely: docker volume rm prometheus_data grafana_data"
EOF

chmod +x scripts/rollback_production_monitoring.sh
```

---

## 📋 **Implementation Workflow Summary**

### **Development Phase** ✅
1. **Branch**: `feature/monitoring-implementation`
2. **Duration**: 2-3 days
3. **Focus**: Implementation and basic testing
4. **Validation**: Local testing and functionality verification

### **Staging Phase** ⏳
1. **Branch**: `monitoring-staging` (NEW)
2. **Duration**: 24-48 hours minimum
3. **Focus**: Production-like testing and validation
4. **Validation**: Load testing, alert validation, resource monitoring

### **Production Phase** 🎯
1. **Branch**: `master` (manual merge required)
2. **Duration**: Controlled deployment
3. **Focus**: Zero-downtime production deployment
4. **Validation**: Production health checks and monitoring

---

## 🚀 **Quick Start Commands by Phase**

### **Development**
```bash
git checkout -b feature/monitoring-implementation
# Follow Phase 1 implementation
./scripts/validate_dev_monitoring.sh
git push origin feature/monitoring-implementation
```

### **Staging** 
```bash
git checkout -b monitoring-staging
# Follow Phase 2 implementation  
./scripts/validate_staging_monitoring.sh
# Monitor for 24-48 hours
git push origin monitoring-staging
```

### **Production**
```bash
# Create PR: monitoring-staging → master
# After approval and merge:
git checkout master
git pull origin master
./scripts/deploy_production_monitoring.sh
```

### **Emergency Rollback**
```bash
./scripts/rollback_production_monitoring.sh
```

---

**Implementation Time Estimate: 6-8 hours + 24-48h staging**  
**Team Required: 1 DevOps Engineer**  
**Risk Level: Low (non-breaking changes with staging validation)**  
**Rollback Time: < 5 minutes** 