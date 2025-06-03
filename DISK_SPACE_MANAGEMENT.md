# Disk Space Management for Meme Maker

This guide helps you understand and manage disk space usage in the Meme Maker project development environment.

## 🚨 Common Disk Space Issues

During development and testing, several components can consume significant disk space:

### 1. Docker Images & Containers (2-8 GB)
- **Backend images**: Multiple versions during builds
- **Worker images**: FFmpeg and dependencies are large
- **Base images**: Node.js, Python, Alpine variants
- **Dangling images**: Failed builds leave orphaned images
- **Build cache**: Docker layer cache grows over time

### 2. Node.js Dependencies (1-3 GB)
- **node_modules**: Frontend dependencies (~500MB-1GB)
- **npm cache**: Global npm cache grows over time
- **Puppeteer**: Downloads full Chromium browser (~300MB)
- **Cypress**: Downloads browser binaries (~500MB)

### 3. Python Environment (500MB-2GB)
- **.venv**: Virtual environment with all packages
- **__pycache__**: Compiled Python bytecode
- **pytest cache**: Test discovery and result cache

### 4. Test Artifacts (100MB-1GB)
- **Coverage reports**: HTML coverage reports
- **Cypress videos/screenshots**: Failed test artifacts
- **Visual regression**: Percy snapshots
- **Log files**: Application and test logs

## 🧹 Automated Cleanup

### Quick Cleanup (PowerShell)
```powershell
# Run the automated cleanup script
.\scripts\cleanup-disk-space.ps1
```

### Manual Cleanup Commands

#### Docker Cleanup
```bash
# Remove all unused containers, networks, images
docker system prune -a --volumes

# Remove build cache specifically
docker builder prune -f

# Remove specific images
docker images | grep meme-maker | awk '{print $3}' | xargs docker rmi
```

#### NPM Cleanup
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules (will need to reinstall)
rm -rf frontend/node_modules
rm -rf node_modules

# Reinstall dependencies
cd frontend && npm ci
```

#### Python Cleanup
```bash
# Remove Python cache
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Remove pytest cache
rm -rf backend/.pytest_cache

# Recreate virtual environment (if needed)
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows
pip install -r backend/requirements.txt
```

#### Test Artifacts Cleanup
```bash
# Remove test reports
rm -rf reports/
rm -rf backend/htmlcov/
rm -rf frontend/coverage/

# Remove Cypress artifacts
rm -rf frontend/cypress/screenshots/
rm -rf frontend/cypress/videos/

# Remove build outputs
rm -rf frontend/out/
rm -rf frontend/.next/
```

## 📊 Monitoring Disk Usage

### Check Current Usage
```powershell
# PowerShell - Get directory sizes
Get-ChildItem -Directory | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    "$($_.Name): $([Math]::Round($size, 2))MB"
}
```

```bash
# Linux/Mac - Get directory sizes
du -sh * | sort -hr
```

### Monitor Docker Usage
```bash
# Check Docker disk usage
docker system df

# Check images by size
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sort -k3 -hr
```

## 🔄 Prevention Strategies

### 1. Optimize Docker Builds
- Use `.dockerignore` to exclude unnecessary files
- Use multi-stage builds to reduce final image size
- Regularly prune Docker system
- Pin base image versions to avoid multiple downloads

### 2. Optimize NPM Dependencies
- Set `PUPPETEER_SKIP_DOWNLOAD=true` when possible
- Use `npm ci` instead of `npm install` in CI
- Configure npm cache location if needed
- Use `--prefer-offline` for faster installs

### 3. Configure Test Tools
- Set Cypress to not download videos for passing tests
- Configure Jest to clean coverage on each run
- Use `pytest --cache-clear` occasionally
- Set up automatic cleanup in CI pipelines

### 4. Development Practices
- Run cleanup script weekly
- Delete feature branches after merging
- Don't commit large test files
- Use `.gitignore` for build artifacts

## 🚀 CI/CD Optimizations

The project includes several optimizations to reduce CI disk usage:

### Docker Build Optimizations
```dockerfile
# Skip unnecessary downloads
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV CYPRESS_INSTALL_BINARY=0

# Use package manager optimizations
RUN npm ci --prefer-offline --no-audit --no-fund
```

### GitHub Actions Optimizations
```yaml
# Cache dependencies
- uses: actions/setup-node@v4
  with:
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json

# Use system Chrome instead of downloading
- name: Install system Chrome
  run: sudo apt-get install -y google-chrome-stable
```

## 📱 Mobile Development Considerations

When adding React Native/mobile components:
- Avoid committing `node_modules` 
- Use `npx react-native clean` regularly
- Configure Metro bundler cache location
- Use `react-native start --reset-cache` when needed

## 🆘 Emergency Cleanup

If you're running out of disk space:

1. **Immediate relief** (removes ~5-10GB):
   ```bash
   docker system prune -a --volumes
   rm -rf frontend/node_modules
   rm -rf .venv
   ```

2. **Full reset** (removes everything, requires full setup):
   ```bash
   git clean -fdx  # ⚠️ This removes ALL untracked files
   ```

3. **Partial reset** (keeps configuration):
   ```bash
   git clean -fdx --exclude=.env --exclude=.vscode
   ```

## 📋 Regular Maintenance Checklist

- [ ] Run cleanup script weekly
- [ ] Monitor Docker image count (`docker images | wc -l`)
- [ ] Check for large directories (`du -sh * | sort -hr`)
- [ ] Clear browser downloads folder
- [ ] Remove old Git branches
- [ ] Update .gitignore for new artifacts

## 🔧 Configuration Files

Key configuration files that help manage disk space:

- `.dockerignore` - Excludes files from Docker context
- `.gitignore` - Prevents committing large files
- `frontend/.env` - Configures build optimizations
- `backend/pytest.ini` - Controls test cache behavior

---

**💡 Pro Tip**: Set up a weekly calendar reminder to run the cleanup script. Your SSD will thank you! 