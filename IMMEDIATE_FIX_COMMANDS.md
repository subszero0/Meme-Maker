# 🚨 IMMEDIATE FIX COMMANDS - UPDATED

## **Run These Commands NOW on Your Server**

### **1. CRITICAL: Stop Conflicting Services**
```bash
# Stop everything first to resolve port conflicts
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans

# Check what's using port 8081
sudo netstat -tulpn | grep :8081

# If something is still running on 8081, kill it:
sudo lsof -ti:8081 | xargs -r sudo kill -9
```

### **2. Fix Port Conflicts in Monitoring**
```bash
# Change cAdvisor port from 8081 to 8083 (8081 conflicts with staging app)
sed -i 's/"8081:8080"/"8083:8080"/g' docker-compose.staging.monitoring.yml

# Verify the change
grep -n "8083:8080" docker-compose.staging.monitoring.yml
```

### **3. Fix Script Permissions**
```bash
chmod +x scripts/fix_staging_deployment.sh scripts/fix_staging_firewall.sh scripts/fix_job_timeout.py
```

### **4. Restart Everything with Fixed Ports**
```bash
# Build with no cache to ensure latest changes
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging build --no-cache

# Start services
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

# Wait for startup
sleep 15

# Check all services are running
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps
```

### **5. Open Firewall Ports**
```bash
# Open necessary ports
./scripts/fix_staging_firewall.sh
```

### **6. Test All Services**
```bash
# Test staging application
curl http://localhost:8082/

# Test backend health  
curl http://localhost:8001/health

# Test Prometheus
curl http://localhost:9090/-/healthy

# Test Grafana
curl http://localhost:3001/api/health

# Test cAdvisor (NEW PORT)
curl http://localhost:8083/healthz
```

---

## **✅ Expected Results After Fixes**

✅ **Application**: http://13.126.173.223:8082/
✅ **Prometheus**: http://13.126.173.223:9090/
✅ **Grafana**: http://13.126.173.223:3001/ (admin / staging_admin_2025_secure)
✅ **cAdvisor**: http://13.126.173.223:8083/ (NEW PORT - no more conflict)

---

## **🔧 GITHUB ACTIONS FIXES**

The parallel workflow issue and SSH key problems need to be fixed:

### **Issues Found:**
1. **Missing SSH Key**: The `ssh-private-key` secret is not configured
2. **Parallel Workflows**: Two workflows running simultaneously causing conflicts

---

## **🆘 If Still Issues**

### **Check Container Status**
```bash
# Check what's running
docker ps -a

# Check port usage
sudo netstat -tulpn | grep -E ':(8001|8082|8083|9090|3001)'

# Check logs if services fail
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs --tail=20
```

### **Complete Reset (Last Resort)**
```bash
# Nuclear option - complete cleanup
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans --volumes
docker system prune -af
docker volume prune -f

# Then restart from step 2
``` 