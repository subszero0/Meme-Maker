# Production Deployment Steps - Manual Guide

This guide provides step-by-step instructions for deploying Meme Maker to your Lightsail instance using blue-green deployment strategy.

## Prerequisites

- ✅ `.env.prod` file created and configured with AWS credentials
- ✅ AWS resources provisioned (S3, Route 53, IAM user)
- ✅ Lightsail instance running with Docker installed
- ✅ SSH access to Lightsail instance configured
- ✅ Domain DNS pointing to Lightsail IP

---

## Option 1: Automated Deployment (Recommended)

### 1. Run the automated deployment script:

```bash
# Make the script executable (Linux/Mac)
chmod +x scripts/deploy_to_production.sh

# Run the deployment
./scripts/deploy_to_production.sh
```

The script will guide you through the process and handle all steps automatically.

---

## Option 2: Manual Step-by-Step Deployment

### Step 1: Prepare Local Environment

```bash
# Ensure you're in the project root
cd /path/to/meme-maker

# Verify .env.prod exists
ls -la .env.prod

# Get current commit SHA (you'll need this)
git rev-parse HEAD
```

### Step 2: Connect to Lightsail

Replace `<LIGHTSAIL_IP>` with your actual Lightsail static IP:

```bash
# Test SSH connection
ssh ubuntu@<LIGHTSAIL_IP>
```

### Step 3: Deploy Code to Server

```bash
# SSH into your Lightsail instance
ssh ubuntu@<LIGHTSAIL_IP>

# Clone the repository (first time) or update it
cd /home/ubuntu

# If first deployment:
git clone https://github.com/your-username/meme-maker.git
cd meme-maker

# If updating existing deployment:
# cd meme-maker
# git fetch origin
# git reset --hard origin/main
```

### Step 4: Transfer Environment File

From your **local machine** (open a new terminal):

```bash
# Copy .env.prod to server
scp .env.prod ubuntu@<LIGHTSAIL_IP>:/home/ubuntu/meme-maker/.env.prod
```

### Step 5: Setup Docker Environment

Back on the **Lightsail server**:

```bash
cd /home/ubuntu/meme-maker

# Create necessary directories
sudo mkdir -p /opt/meme-data
sudo chown ubuntu:ubuntu /opt/meme-data
mkdir -p logs/deployments

# Pull Docker images
docker compose -f infra/production/docker-compose.prod.yml --env-file .env.prod pull
```

### Step 6: Run Blue-Green Deployment

```bash
# Get current commit SHA
GIT_SHA=$(git rev-parse HEAD)
echo "Deploying SHA: $GIT_SHA"

# Run the blue-green deployment script
bash scripts/promote_to_prod.sh $GIT_SHA
```

This script will:
- 🔵 Start new containers on alternate port (blue/green strategy)
- 🏥 Perform health checks
- 🧪 Run smoke tests
- 🔄 Switch traffic to new containers
- 🗑️ Clean up old containers (after grace period)

### Step 7: Verify Deployment

#### Test Health Endpoint
```bash
# Test from server
curl -fsSL http://localhost:8080/health

# Test from internet (replace with your domain)
curl -fsSL https://memeit.pro/health
```

Expected response: `{"status":"ok"}`

#### Test API Documentation
```bash
curl -fsSL https://memeit.pro/docs
```

Should return HTML with "Swagger" in the content.

#### Test Monitoring
```bash
curl -I https://monitoring.memeit.pro/grafana
```

Should return HTTP 401 (basic auth prompt) or 200.

### Step 8: Cleanup

```bash
# Remove old Docker images
docker image prune -f

# Check disk usage
docker system df
```

---

## Verification Checklist

After deployment, verify these endpoints:

- [ ] ✅ `https://memeit.pro/health` → `{"status":"ok"}`
- [ ] ✅ `https://memeit.pro/docs` → Swagger UI loads
- [ ] ✅ `https://monitoring.memeit.pro/grafana` → Basic auth prompt or dashboard
- [ ] ✅ SSL certificate is valid and trusted
- [ ] ✅ Domain redirects www to non-www (or vice versa)

## Container Status Check

