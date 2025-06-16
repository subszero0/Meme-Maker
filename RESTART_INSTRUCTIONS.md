# 🔄 Complete Restart Instructions

Follow these steps **exactly** to ensure all changes are applied and the resolution picker works correctly.

## Step 1: Stop All Services

Open PowerShell as Administrator and navigate to your project directory:

```powershell
cd "C:\Users\Vivek Subramanian\Desktop\Meme Maker - Local\Meme-Maker"
```

Stop all Docker services:

```powershell
docker-compose down
```

Wait for all containers to stop completely (about 10-15 seconds).

## Step 2: Clean Docker Resources (Optional but Recommended)

Remove any cached images and containers to ensure fresh builds:

```powershell
# Remove stopped containers
docker container prune -f

# Remove unused images 
docker image prune -f

# If you want to be extra thorough (rebuilds everything):
docker system prune -f
```

## Step 3: Rebuild and Start Services

Rebuild all services with the latest code changes:

```powershell
docker-compose up --build
```

**Important**: Wait for all services to be fully ready before testing:

- ✅ Look for: "🚀 Worker starting up..."
- ✅ Look for: "✅ Redis connection successful"  
- ✅ Look for: "⏰ Starting job polling (interval: 2s)"
- ✅ Look for: Backend server ready on port 8000
- ✅ Look for: Frontend ready on port 3000

This usually takes 2-3 minutes for the first build.

## Step 4: Verify Services Are Running

In a new PowerShell window, check that all services are running:

```powershell
docker-compose ps
```

You should see all services with "running" status:
- `meme-maker-backend`
- `meme-maker-worker` 
- `meme-maker-frontend`
- `redis`

## Step 5: Test Resolution Picker (Automated)

Run the debug script to test if resolution picker is working:

```powershell
python test_resolution_debug.py
```

This will automatically test:
1. ✅ Metadata extraction with formats
2. ✅ Job creation with format_id
3. ✅ Worker processing with correct resolution

## Step 6: Test Resolution Picker (Manual)

1. Open browser and go to: http://localhost:3000
2. Paste a YouTube URL (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
3. **IMPORTANT**: Check browser console (F12) for logging messages:
   - Look for: 🎬 ResolutionSelector messages
   - Look for: 🎭 TrimPanel messages  
   - Look for: 🏠 HomePage messages
   - Look for: 🔌 API messages
4. Select a resolution from dropdown
5. Set trim times and submit
6. Monitor processing

## Step 7: Check Docker Logs for Detailed Info

Monitor the logs in real-time to see what's happening:

```powershell
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f worker
docker-compose logs -f backend
```

Look for these log messages that indicate resolution picker is working:
- 🏗️ Backend: Received job creation request
- 🏗️ Backend: format_id received: [format_id]
- 🚀 Backend: Enqueueing job with format: [format_id]
- 🎬 Worker: Using user-selected format: [format_id]

## 🚨 Troubleshooting

### If Resolution Picker Still Not Working:

1. **Check format_id in logs**: Look for "format: None" vs actual format ID
2. **Browser console errors**: Check for JavaScript errors that prevent format selection
3. **API connectivity**: Ensure frontend can reach backend API
4. **Docker networking**: Verify all containers can communicate

### Common Issues:

**Issue**: "format: None" in worker logs
**Solution**: Format ID is not being passed correctly. Check browser console for frontend errors.

**Issue**: ResolutionSelector doesn't load formats
**Solution**: Backend metadata endpoint may be failing. Check backend logs.

**Issue**: Downloads same quality regardless of selection  
**Solution**: Worker is falling back to default format. Check worker logs for format processing.

### Emergency Reset:

If nothing works, perform a complete reset:

```powershell
# Stop everything
docker-compose down

# Remove everything related to the project
docker-compose down --volumes --remove-orphans

# Remove all Docker images for this project
docker image rm $(docker image ls --filter=reference="*meme*" -q) -f

# Rebuild from scratch
docker-compose up --build
```

## Expected Behavior After Fix

✅ **Resolution dropdown** shows multiple options (720p, 1080p, etc.)
✅ **File sizes** displayed next to each resolution  
✅ **Browser console** shows format_id being selected and passed through
✅ **Docker logs** show worker receiving and using the correct format_id
✅ **Downloaded video** matches the selected resolution
✅ **Different resolutions** produce different file sizes

---

**Note**: The comprehensive logging has been added to track the resolution picker at every step. This will help identify exactly where the format_id is being lost if the issue persists. 