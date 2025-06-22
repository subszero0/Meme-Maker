# Production Server Fix Guide - Step by Step

## 🎯 Overview
We're going to fix two issues on your AWS Lightsail server:
1. Frontend calling localhost instead of using relative URLs
2. Backend API not responding properly

## 📋 Prerequisites
- SSH access to your AWS Lightsail server
- The server IP: 13.126.173.223 (confirmed working)
- Your SSH key file

---

## Step 1: Connect to Your Production Server

### Option A: Using SSH Key File
```bash
ssh -i /path/to/your/key.pem ubuntu@13.126.173.223
```

### Option B: Using Lightsail Browser SSH
1. Go to AWS Lightsail console
2. Find your instance
3. Click "Connect using SSH"

### Verify You're Connected
Once connected, run:
```bash
pwd
ls -la
```
You should see your Meme-Maker directory.

---

## Step 2: Navigate to Project Directory

```bash
cd ~/Meme-Maker
# or wherever your project is located
```

Verify you're in the right place:
```bash
ls -la
# You should see: docker-compose.yaml, frontend-new/, backend/, etc.
```

---

## Step 3: Check Current Status

Let's see what's currently running:
```bash
docker-compose ps
```

This will show you which containers are running/stopped.

---

## Step 4: Upload the Fix Script

### Option A: Create the script directly on server
```bash
nano fix_production_config.py
```
Then copy and paste the script content.

### Option B: Download from your local machine
If you have the script locally, you can transfer it:
```bash
scp -i /path/to/your/key.pem fix_production_config.py ubuntu@13.126.173.223:~/Meme-Maker/
```

---

## Step 5: Run the Fix Script

Make the script executable:
```bash
chmod +x fix_production_config.py
```

Run the fix:
```bash
python3 fix_production_config.py
```

The script will:
1. Create a backup of current state
2. Stop all containers
3. Rebuild frontend and backend with fresh configuration
4. Start all containers
5. Test that everything works

---

## Step 6: Monitor the Process

The fix will take several minutes. You'll see output like:
```
[INFO] 🔧 STARTING PRODUCTION FIX - 2025-01-27
[ACTION] 🔧 Creating backup of current state
[PASS] ✅ Backup created in backup_before_fix_20250127_123456
[ACTION] 🔧 Fixing frontend build configuration
[COMMAND] docker-compose down
[PASS] ✅ Stop all containers - Success
...
```

---

## Step 7: Verify the Fix

After the script completes, test your website:

### Test 1: Check Container Status
```bash
docker-compose ps
```
All containers should show "Up" status.

### Test 2: Test API Directly on Server
```bash
curl https://memeit.pro/api/health
```
Should return: `{"status": "healthy"}` or similar.

### Test 3: Test in Your Browser
1. Go to https://memeit.pro
2. Open DevTools (F12) → Console tab
3. Enter a YouTube URL and click "Let's Go"
4. **You should NOT see any localhost:8000 errors**

---

## Step 8: Troubleshooting

### If the script fails:
1. Check the error messages in the output
2. Run individual commands manually:
   ```bash
   docker-compose down
   docker-compose build --no-cache frontend
   docker-compose build --no-cache backend
   docker-compose up -d
   ```

### If containers won't start:
```bash
docker-compose logs frontend
docker-compose logs backend
```

### If API still returns 404:
```bash
docker-compose exec frontend curl http://backend:8000/health
```

---

## ✅ Success Criteria

You'll know the fix worked when:
- ✅ https://memeit.pro loads without errors
- ✅ No localhost:8000 errors in browser console
- ✅ API health check returns 200: `curl https://memeit.pro/api/health`
- ✅ You can enter a YouTube URL and it processes correctly

---

## 🔄 Rollback Plan

If something goes wrong, you can restore from backup:
```bash
# Find your backup directory
ls -la backup_before_fix_*

# Restore configuration
cp backup_before_fix_*/docker-compose.yaml .
cp backup_before_fix_*/nginx.conf frontend-new/

# Restart with old configuration
docker-compose up -d
```

---

## 📞 Next Steps

Once the fix is complete:
1. Test the website thoroughly
2. The website will work 24/7 without your computer being on
3. You can turn off Docker Desktop on your local machine
4. Users can access https://memeit.pro anytime 