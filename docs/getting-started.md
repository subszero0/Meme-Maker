# Getting Started with Meme Maker

A complete step-by-step guide to set up and run the Meme Maker application from scratch.

## Prerequisites

Before we start, you'll need to install the following software on your computer:

### 1. Install Git
Git is used for version control and downloading the code.

**Windows:**
- Download from [https://git-scm.com/download/windows](https://git-scm.com/download/windows)
- Run the installer and follow the setup wizard
- Keep all default settings

**macOS:**
- Install using Homebrew: `brew install git`
- Or download from [https://git-scm.com/download/mac](https://git-scm.com/download/mac)

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install git
```

### 2. Install Docker
Docker is used to run the application and its dependencies.

**Windows:**
- Download Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
- Run the installer and follow the setup wizard
- Restart your computer when prompted
- Start Docker Desktop from the Start menu

**macOS:**
- Download Docker Desktop for Mac from the same link above
- Drag Docker to Applications folder
- Launch Docker from Applications

**Linux (Ubuntu/Debian):**
```bash
# Install Docker
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and log back in for group changes to take effect
```

### 3. Install Node.js (for frontend development)
**All platforms:**
- Download from [https://nodejs.org/](https://nodejs.org/)
- Choose the LTS (Long Term Support) version
- Run the installer and follow the setup wizard

### 4. Install Python (for backend development)
**Windows:**
- Download Python 3.12 from [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Important:** Check "Add Python to PATH" during installation

**macOS:**
```bash
brew install python@3.12
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.12 python3.12-pip python3.12-venv
```

---

## Step 1: Download the Code

1. **Open your terminal/command prompt:**
   - **Windows:** Press `Win + R`, type `cmd`, press Enter
   - **macOS:** Press `Cmd + Space`, type `terminal`, press Enter
   - **Linux:** Press `Ctrl + Alt + T`

2. **Navigate to where you want to store the project:**
   ```bash
   # Windows
   cd C:\Users\YourUsername\Desktop
   
   # macOS/Linux
   cd ~/Desktop
   ```

3. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Meme-Maker.git
   cd Meme-Maker
   ```

---

## Step 2: Set Up Environment Variables

1. **Copy the environment template:**
   ```bash
   # Windows
   copy env.template .env
   
   # macOS/Linux
   cp env.template .env
   ```

2. **Edit the environment file:**
   Open `.env` in a text editor (Notepad on Windows, TextEdit on macOS, or nano on Linux) and update these values:

   ```env
   # Basic Configuration
   REDIS_URL=redis://localhost:6379
   
   # MinIO (Local S3-compatible storage)
   MINIO_ACCESS_KEY=admin
   MINIO_SECRET_KEY=admin12345
   AWS_ENDPOINT_URL=http://localhost:9000
   S3_BUCKET=clips
   
   # Application Settings
   ENV=development
   LOG_LEVEL=INFO
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   
   # Worker Settings
   WORKER_CONCURRENCY=2
   MAX_CLIP_DURATION=180
   ```

---

## Step 3: Start the Application

### Quick Start (Recommended for first-time users)

1. **Make sure Docker is running:**
   - Look for Docker icon in your system tray/menu bar
   - If not running, start Docker Desktop

2. **Start all services with one command:**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the backend and worker containers
   - Start Redis (for job queue)
   - Start MinIO (for file storage)
   - Start the backend API
   - Start the worker process
   - Build and serve the frontend

3. **Wait for everything to start:**
   - You'll see lots of log messages
   - Wait until you see messages like:
     ```
     meme-backend | INFO: Uvicorn running on http://0.0.0.0:8000
     meme-frontend | ready - started server on 0.0.0.0:3000
     ```

### Alternative: Development Mode (for developers)

If you want to run components separately for development:

1. **Start infrastructure services:**
   ```bash
   docker-compose up redis minio -d
   ```

2. **Start the backend:**
   ```bash
   cd backend
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start the worker (in a new terminal):**
   ```bash
   cd backend
   # Activate virtual environment first (same as above)
   python -m app.worker
   ```

4. **Start the frontend (in another new terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Step 4: Access the Application

Once everything is running, you can access:

### 🌐 **Main Application (Frontend)**
- **URL:** [http://localhost:3000](http://localhost:3000)
- This is the main user interface where you'll clip videos

### 🔧 **API Documentation**
- **URL:** [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive API documentation (Swagger UI)

### 📊 **MinIO Storage Interface**
- **URL:** [http://localhost:9001](http://localhost:9001)
- Username: `admin`
- Password: `admin12345`
- View uploaded files and clips

### 🔍 **Health Check**
- **URL:** [http://localhost:8000/health](http://localhost:8000/health)
- Should return `{"status": "healthy"}`

---

## Step 5: Using the Application

Now you can use Meme Maker as an end user:

### 1. **Open the Application**
- Go to [http://localhost:3000](http://localhost:3000) in your web browser
- You should see the Meme Maker homepage

### 2. **Clip a Video**

**Step 2.1: Paste a Video URL**
- Find a public video on YouTube, Instagram, or other supported platforms
- Copy the video URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
- Paste it into the URL input field
- Click "Load Video" or "Get Video Info"

**Step 2.2: Preview the Video**
- The video will load in the preview player
- You can play/pause to find the part you want to clip

**Step 2.3: Set Clip Start and End Times**
- Use the timeline slider to select the start and end points
- Or manually enter times in the format `mm:ss` (e.g., `01:30` for 1 minute 30 seconds)
- Maximum clip length is 3 minutes

**Step 2.4: Start Clipping**
- Check the "I have the right to download this content" checkbox
- Click "Create Clip" or "Download Clip"

**Step 2.5: Download Your Clip**
- The system will process your request (this may take 10-60 seconds)
- Once ready, a download link will appear
- Click to download your clipped video file

### 3. **Check Processing Status**
- If the clip takes time to process, you'll see a progress indicator
- The job queue processes clips in order
- Large files or complex clips may take longer

---

## Step 6: Troubleshooting

### Common Issues and Solutions

**Problem: "Docker is not running"**
- **Solution:** Start Docker Desktop and wait for it to fully load

**Problem: "Port already in use"**
- **Solution:** Stop other applications using the same ports, or change ports in the configuration

**Problem: "Cannot connect to Redis"**
- **Solution:** Make sure Redis container is running: `docker-compose up redis -d`

**Problem: "Frontend not loading"**
- **Solution:** Check if the frontend container is running and accessible at http://localhost:3000

**Problem: "Video download fails"**
- **Solution:** 
  - Ensure the video URL is public and accessible
  - Check that the video platform is supported
  - Verify your internet connection

**Problem: "Clip processing is stuck"**
- **Solution:**
  - Check worker logs: `docker-compose logs worker`
  - Restart the worker: `docker-compose restart worker`

### Viewing Logs

To see what's happening behind the scenes:

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs worker
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f backend
```

### Stopping the Application

When you're done:

```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

---

## Step 7: Production Deployment (Optional)

If you want to deploy this to a server for public access:

### Prerequisites for Production
- A Linux server (VPS) with at least 2GB RAM
- A domain name (e.g., `yourdomain.com`)
- Basic server administration knowledge

### Quick Production Setup

1. **Set up the server:**
   ```bash
   # On your server
   sudo apt update
   sudo apt install docker.io docker-compose git
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **Clone and configure:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Meme-Maker.git
   cd Meme-Maker
   
   # Create production environment
   cp env.template .env.prod
   # Edit .env.prod with production values
   ```

3. **Deploy using the production setup:**
   ```bash
   # Build and tag for production
   git tag v1.0.0
   ./scripts/promote_to_prod.sh v1.0.0
   ```

4. **Set up DNS:**
   - Point your domain to your server's IP address
   - The application will automatically get SSL certificates

---

## Next Steps

### For End Users
- Start clipping videos!
- Share the application with friends
- Report any issues you encounter

### For Developers
- Explore the codebase in `backend/` and `frontend/`
- Check out the API documentation at `/docs`
- Read the development documentation in `docs/`
- Set up monitoring and alerts for production

### For System Administrators
- Set up automated backups
- Configure monitoring and alerting
- Review security settings
- Plan for scaling as usage grows

---

## Support

If you encounter issues:

1. **Check the troubleshooting section above**
2. **View application logs** for error messages
3. **Check GitHub Issues** for known problems
4. **Create a new issue** with detailed information about your problem

---

## Summary

You now have a fully functional Meme Maker application running locally! The application allows users to:

- ✅ Paste video URLs from popular platforms
- ✅ Preview videos and select clip segments
- ✅ Download high-quality video clips
- ✅ Process multiple requests concurrently
- ✅ Monitor system health and performance

The application is production-ready and includes comprehensive monitoring, security features, and deployment automation.

**Quick Access Links:**
- 🌐 **App:** [http://localhost:3000](http://localhost:3000)
- 📚 **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- 💾 **Storage:** [http://localhost:9001](http://localhost:9001)
- ❤️ **Health:** [http://localhost:8000/health](http://localhost:8000/health)

Happy clipping! 🎬✂️ 