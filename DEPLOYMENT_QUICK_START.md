# 🚀 Quick Start: Deploy to Lightsail

**Ready to deploy in 10 minutes!** Your Meme Maker app is configured for simple Lightsail deployment with local storage.

## ⚡ Prerequisites

1. **Lightsail Instance**: 2GB RAM, Ubuntu 22.04, with SSH access
2. **Domain** (optional): Point your domain to the Lightsail IP
3. **SSH Key**: Downloaded from Lightsail console

---

## 🎯 Deploy in 3 Commands

### Step 1: Connect to Your Server
```bash
ssh -i your-key.pem ubuntu@your-lightsail-ip
```

### Step 2: Clone and Setup
```bash
git clone https://github.com/subszero0/Meme-Maker.git
cd Meme-Maker
chmod +x scripts/*.sh
./scripts/production-setup.sh
```

**Important**: If Docker was just installed, logout and login again:
```bash
exit
ssh -i your-key.pem ubuntu@your-lightsail-ip
cd Meme-Maker
```

### Step 3: Configure and Deploy
```bash
# Edit environment for your domain/IP
nano .env
# Update BASE_URL and CORS_ORIGINS with your domain or IP

# Deploy!
./scripts/deploy.sh
```

---

## ✅ Test Your Deployment

Visit `http://your-lightsail-ip` in your browser and test video processing!

**Health Check:**
```bash
curl http://localhost:8000/health
```

---

## 🔧 Optional: Domain + SSL

If you have a domain:

```bash
# Set up Nginx reverse proxy
sudo cp scripts/nginx-meme-maker.conf /etc/nginx/sites-available/meme-maker
sudo nano /etc/nginx/sites-available/meme-maker  # Update domain
sudo ln -s /etc/nginx/sites-available/meme-maker /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Get SSL certificate
sudo apt install snapd
sudo snap install --classic certbot
sudo certbot --nginx -d yourdomain.com
```

---

## 📈 Ongoing Maintenance

### Update Application
```bash
~/update-meme-maker.sh
```

### Monitor Status
```bash
docker-compose ps
docker-compose logs -f
```

### Auto-cleanup (prevents disk full)
```bash
sudo cp scripts/cleanup-old-files.sh /usr/local/bin/
crontab -e
# Add: 0 2 * * * /usr/local/bin/cleanup-old-files.sh
```

---

## 🎉 You're Live!

Your Meme Maker is now running on Lightsail with:
- ✅ Local file storage (no S3 complexity)
- ✅ Docker containers for reliability
- ✅ Monitoring with Prometheus/Grafana
- ✅ Auto-scaling worker processes

**Access URLs:**
- **App**: `http://your-lightsail-ip` or `https://yourdomain.com`
- **Prometheus**: `http://your-lightsail-ip:9090`
- **Grafana**: `http://your-lightsail-ip:3001` (admin/admin)

**Need Help?** Check `DEPLOYMENT_CHECKLIST.md` for detailed troubleshooting. 