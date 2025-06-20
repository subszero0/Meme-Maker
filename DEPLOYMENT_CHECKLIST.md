# 🚀 Meme Maker Lightsail Deployment Checklist

Follow this checklist step by step to deploy your Meme Maker application to Amazon Lightsail.

## 📋 Pre-Deployment Requirements

### ✅ Lightsail Instance Setup
- [ ] Amazon Lightsail instance created (recommended: 2GB RAM, 60GB SSD)
- [ ] Ubuntu/Debian OS selected
- [ ] SSH key pair created and downloaded
- [ ] Instance is running and accessible
- [ ] Static IP assigned (optional but recommended)
- [ ] Domain name configured to point to Lightsail IP (optional)

### ✅ Local Preparation
- [ ] Repository is up to date and pushed to GitHub
- [ ] All code changes are committed and pushed

---

## 🎯 Step 1: Connect to Lightsail Instance

```bash
# Connect via SSH (replace with your details)
ssh -i your-key.pem ubuntu@your-lightsail-ip
```

---

## 🛠️ Step 2: Initial Server Setup

Run the production setup script:

```bash
# Clone the repository
git clone https://github.com/subszero0/Meme-Maker.git
cd Meme-Maker

# Make scripts executable
chmod +x scripts/*.sh

# Run production setup
./scripts/production-setup.sh
```

**If Docker group changes were made, logout and login again:**
```bash
exit
ssh -i your-key.pem ubuntu@your-lightsail-ip
cd Meme-Maker
```

### ✅ Verify Installation
- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`
- [ ] Storage directory created: `ls -la /opt/meme-maker/storage`
- [ ] User added to docker group: `groups $USER`

---

## ⚙️ Step 3: Configure Environment

Edit the environment file:

```bash
nano .env
```

**Update these values:**
```bash
# Replace 'yourdomain.com' with your actual domain or IP
BASE_URL=https://yourdomain.com
CORS_ORIGINS=["https://yourdomain.com", "http://your-lightsail-ip:80"]

# For IP-only deployment (no domain):
# BASE_URL=http://your-lightsail-ip
# CORS_ORIGINS=["http://your-lightsail-ip:80"]
```

### ✅ Environment Configuration
- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT=production`
- [ ] `BASE_URL` updated with your domain/IP
- [ ] `CORS_ORIGINS` updated with your domain/IP
- [ ] No S3/AWS keys present (not needed!)

---

## 🚀 Step 4: Deploy Application

```bash
# Run deployment script
./scripts/deploy.sh
```

### ✅ Deployment Verification
- [ ] All containers started: `docker-compose ps`
- [ ] Backend health check passes: `curl http://localhost:8000/health`
- [ ] Frontend responds: `curl http://localhost:80/`
- [ ] No error messages in deployment output

**Check individual service logs if needed:**
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs worker
docker-compose logs redis
```

---

## 🌐 Step 5: Test Application

### Basic Functionality Test
```bash
# Test health endpoint
curl -f http://localhost:8000/health

# Test job creation (optional)
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "start_time": 0, "end_time": 10}'
```

### Browser Test
- [ ] Access application at `http://your-lightsail-ip`
- [ ] Frontend loads correctly
- [ ] Can submit a YouTube URL
- [ ] Video processing works end-to-end

---

## 🔒 Step 6: Set Up Nginx Reverse Proxy (Optional)

**Only needed if you have a domain name:**

```bash
# Install Nginx (if not already done)
sudo apt install nginx -y

# Copy Nginx configuration
sudo cp scripts/nginx-meme-maker.conf /etc/nginx/sites-available/meme-maker

# Update domain name in config
sudo nano /etc/nginx/sites-available/meme-maker
# Replace 'yourdomain.com' with your actual domain

# Enable the site
sudo ln -s /etc/nginx/sites-available/meme-maker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### ✅ Nginx Configuration
- [ ] Configuration file copied and updated
- [ ] Domain name replaced in config
- [ ] Nginx configuration test passes: `sudo nginx -t`
- [ ] Nginx reloaded successfully
- [ ] Application accessible via domain name

---

## 🔐 Step 7: Set Up SSL (Optional)

**Only if you have a domain name:**

```bash
# Install Certbot
sudo apt install snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### ✅ SSL Configuration
- [ ] Certbot installed
- [ ] SSL certificate obtained
- [ ] HTTPS redirection configured
- [ ] Auto-renewal test passes
- [ ] Application accessible via HTTPS

