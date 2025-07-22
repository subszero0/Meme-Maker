# 🚨 IMMEDIATE FIX COMMANDS

## **Run These Commands NOW on Your Server**

You're already SSH'd into the server. Run these commands in sequence:

### **1. Fix Script Permissions (CRITICAL)**
```bash
chmod +x scripts/fix_staging_deployment.sh scripts/fix_staging_firewall.sh scripts/fix_job_timeout.py
```

### **2. Restart Containers with Timeout Fixes (YOU DID TIMEOUT FIXES)**
```bash
# Restart backend and worker with new timeout settings
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging restart backend-staging worker-staging

# Wait for restart
sleep 10

# Check if containers are running
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps
```

### **3. Fix Staging Deployment & Monitoring (NETWORK CONFLICT FIXED)**
```bash
# This should now work (network conflict resolved)
./scripts/fix_staging_deployment.sh
```

### **4. Fix Firewall for Prometheus/Grafana Access**
```bash
# Open firewall ports
./scripts/fix_staging_firewall.sh
```

### **5. Test Everything**
```bash
# Test staging application (NEW PORT 8082)
curl http://localhost:8082/

# Test backend health (NEW PORT 8001)  
curl http://localhost:8001/health

# Test Prometheus
curl http://localhost:9090/-/healthy

# Test Grafana
curl http://localhost:3001/api/health

# Check all container status
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps
```

---

## **Expected Results After Fixes**

✅ **Application**: http://13.126.173.223:8082/ (NEW PORT)
✅ **Prometheus**: http://13.126.173.223:9090/
✅ **Grafana**: http://13.126.173.223:3001/ (admin / staging_admin_2025_secure)
✅ **Jobs complete beyond 40%** (timeout increased to 15 minutes)

---

## **If Still Issues**

### **Check Container Logs**
```bash
# Backend logs
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs backend-staging --tail=20

# Worker logs  
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs worker-staging --tail=20

# Prometheus logs
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs prometheus --tail=10

# Grafana logs
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs grafana --tail=10
```

### **Force Cleanup (Last Resort)**
```bash
# Stop everything
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans

# Clean up
docker system prune -f

# Restart
./scripts/fix_staging_deployment.sh
``` 