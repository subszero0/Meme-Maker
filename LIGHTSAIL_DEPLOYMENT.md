# Amazon Lightsail Deployment Guide

## 🌐 **Infrastructure Setup**

This project is deployed on **Amazon Lightsail** (not AWS EC2).

### **Current Configuration:**
- **Service**: Amazon Lightsail
- **Instance**: Ubuntu 
- **Region**: Mumbai, Zone A (ap-south-1a)
- **Static IP**: 13.126.173.223
- **Private IP**: 172.26.5.85
- **Domain**: memeit.pro (registered with one.com)

## 🔧 **Network Configuration**

### **Lightsail Firewall Rules Required:**

To access the application externally, configure these firewall rules in Lightsail console:

1. **Go to**: Lightsail Console → Your Instance → Networking tab
2. **Add these firewall rules:**

| Application | Protocol | Port | Source | Purpose |
|-------------|----------|------|---------|---------|
| Custom | TCP | 22 | Any IP | SSH Access (default) |
| Custom | TCP | 80 | Any IP | HTTP (default) |
| Custom | TCP | 443 | Any IP | HTTPS (default) |
| Custom | TCP | 8082 | Any IP | Staging Application |
| Custom | TCP | 8001 | Any IP | Backend API |
| Custom | TCP | 9090 | Any IP | Prometheus Monitoring |
| Custom | TCP | 3001 | Any IP | Grafana Dashboard |

### **Production Firewall (Restricted Access):**
For production, consider restricting monitoring ports:

| Application | Protocol | Port | Source | Purpose |
|-------------|----------|------|---------|---------|
| Custom | TCP | 8082 | Any IP | Application |
| Custom | TCP | 8001 | Any IP | Backend API |
| Custom | TCP | 9090 | Your Office IP | Prometheus (restricted) |
| Custom | TCP | 3001 | Your Office IP | Grafana (restricted) |

## 🌍 **Domain Configuration**

### **DNS Setup (one.com registrar):**

To connect memeit.pro to your Lightsail instance:

1. **Go to**: one.com DNS management
2. **Add A Record**:
   - **Name**: @ (or blank for root domain)
   - **Value**: 13.126.173.223
   - **TTL**: 3600
3. **Add A Record for www**:
   - **Name**: www
   - **Value**: 13.126.173.223
   - **TTL**: 3600

### **Staging Subdomain (Optional):**
- **Name**: staging
- **Value**: 13.126.173.223
- **TTL**: 3600

## 🚀 **Deployment Commands**

### **SSH Connection:**
```bash
ssh ubuntu@13.126.173.223
```

### **Project Location:**
```bash
cd ~/Meme-Maker-Staging
```

## 📊 **Service URLs**

After configuring Lightsail firewall:

### **Staging Environment:**
- **Application**: http://13.126.173.223:8082/
- **Backend API**: http://13.126.173.223:8001/health
- **Prometheus**: http://13.126.173.223:9090/
- **Grafana**: http://13.126.173.223:3001/ (admin/staging_admin_2025_secure)

### **With Domain (after DNS setup):**
- **Application**: http://staging.memeit.pro/
- **Backend API**: http://staging.memeit.pro:8001/health
- **Prometheus**: http://monitoring.memeit.pro:9090/
- **Grafana**: http://monitoring.memeit.pro:3001/

## ⚠️ **Important Notes**

1. **Not AWS EC2**: This is Lightsail, which has simpler networking than EC2
2. **No Security Groups**: Use Lightsail firewall rules instead
3. **Static IP**: 13.126.173.223 is permanent (won't change on restart)
4. **Backup Strategy**: Use Lightsail snapshots, not EC2 AMIs

## 🔧 **Common Issues**

### **Can't Access Services Externally:**
1. Check Lightsail firewall rules (most common issue)
2. Verify services are running: `docker ps`
3. Check local ports: `ss -tulpn | grep -E "(8082|8001)"`

### **Domain Not Working:**
1. Check DNS propagation: `nslookup memeit.pro`
2. Verify A record points to 13.126.173.223
3. DNS changes can take 24-48 hours to propagate

## 📋 **Deployment Checklist**

- [ ] Lightsail firewall rules configured
- [ ] Services running and healthy
- [ ] Domain DNS configured (optional)
- [ ] SSL certificate configured (for HTTPS)
- [ ] Monitoring stack deployed
- [ ] Backup snapshots scheduled 