---

## 🔄 Step 8: Set Up Automation

### Update Script
```bash
# Copy update script to home directory
cp scripts/update-meme-maker.sh ~/
chmod +x ~/update-meme-maker.sh
```

### Cleanup Automation
```bash
# Copy cleanup script
sudo cp scripts/cleanup-old-files.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/cleanup-old-files.sh

# Set up cron job
crontab -e
# Add this line:
0 2 * * * /usr/local/bin/cleanup-old-files.sh
```

### ✅ Automation Setup
- [ ] Update script copied to home directory
- [ ] Cleanup script installed system-wide
- [ ] Cron job configured for daily cleanup
- [ ] Test update script: `~/update-meme-maker.sh`

---

## 🎯 Step 9: Final Verification

### Health Checks
```bash
# Application health
curl -f http://localhost:8000/health

# Container status
docker-compose ps

# Storage permissions
ls -la /opt/meme-maker/storage

# Disk usage
df -h /opt/meme-maker/storage
```

### End-to-End Test
- [ ] Access application in browser
- [ ] Submit a YouTube URL
- [ ] Video processes successfully
- [ ] Download works
- [ ] File is stored in `/opt/meme-maker/storage`

### ✅ Success Criteria
- [ ] All containers running (green status)
- [ ] Health endpoint responds with 200
- [ ] Frontend loads without errors
- [ ] Video processing works end-to-end
- [ ] Files stored locally (no S3 dependencies)
- [ ] Automatic cleanup configured

---

## 📊 Step 10: Monitoring Setup

### Basic Monitoring
```bash
# View application logs
docker-compose logs -f

# Monitor system resources
htop

# Check disk usage
df -h

# View container stats
docker stats
```

### Access Monitoring Dashboards (Optional)
- **Prometheus**: `http://your-lightsail-ip:9090`
- **Grafana**: `http://your-lightsail-ip:3001` (admin/admin)

### ✅ Monitoring
- [ ] Can access logs easily
- [ ] System resource monitoring working
- [ ] Optional: Prometheus/Grafana accessible

---

## 🔧 Maintenance Commands

### Daily Operations
```bash
# Check application status
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Check disk usage
df -h /opt/meme-maker/storage
```

### Updates
```bash
# Update application
~/update-meme-maker.sh

# View update logs
docker-compose logs -f
```

### Troubleshooting
```bash
# Restart all services
docker-compose restart

# Rebuild if needed
docker-compose build --no-cache
docker-compose up -d

# Clean Docker cache
docker system prune -a
```

---

## 🎉 Deployment Complete!

### What You've Achieved:
✅ **Simplified Architecture**: No complex AWS services  
✅ **Cost Effective**: Fixed Lightsail pricing, no storage charges  
✅ **Better Performance**: Local file access vs network calls  
✅ **Easier Debugging**: Direct server access and local logs  
✅ **No AWS Dependencies**: Pure Docker Compose deployment  

### Access Your Application:
- **Domain**: `https://yourdomain.com` (if configured)
- **IP**: `http://your-lightsail-ip`
- **Monitoring**: `http://your-lightsail-ip:9090` (Prometheus)
- **Dashboard**: `http://your-lightsail-ip:3001` (Grafana)

### Next Steps:
1. **Monitor**: Keep an eye on disk usage and application performance
2. **Backup**: Consider regular backups of your configuration
3. **Scale**: Monitor usage and upgrade Lightsail instance if needed
4. **Security**: Regular system updates and security monitoring

---

## 📞 Support

**Common Issues:**
- **Containers not starting**: Check logs with `docker-compose logs`
- **Storage issues**: Check permissions and disk space
- **Access issues**: Verify firewall and security group settings
- **Domain issues**: Check DNS propagation and Nginx configuration

**Resources:**
- **Repository**: https://github.com/subszero0/Meme-Maker
- **Logs**: `docker-compose logs [service-name]`
- **System Stats**: `htop`, `df -h`, `docker stats` 