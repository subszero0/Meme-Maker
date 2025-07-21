# Meme Maker Monitoring Infrastructure

This directory contains the monitoring infrastructure configuration for the Meme Maker application using Prometheus and Grafana.

## 🏗️ Structure

```
infra/
├── prometheus/
│   ├── prometheus.dev.yml      # Development Prometheus configuration
│   └── rules/
│       └── meme_maker.dev.yml  # Development alert rules
├── grafana/
│   ├── dashboards/
│   │   └── meme-maker-overview.json  # Main application dashboard
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml  # Prometheus datasource config
│       └── dashboards/
│           └── default.yml     # Dashboard provisioning config
└── README.md                   # This file
```

## 🚀 Quick Start (Development)

1. **Start the monitoring stack:**
   ```bash
   docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml up -d
   ```

2. **Validate the deployment:**
   ```powershell
   # Windows PowerShell
   .\scripts\validate_dev_monitoring.ps1
   
   # Or bash (if available)
   bash ./scripts/validate_dev_monitoring.sh
   ```

3. **Access the dashboards:**
   - **Prometheus**: http://localhost:9090
   - **Grafana**: http://localhost:3001 (admin/dev_admin_2025)

## 📊 Available Metrics

### Backend Metrics
- HTTP request rates and latencies
- Queue depth and processing times
- Custom business metrics (job latency, queue sizes)
- Storage metrics

### Infrastructure Metrics
- Container resource usage (CPU, Memory)
- Redis performance metrics
- Node/host system metrics

### Alert Rules (Development)
- Queue depth alerts (>5 items for >2min)
- High job latency alerts (>60s p95 for >1min)
- Service down alerts (>30s downtime)

## 🔧 Configuration

### Development Environment
- **Retention**: 7 days, 2GB max
- **Scrape intervals**: 5-30 seconds (faster for development)
- **Alert thresholds**: Relaxed for development testing
- **Ports exposed**: All monitoring services accessible locally

### Environment Variables
Configure in `.env.monitoring.dev`:
- `GRAFANA_ADMIN_PASSWORD`: Grafana admin password
- `GRAFANA_SECRET_KEY`: Grafana secret key for sessions
- `PROMETHEUS_RETENTION_TIME`: Data retention period
- `PROMETHEUS_RETENTION_SIZE`: Storage size limit

## 🎯 Monitoring Workflow

1. **Development** (`feature/monitoring-implementation` branch)
   - Fast scrape intervals for immediate feedback
   - All ports exposed for debugging
   - Relaxed alert thresholds
   - Debug logging enabled

2. **Staging** (`monitoring-staging` branch)
   - Production-like configuration
   - Moderate resource limits
   - Production-like alert thresholds
   - 24-48 hour validation period

3. **Production** (`master` branch)
   - Secure configuration (no exposed ports)
   - Production resource limits
   - Full security hardening
   - 30-day retention

## 🛠️ Customization

### Adding New Dashboards
1. Create JSON dashboard file in `grafana/dashboards/`
2. Restart Grafana service
3. Dashboard will be auto-imported

### Adding New Alerts
1. Edit `prometheus/rules/meme_maker.dev.yml`
2. Add your alert rule
3. Restart Prometheus service

### Adding New Metrics
1. Instrument your application code
2. Expose metrics on `/metrics` endpoint
3. Prometheus will auto-discover and scrape

## 🔍 Troubleshooting

### Common Issues
1. **Services not starting**: Check Docker logs
   ```bash
   docker-compose logs prometheus grafana
   ```

2. **Metrics not appearing**: Verify scrape targets
   - Visit http://localhost:9090/targets
   - Check target health status

3. **Dashboard not loading**: Check Grafana logs
   ```bash
   docker-compose logs grafana
   ```

### Health Checks
Use the validation scripts to check system health:
```powershell
.\scripts\validate_dev_monitoring.ps1
```

## 📈 Next Steps

1. **Staging Deployment**: After development validation
2. **Production Hardening**: Security configurations
3. **Alert Manager**: Set up notification channels
4. **Custom Dashboards**: Create business-specific views

For detailed implementation steps, see `Prometheus and Grafana_todo.md`. 