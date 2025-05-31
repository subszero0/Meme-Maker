# Meme Maker Monitoring & Alerting

This document describes the monitoring setup, alerting rules, and incident response procedures for the Meme Maker application.

## Overview

The monitoring stack consists of:
- **Prometheus**: Metrics collection and alerting rules
- **Alertmanager**: Alert routing and notification delivery
- **Grafana**: Dashboards and visualization
- **Backend metrics**: Custom application metrics from FastAPI
- **S3 Metrics Exporter**: Cost monitoring for S3 storage and egress

## Alert Definitions

### Critical Alerts

#### API_Uptime_Failure
**Trigger**: Health check fails for more than 3 consecutive minutes
**Severity**: Critical
**Notifications**: Slack + Email

**Runbook**:
1. Check if the backend service is running: `docker ps | grep meme-maker-backend`
2. Review backend logs: `docker logs meme-maker-backend --tail 50`
3. Check service dependencies:
   - Redis: `docker exec meme-maker-redis redis-cli ping`
   - MinIO: `curl http://localhost:9002/minio/health/live`
4. If services are running but unresponsive, restart the backend:
   ```bash
   docker-compose restart backend
   ```
5. If the issue persists, check resource usage: `docker stats`
6. Escalate to on-call engineer if restart doesn't resolve the issue

#### API_Error_Rate_High
**Trigger**: HTTP error rate > 5% over 5 minutes
**Severity**: Critical
**Notifications**: Slack + Email

**Runbook**:
1. Check recent error logs: `docker logs meme-maker-backend --tail 100 | grep ERROR`
2. Review Grafana dashboard for error patterns
3. Check specific error types:
   - 500 errors: Internal server issues, check backend logs
   - 502/503 errors: Potential proxy/load balancer issues
   - 429 errors: Rate limiting triggered (may be expected during attacks)
4. Check Redis connectivity: `docker exec meme-maker-redis redis-cli info`
5. Monitor queue depth: Check Prometheus `/metrics` endpoint for `rq_jobs_in_queue`
6. If errors are client-related (4xx), monitor for potential abuse
7. If errors are server-related (5xx), consider scaling or restarting services

#### Worker_Not_Processing
**Trigger**: No jobs completed in last 10 minutes
**Severity**: Critical
**Notifications**: Slack + Email

**Runbook**:
1. Check worker container status: `docker ps | grep meme-maker-worker`
2. Review worker logs: `docker logs meme-maker-worker --tail 50`
3. Check queue status: `docker exec meme-maker-redis redis-cli llen rq:queue:default`
4. Verify worker can access dependencies:
   - Redis: `docker exec meme-maker-worker python -c "import redis; r=redis.from_url('redis://redis:6379'); print(r.ping())"`
   - MinIO: Check S3 upload permissions
5. Restart worker if stuck: `docker-compose restart worker`
6. Check for resource constraints: `docker stats meme-maker-worker`
7. Monitor yt-dlp updates: Worker auto-updates on startup

### Warning Alerts

#### Job_Queue_High
**Trigger**: Queue depth > 15 jobs for 5 minutes
**Severity**: Warning
**Notifications**: Slack only

**Runbook**:
1. Check current queue depth: `docker exec meme-maker-redis redis-cli llen rq:queue:default`
2. Review worker performance metrics in Grafana
3. Check if it's due to high traffic (expected) or worker slowdown (investigate)
4. Consider scaling workers if sustained high load:
   ```bash
   docker-compose up --scale worker=2 -d
   ```
5. Monitor processing rates and adjust scaling as needed

### Cost Guardrail Alerts

#### S3StorageTooHigh
**Trigger**: S3 storage > 200 GB for 12 hours
**Severity**: Warning
**Notifications**: Slack only

**Runbook**:
1. Check current S3 storage usage:
   ```bash
   curl http://localhost:9100/metrics | grep S3_STORAGE_BYTES
   ```
2. Review S3 bucket contents:
   ```bash
   aws s3 ls s3://clips --recursive --human-readable --summarize
   ```
3. Check for failed file deletions:
   ```bash
   docker logs meme-maker-worker | grep "Failed to delete"
   ```
4. Manually clean up old files if necessary:
   ```bash
**Slack**:
- Channel: `#alerts`
- Critical alerts include full context and runbook links
- Warning alerts are summary-only
- Resolved notifications are sent

**Email**:
- Only for critical alerts
- HTML formatted with full details
- Includes direct links to runbooks and dashboards

