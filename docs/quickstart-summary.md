# Meme Maker - Getting Started Options

Choose the method that best fits your experience level and needs:

## 🎯 For Complete Beginners

**👉 Start here if you've never used Docker or Git before.**

### Option 1: Automated Setup Scripts
The easiest way to get started with zero technical knowledge:

#### Windows Users
1. Download this repository as ZIP and extract it
2. Open PowerShell as Administrator
3. Navigate to the extracted folder
4. Run: `.\scripts\quick-start.ps1`

#### macOS/Linux Users  
1. Download this repository as ZIP and extract it
2. Open Terminal
3. Navigate to the extracted folder
4. Run: `chmod +x scripts/quick-start.sh && ./scripts/quick-start.sh`

### Option 2: Complete Step-by-Step Guide
**📖 [Follow the Complete Getting Started Guide](getting-started.md)**

This comprehensive guide covers:
- Installing all prerequisites (Git, Docker, etc.)
- Downloading and setting up the application
- Starting and using the application
- Troubleshooting common issues
- Understanding what each component does

---

## ⚡ For Users with Docker Experience

### Option 3: Docker Quick Start
If you already have Docker installed:

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Meme-Maker.git
cd Meme-Maker

# Start application
docker-compose up --build

# Access at http://localhost:3000
```

### Option 4: Production Mode
For testing the production configuration locally:

```bash
# Use production Docker Compose
docker-compose -f infra/production/docker-compose.prod.yml up --build

# Access at http://localhost:80
```

---

## 🛠️ For Developers

### Option 5: Development Environment
For active development with hot reload:

```bash
# Start infrastructure only
docker-compose up redis minio -d

# Backend (terminal 1)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Worker (terminal 2)  
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m app.worker

# Frontend (terminal 3)
cd frontend
npm install
npm run dev
```

### Option 6: Component Testing
Test individual components:

```bash
# Test backend only
cd backend && python -m pytest

# Test frontend only
cd frontend && npm test

# Full smoke test
./scripts/run_smoke_tests.sh http://localhost:8000
```

---

## 🌐 For Production Deployment

### Option 7: VPS Deployment
Deploy to a real server:

```bash
# Tag a release
git tag v1.0.0
git push origin v1.0.0

# Automated deployment via GitHub Actions
# Or manual deployment:
./scripts/promote_to_prod.sh v1.0.0
```

See **[Release Checklist](release-checklist.md)** for production deployment details.

---

## 📊 What You Get

No matter which option you choose, once running you'll have access to:

### 🌐 **Main Application** - http://localhost:3000
- Modern web interface for video clipping
- Supports YouTube, Instagram, Facebook, Threads, Reddit
- Drag-and-drop timeline for precise trimming
- Real-time video preview
- One-click download of clips

### 🔧 **API Documentation** - http://localhost:8000/docs  
- Interactive Swagger/OpenAPI documentation
- Test all API endpoints directly in browser
- View request/response schemas

### 💾 **Storage Console** - http://localhost:9001
- MinIO web interface (S3-compatible storage)
- View uploaded videos and generated clips
- Monitor storage usage
- **Credentials**: admin / admin12345

### ❤️ **Health Check** - http://localhost:8000/health
- Quick system status check
- Returns JSON status of all components

### 📊 **Monitoring** (in development/production modes)
- **Prometheus**: http://localhost:9090 - Metrics collection
- **Grafana**: http://localhost:3001 - Visual dashboards (admin/admin)
- **Alertmanager**: http://localhost:9093 - Alert management

---

## 🎬 How to Use the App

Once you have it running:

1. **Open** http://localhost:3000 in your browser
2. **Paste** a video URL (e.g., YouTube link)
3. **Wait** for the video to load and preview
4. **Select** start and end times (max 3 minutes)
5. **Check** the "I have rights to download" checkbox
6. **Click** "Create Clip"
7. **Download** your clip when processing completes!

---

## 🆘 Need Help?

1. **Check the troubleshooting** section in the [Getting Started Guide](getting-started.md#step-6-troubleshooting)
2. **View application logs** with `docker-compose logs`
3. **Check GitHub Issues** for known problems
4. **Create a new issue** with your system details and error messages

---

## 📝 Summary

| Experience Level | Recommended Option | Time to Setup |
|---|---|---|
| **Beginner** | Automated Scripts | 5-10 minutes |
| **Some Docker experience** | Docker Quick Start | 2-5 minutes |
| **Developer** | Development Environment | 10-15 minutes |
| **DevOps/SysAdmin** | Production Deployment | 30-60 minutes |

**Choose your path and start clipping videos! 🎬✂️** 