
# Lightsail Deployment Guide for Meme Maker

## 🎯 Overview

Your Meme Maker application is configured for **Amazon Lightsail deployment with local storage** - no complex AWS infrastructure or S3 required!

**Current Setup**:
- ✅ Local file storage (migrated from S3)
- ✅ Lightsail instance hosting
- ✅ Docker Compose deployment
- ✅ No AWS ECS/ECR complexity

---

## 🚨 Important: No AWS Keys Needed for File Storage

**Why AWS keys were mentioned**: The original deployment guide incorrectly assumed AWS ECS deployment. Your application uses **Lightsail with local storage** - much simpler!

**What you actually need**:
- Amazon Lightsail instance (2GB RAM, 60GB SSD)
- Docker and Docker Compose
- Domain name (optional)
- SSH access to your server

---

## 📋 Pre-Deployment Checklist

### 1. Lightsail Instance Setup
- [ ] Lightsail instance running (Ubuntu/Debian recommended)
- [ ] SSH access configured
- [ ] Domain pointed to Lightsail IP (optional)
- [ ] Docker and Docker Compose installed

### 2. Repository Access
- [ ] Git installed on Lightsail instance
- [ ] SSH key or access token for GitHub

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Lightsail Instance

```bash
# SSH into your Lightsail instance
ssh -i your-key.pem ubuntu@your-lightsail-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Install Git (if not installed)
sudo apt install git -y

# Logout and login again for Docker group to take effect
exit
```

### Step 2: Clone Repository

```bash
# SSH back in
ssh -i your-key.pem ubuntu@your-lightsail-ip

# Clone your repository
git clone https://github.com/subszero0/Meme-Maker.git
cd Meme-Maker

# Switch to main branch if needed
git checkout main
```

### Step 3: Configure Environment

```bash
# Create production environment file
cp env.template .env

# Edit environment for production
nano .env
```

**Production Environment Configuration**:
```bash
# Application Settings
DEBUG=false
ENVIRONMENT=production

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_DB=0

# Storage Configuration - LOCAL ONLY (no S3)
STORAGE_BACKEND=local
CLIPS_DIR=/app/clips
BASE_URL=https://yourdomain.com  # or http://your-lightsail-ip

# Worker Configuration
MAX_CONCURRENT_JOBS=20
JOB_TIMEOUT=300

# Security
CORS_ORIGINS=["https://yourdomain.com", "http://your-lightsail-ip"]

# Remove/comment out all S3/AWS settings - not needed!
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# S3_BUCKET=
```

### Step 4: Deploy Application

```bash
# Create storage directory
sudo mkdir -p /opt/meme-maker/storage
sudo chown $USER:$USER /opt/meme-maker/storage

# Start the application
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Configure Reverse Proxy (Optional but Recommended)

If you want to use a domain name:

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/meme-maker
```

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # API and WebSocket proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # File serving optimization (optional)
    location /api/v1/jobs/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Add caching headers for downloads
        add_header Cache-Control "public, max-age=3600";
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/meme-maker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Set Up SSL (Optional)

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

---

## 🔄 Step 7: Automated Updates

### Create Update Script

```bash
# Create update script
nano ~/update-meme-maker.sh
```

```bash
#!/bin/bash
cd /home/ubuntu/Meme-Maker

# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Show status
docker-compose ps
echo "✅ Meme Maker updated successfully!"
```

```bash
# Make script executable
chmod +x ~/update-meme-maker.sh
```

### Set Up Automatic Cleanup

```bash
# Create cleanup script
nano ~/cleanup-old-files.sh
```

```bash
#!/bin/bash
# Clean up files older than 24 hours

CLIPS_DIR="/opt/meme-maker/storage"
find $CLIPS_DIR -name "*.mp4" -type f -mtime +1 -delete
find $CLIPS_DIR -type d -empty -delete

echo "🧹 Cleanup completed: $(date)"
```

```bash
# Make executable
chmod +x ~/cleanup-old-files.sh

# Add to crontab
crontab -e
# Add this line:
0 2 * * * /home/ubuntu/cleanup-old-files.sh >> /var/log/meme-maker-cleanup.log 2>&1
```

---

## 🚦 Step 8: Verification & Testing

### Health Checks

```bash
# Test local health endpoint
curl -f http://localhost:8000/health

# Test external access (if domain configured)
curl -f https://yourdomain.com/api/health

# Test video processing
curl -X POST https://yourdomain.com/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Check Storage

```bash
# Check storage usage
df -h /opt/meme-maker/storage

# Check running containers
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs worker
docker-compose logs frontend
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Containers Not Starting
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild if needed
docker-compose build --no-cache
```

#### 2. Storage Permission Issues
```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/meme-maker/storage
sudo chmod -R 755 /opt/meme-maker/storage
```

#### 3. Out of Disk Space
```bash
# Check disk usage
df -h

# Manual cleanup
find /opt/meme-maker/storage -name "*.mp4" -type f -mtime +1 -delete

# Clean Docker
docker system prune -a
```

#### 4. Application Not Accessible
```bash
# Check if ports are open
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000

# Check Nginx status
sudo systemctl status nginx

# Check firewall
sudo ufw status
```

---

## 📊 Monitoring & Maintenance

### Daily Checks
```bash
# Check application health
curl -f http://localhost:8000/health

# Check disk usage
df -h

# Check container status
docker-compose ps
```

### Weekly Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up Docker
docker system prune

# Check logs for errors
docker-compose logs | grep -i error
```

### Monitor Storage Usage
```bash
# Add to monitoring script
#!/bin/bash
USAGE=$(df /opt/meme-maker/storage | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
    echo "⚠️  Storage usage is ${USAGE}% - cleanup recommended"
fi
```

---

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ All containers are running (`docker-compose ps`)
- ✅ Health endpoint responds (`curl http://localhost:8000/health`)
- ✅ Frontend loads in browser
- ✅ Video processing works end-to-end
- ✅ Files are stored locally (no S3 dependencies)
- ✅ Automatic cleanup is working

---

## 🔄 Updating Production

### For Code Changes
```bash
# SSH to Lightsail
ssh -i your-key.pem ubuntu@your-lightsail-ip

# Run update script
~/update-meme-maker.sh
```

### For Configuration Changes
```bash
# Edit environment
nano .env

# Restart containers
docker-compose restart
```

---

## 💡 Key Advantages of This Setup

1. **Simplified Architecture**: No complex AWS services
2. **Cost Effective**: Fixed Lightsail pricing, no storage charges
3. **Better Performance**: Local file access vs network calls
4. **Easier Debugging**: Direct server access and local logs
5. **No AWS Dependencies**: Pure Docker Compose deployment

---

## 📞 Support

- **Logs**: `docker-compose logs [service-name]`
- **Storage Stats**: Check `/opt/meme-maker/storage`
- **System Resources**: `htop`, `df -h`, `docker stats`
- **GitHub Repository**: https://github.com/subszero0/Meme-Maker

**Remember**: This setup uses local storage only - no AWS keys or S3 configuration needed! 