```bash
# Check all containers are running
docker ps

# Check specific container logs
docker logs meme-prod-backend
docker logs meme-prod-worker
docker logs meme-prod-redis
docker logs meme-prod-caddy

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected output:
```
NAMES                STATUS
meme-prod-caddy      Up X minutes (healthy)
meme-prod-backend    Up X minutes (healthy)
meme-prod-worker     Up X minutes (healthy)
meme-prod-redis      Up X minutes (healthy)
meme-prod-minio      Up X minutes (healthy)
```

---

## Troubleshooting

### Issue: Health endpoint not responding

```bash
# Check backend container logs
docker logs meme-prod-backend --tail 50

# Check if backend is accessible internally
docker exec meme-prod-backend curl http://localhost:8000/health

# Check network connectivity
docker network ls
docker network inspect meme-maker_prod-net
```

### Issue: SSL/Domain issues

```bash
# Check Caddy logs
docker logs meme-prod-caddy --tail 50

# Test domain resolution
dig memeit.pro
dig www.memeit.pro

# Check Caddy configuration
docker exec meme-prod-caddy caddy fmt --config /etc/caddy/Caddyfile
```

### Issue: Database/Redis connection

```bash
# Check Redis logs
docker logs meme-prod-redis --tail 50

# Test Redis connectivity from backend
docker exec meme-prod-backend redis-cli -h redis ping

# Check MinIO status
docker logs meme-prod-minio --tail 50
```

### Issue: Blue-Green deployment failed

```bash
# Check which stack is currently active
docker ps | grep meme-prod

# Rollback to previous version if needed
cd /home/ubuntu/meme-maker
bash scripts/promote_to_prod.sh rollback

# Check deployment logs
tail -f logs/deployments/$(date +%Y-%m-%d).log
```

---

## Post-Deployment Tasks

### 1. Set up monitoring alerts

```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .job, health: .health}'

# Check Alertmanager status
curl -s http://localhost:9093/api/v1/status
```

### 2. Test application functionality

```bash
# Test video upload (replace with actual test)
curl -X POST https://memeit.pro/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=test", "start_time": 0, "end_time": 30}'
```

### 3. Set up log rotation

```bash
# Configure logrotate for Docker logs
sudo vim /etc/logrotate.d/docker

# Add the following content:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size 1M
    missingok
    delaycompress
    copytruncate
}
```

### 4. Set up automated backups

```bash
# Create backup script for MinIO data
cat > /home/ubuntu/backup-minio.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/minio-data-$DATE.tar.gz /opt/meme-data
find $BACKUP_DIR -name "minio-data-*.tar.gz" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backup-minio.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup-minio.sh") | crontab -
```

---

## Rollback Procedure

If something goes wrong after deployment:

```bash
cd /home/ubuntu/meme-maker

# Option 1: Rollback using the script
bash scripts/promote_to_prod.sh rollback

# Option 2: Manual rollback to specific commit
bash scripts/promote_to_prod.sh <previous-commit-sha>

# Option 3: Emergency stop all containers
docker compose -f infra/production/docker-compose.prod.yml down
```

---

## Performance Monitoring

### Key metrics to monitor:

1. **Response times**: < 200ms for health endpoint
2. **Memory usage**: Backend < 2GB, Worker < 4GB
3. **Disk usage**: < 80% on /opt/meme-data
4. **Job queue length**: < 50 pending jobs
5. **Error rates**: < 1% 5xx responses

### Monitoring commands:

```bash
# Check resource usage
docker stats

# Check job queue status
docker exec meme-prod-redis redis-cli llen queue:default

# Check disk usage
df -h /opt/meme-data

# Check network connections
docker exec meme-prod-backend ss -tuln
```

---

## Security Best Practices

- [ ] ✅ All containers run as non-root users
- [ ] ✅ Secrets are not in source control
- [ ] ✅ SSL/TLS enforced for all endpoints
- [ ] ✅ Internal services not exposed publicly
- [ ] ✅ Regular security updates applied
- [ ] ✅ Log aggregation configured
- [ ] ✅ Monitoring and alerting active

Your Meme Maker application is now successfully deployed to production! 🎉 