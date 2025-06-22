# 🔒 SSL Setup - Final Steps

## Current Status ✅
Your application is now working on HTTP! All containers are running successfully:
- Frontend: Working on http://memeit.pro
- Backend: Running and healthy
- Worker: Processing jobs
- Redis: Connected

## Next: Enable HTTPS 🚀

### Step 1: Update Docker Compose for HTTPS
SSH into your server and run:

```bash
cd ~/Meme-Maker

# First, update docker-compose.yaml to add port 443
nano docker-compose.yaml
```

Add this line under the frontend ports section:
```yaml
frontend:
  # ... existing config ...
  ports:
    - "80:3000"
    - "443:443"  # Add this line
```

### Step 2: Create SSL Directories
```bash
# Create SSL certificate directories
sudo mkdir -p ssl/certs ssl/private
sudo chown -R $USER:$USER ssl/
```

### Step 3: Install Certbot and Get SSL Certificate
```bash
# Install certbot
sudo apt update
sudo apt install snapd -y
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Stop containers temporarily to get certificate
docker-compose down

# Get SSL certificate for your domain
sudo certbot certonly --standalone -d memeit.pro -d www.memeit.pro

# Copy certificates to your ssl directory
sudo cp /etc/letsencrypt/live/memeit.pro/fullchain.pem ssl/certs/memeit.pro.crt
sudo cp /etc/letsencrypt/live/memeit.pro/privkey.pem ssl/private/memeit.pro.key
sudo chown -R $USER:$USER ssl/
```

### Step 4: Restart with HTTPS
```bash
# Start containers with new configuration
docker-compose up -d

# Check all services are running
docker-compose ps
```

### Step 5: Test HTTPS
```bash
# Test HTTPS endpoint
curl -s -o /dev/null -w "HTTPS Status: %{http_code}\n" https://memeit.pro/

# Test API through HTTPS
curl -s -o /dev/null -w "API Status: %{http_code}\n" https://memeit.pro/api/health
```

## 🔍 Troubleshooting

If HTTPS doesn't work:

1. **Check nginx logs:**
```bash
docker-compose logs frontend
```

2. **Check certificate files:**
```bash
ls -la ssl/certs/ ssl/private/
```

3. **Verify port 443 is open:**
```bash
sudo ufw status
sudo ufw allow 443
```

4. **Test certificate validity:**
```bash
openssl x509 -in ssl/certs/memeit.pro.crt -text -noout | grep -A2 "Validity"
```

## ✅ Success Criteria

Your setup is complete when:
- ✅ https://memeit.pro loads the frontend
- ✅ https://memeit.pro/api/health returns 200
- ✅ Video processing works end-to-end
- ✅ HTTP automatically redirects to HTTPS

## 🔄 Certificate Auto-Renewal

Set up automatic renewal:
```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab for auto-renewal
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook "cd /home/ubuntu/Meme-Maker && docker-compose restart frontend"
```

Run these steps and let me know the results! 