### Alert Routing

```yaml
Critical Alerts (severity: critical):
  - Group wait: 10 seconds
  - Repeat interval: 1 hour
  - Sent to: Slack + Email

Warning Alerts (severity: warning):
  - Group wait: 30 seconds
  - Repeat interval: 2 hours
  - Sent to: Slack only
```

### Inhibition Rules

To prevent alert spam:
- If API is down → suppress error rate alerts
- If worker is stuck → suppress queue high alerts

## Alert Management

### Silencing Alerts

To silence an alert temporarily:

1. **Via Alertmanager UI** (http://localhost:9093):
   - Navigate to "Silences"
   - Click "New Silence"
   - Add matchers (e.g., `alertname="API_Uptime_Failure"`)
   - Set duration and comment

2. **Via API**:
   ```bash
   curl -X POST http://localhost:9093/api/v1/silences \
     -H "Content-Type: application/json" \
     -d '{
       "matchers": [{"name": "alertname", "value": "API_Uptime_Failure"}],
       "startsAt": "2024-01-01T00:00:00Z",
       "endsAt": "2024-01-01T02:00:00Z",
       "comment": "Planned maintenance"
     }'
   ```

### Emergency Contacts

**Primary On-Call**: Check team rotation schedule
**Escalation**: Engineering Manager
**Infrastructure Issues**: DevOps team

## Testing Alerts

### Test Alert Delivery

1. **Test Slack integration**:
   ```bash
   curl -X POST "${ALERT_SLACK_WEBHOOK}" \
     -H "Content-Type: application/json" \
     -d '{"text": "Test alert from Meme Maker monitoring"}'
   ```

2. **Test email delivery**:
   ```bash
   docker exec meme-maker-alertmanager \
     amtool alert add alertname="TestAlert" service="meme-maker" severity="critical"
   ```

### Simulate Failure Conditions

1. **Simulate API downtime**:
   ```bash
   # Stop backend temporarily
   docker stop meme-maker-backend
   # Wait 4 minutes, then restart
   docker start meme-maker-backend
   ```

2. **Simulate high error rate**:
   ```bash
   # Create temporary endpoint that returns 500
   # Add to backend code temporarily:
   # @app.get("/test-error")
   # async def test_error():
   #     raise HTTPException(status_code=500, detail="Test error")
   
   # Then generate errors:
   for i in {1..100}; do curl http://localhost:8000/test-error; done
   ```

3. **Simulate worker issues**:
   ```bash
   # Stop worker
   docker stop meme-maker-worker
   # Wait 12 minutes for alert, then restart
   docker start meme-maker-worker
   ```

## Metrics Reference

### Backend Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by status code |
| `http_request_duration_seconds` | Histogram | Request duration |
| `rq_jobs_in_queue` | Gauge | Jobs waiting in queue |
| `job_duration_seconds` | Histogram | Job processing time |
| `active_jobs` | Gauge | Currently processing jobs |

### Prometheus Targets

- `backend:8000/metrics` - Backend application metrics
- `prometheus:9090/metrics` - Prometheus self-monitoring
- `alertmanager:9093/metrics` - Alertmanager metrics

## Troubleshooting

### Common Issues

**Alerts not firing**:
1. Check Prometheus rules loaded: http://localhost:9090/rules
2. Verify Alertmanager connection: http://localhost:9090/config
3. Check Alertmanager logs: `docker logs meme-maker-alertmanager`

**Notifications not delivered**:
1. Test webhook URLs manually
2. Check Alertmanager configuration: http://localhost:9093/#/config
3. Verify environment variables are set correctly
4. Check Alertmanager logs for delivery errors

**False positives**:
1. Adjust alert thresholds in `prometheus-rules.yml`
2. Increase `for` duration to reduce sensitivity
3. Add additional label matchers to make alerts more specific

## Dashboard Links

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Grafana**: http://localhost:3000
- **Application**: http://localhost:8000

## Maintenance

### Regular Tasks

**Weekly**:
- Review alert frequency and accuracy
- Check for new error patterns in logs
- Update alert thresholds if needed

**Monthly**:
- Rotate SMTP credentials if required
- Review and clean up old silences
- Update team contact information

**Quarterly**:
- Review and update runbook procedures
- Test full disaster recovery procedures
- Update monitoring infrastructure

---

*This document should be kept up-to-date as the system evolves. Last updated: [Current Date]* 