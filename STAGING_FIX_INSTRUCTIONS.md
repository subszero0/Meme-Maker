# 🚨 STAGING DEPLOYMENT FIX INSTRUCTIONS

## 🎯 **Problems Identified**

1. **Container Conflicts**: Wrong docker-compose commands causing name conflicts
2. **Monitoring Not Accessible**: Prometheus (9090) and Grafana (3001) ports blocked
3. **Jobs Failing at 40%**: Timeout issues causing job processing failures

---

## 🔧 **SOLUTION: Run These Commands on Your Server**

### **SSH into your Lightsail server:**
```bash
ssh ubuntu@13.126.173.223
cd ~/Meme-Maker-Staging
```

### **Step 1: Fix Container Conflicts & Restart Services**
```bash
# Download latest fixes
git pull origin monitoring-staging

# Run comprehensive deployment fix
./scripts/fix_staging_deployment.sh
```

**This script will:**
- ✅ Clean up conflicting containers properly
- ✅ Use correct docker-compose files for staging
- ✅ Restart all services including monitoring stack
- ✅ Test all service health checks
- ✅ Provide detailed diagnostics

---

### **Step 2: Fix Firewall for Monitoring Access**
```bash
# Fix firewall and test port accessibility
./scripts/fix_staging_firewall.sh
```

**This script will:**
- ✅ Open ports 9090 (Prometheus) and 3001 (Grafana) in UFW
- ✅ Test local and external port accessibility
- ✅ Provide AWS Lightsail firewall instructions

**⚠️ IMPORTANT**: You must also update AWS Lightsail firewall:
1. Go to: https://lightsail.aws.amazon.com/
2. Click on your instance: `ip-172-26-5-85`
3. Click **Networking** tab
4. Under **Firewall**, click **Add rule**
5. Add these rules:
   - **Custom TCP 9090** (Prometheus)
   - **Custom TCP 3001** (Grafana)

---

### **Step 3: Fix Job Processing Timeouts**
```bash
# Fix timeout issues causing 40% failures
python3 scripts/fix_job_timeout.py

# Restart backend and worker with new timeouts
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging restart backend worker

# Monitor worker logs
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging logs -f worker
```

**This script will:**
- ✅ Increase video processing timeout: 300s → 900s (15 minutes)
- ✅ Increase socket timeouts: 30/45/60s → 90/120/180s
- ✅ Increase Redis timeouts: 10s → 30s
- ✅ Create backup files before changes

---

## 📊 **After Fixes - Expected Results**

### **✅ Application Access**
```
✅ Frontend: http://13.126.173.223:8081/
✅ Backend Health: http://13.126.173.223:8000/health
```

### **✅ Monitoring Access** 
```
✅ Prometheus: http://13.126.173.223:9090/
✅ Grafana: http://13.126.173.223:3001/
   Username: admin
   Password: staging_admin_2025_secure
```

### **✅ Job Processing**
- Jobs should now complete beyond 40%
- Processing time extended to 15 minutes max
- Better error handling and retry logic

---

## 🔍 **Verification Commands**

### **Check All Container Status:**
```bash
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml ps
```

### **Test All Health Endpoints:**
```bash
# Backend
curl http://localhost:8000/health

# Frontend  
curl http://localhost:8081/

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3001/api/health
```

### **Monitor Real-Time Logs:**
```bash
# All services
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml logs -f

# Just worker (for job processing)
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml logs -f worker

# Just monitoring
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml logs -f prometheus grafana
```

---

## 🚨 **If Issues Persist**

### **Container Issues:**
```bash
# Force cleanup all containers
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker system prune -f

# Restart fresh
./scripts/fix_staging_deployment.sh
```

### **Port Access Issues:**
```bash
# Check UFW status
sudo ufw status numbered

# Check if ports are listening
sudo netstat -tlnp | grep -E ':(9090|3001|8081)'

# Test external connectivity
telnet 13.126.173.223 9090
telnet 13.126.173.223 3001
```

### **Job Processing Issues:**
```bash
# Check worker logs for errors
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml logs worker | tail -50

# Check Redis connectivity
docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml exec redis redis-cli ping

# Test a simple job
curl -X POST http://localhost:8000/api/clips/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "start_time": 0, "end_time": 10}'
```

---

## 📈 **Expected Monitoring Metrics**

Once fixed, you should see these in Grafana:
- ✅ **Queue Depth**: Redis job queue metrics
- ✅ **Job Processing Latency**: Time to complete jobs  
- ✅ **Memory Usage**: Container memory consumption
- ✅ **CPU Usage**: Container CPU utilization
- ✅ **Error Rates**: Failed job percentages

---

## 🎉 **Success Criteria**

- [ ] All containers running without conflicts
- [ ] Frontend accessible at :8081
- [ ] Prometheus accessible at :9090
- [ ] Grafana accessible at :3001 with login
- [ ] Jobs complete beyond 40% mark
- [ ] All 4 Grafana dashboard panels showing data

**Run the three fix scripts in order, and your staging environment should be fully operational with comprehensive monitoring!** 