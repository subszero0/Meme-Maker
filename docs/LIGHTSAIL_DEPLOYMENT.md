# LightSail Deployment Guide

This guide helps you deploy the Meme Maker application to your AWS LightSail server.

## 🎯 Overview

- **Simple Setup**: No complex AWS services needed
- **Cost Effective**: Use your existing LightSail server
- **Docker-based**: Uses Docker Compose for easy management

## 📋 Prerequisites

- AWS LightSail server (Ubuntu)
- SSH access to your server
- Domain name (optional)

## 🚀 Initial Server Setup

### 1. Connect to Your LightSail Server

```bash
ssh ubuntu@YOUR_LIGHTSAIL_IP
```

### 2. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
exit
```

### 4. Clone Your Repository

```bash
ssh ubuntu@YOUR_LIGHTSAIL_IP
git clone https://github.com/YOUR_USERNAME/Meme-Maker.git /home/ubuntu/meme-maker
cd /home/ubuntu/meme-maker
```

## ⚙️ Configure Environment

### 1. Create Environment File

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

### 2. Basic Configuration

```env
# Basic settings for LightSail
REDIS_HOST=redis
REDIS_PORT=6379
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=/app/storage
MAX_CLIP_SECONDS=30

# Security
SECRET_KEY=your-very-long-random-secret-key-here

# Application
APP_NAME=Meme Maker
DEBUG=false
```

## 🐳 Deploy with Docker

### 1. Build and Start Services

```bash
# Build the application
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Verify Deployment

```bash
# Check if services are running
curl http://localhost:8000/health

# View logs
docker-compose logs -f backend
```

## 🌐 Configure Nginx (Optional)

### 1. Install Nginx

```bash
sudo apt install nginx -y
```

### 2. Configure Nginx

Create `/etc/nginx/sites-available/meme-maker`:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/meme-maker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔄 Update Deployment

### Simple Update Script

Create `update.sh`:

```bash
#!/bin/bash
set -e

echo "🔄 Updating Meme Maker..."

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "✅ Update complete!"
```

Make it executable:

```bash
chmod +x update.sh
```

## 📊 Monitoring

### 1. Check Service Status

```bash
# Docker services
docker-compose ps

# System resources
htop

# Disk usage
df -h
```

### 2. View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs worker
docker-compose logs redis
```

## 🔧 Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   sudo netstat -tulpn | grep :8000
   sudo fuser -k 8000/tcp
   ```

2. **Docker permission errors**:
   ```bash
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

3. **Out of disk space**:
   ```bash
   docker system prune -a
   docker volume prune
   ```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Redis connection
docker-compose exec redis redis-cli ping

# Frontend build
curl http://localhost:3000
```

## 🔐 Security Recommendations

1. **Firewall Setup**:
   ```bash
   sudo ufw allow ssh
   sudo ufw allow http
   sudo ufw allow https
   sudo ufw enable
   ```

2. **Regular Updates**:
   ```bash
   # System updates
   sudo apt update && sudo apt upgrade -y
   
   # Application updates
   ./update.sh
   ```

3. **Backup Important Data**:
   ```bash
   # Backup configuration
   tar -czf backup-$(date +%Y%m%d).tar.gz backend/.env docker-compose.yml
   ```

## 🎉 Next Steps

1. **Domain Setup**: Point your domain to LightSail IP
2. **SSL Certificate**: Use Let's Encrypt with Certbot
3. **Monitoring**: Set up basic monitoring with logs
4. **Backups**: Regular backups of your configuration

---

**Need Help?** Check the logs first:
```bash
docker-compose logs --tail=50 backend
``` 