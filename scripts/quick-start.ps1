# Meme Maker Quick Start Script for Windows
# This script will set up and start the Meme Maker application

param(
    [switch]$SkipPrereqs,
    [switch]$ProductionMode
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColoredOutput {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

function Test-Docker {
    try {
        $dockerInfo = docker info 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Header
Write-ColoredOutput "🚀 Meme Maker Quick Start" $InfoColor
Write-ColoredOutput "=========================" $InfoColor
Write-ColoredOutput ""

# Check prerequisites
if (-not $SkipPrereqs) {
    Write-ColoredOutput "🔍 Checking prerequisites..." $InfoColor
    
    # Check Git
    if (-not (Test-Command "git")) {
        Write-ColoredOutput "❌ Git is not installed or not in PATH" $ErrorColor
        Write-ColoredOutput "Please install Git from: https://git-scm.com/download/windows" $WarningColor
        exit 1
    } else {
        Write-ColoredOutput "✅ Git is installed" $SuccessColor
    }
    
    # Check Docker
    if (-not (Test-Command "docker")) {
        Write-ColoredOutput "❌ Docker is not installed or not in PATH" $ErrorColor
        Write-ColoredOutput "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" $WarningColor
        exit 1
    } else {
        Write-ColoredOutput "✅ Docker is installed" $SuccessColor
    }
    
    # Check if Docker is running
    if (-not (Test-Docker)) {
        Write-ColoredOutput "❌ Docker is not running" $ErrorColor
        Write-ColoredOutput "Please start Docker Desktop and wait for it to fully load" $WarningColor
        Write-ColoredOutput "Then run this script again" $InfoColor
        exit 1
    } else {
        Write-ColoredOutput "✅ Docker is running" $SuccessColor
    }
    
    Write-ColoredOutput ""
}

# Create environment file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-ColoredOutput "📝 Creating environment configuration..." $InfoColor
    
    if (Test-Path "env.template") {
        Copy-Item "env.template" ".env"
        Write-ColoredOutput "✅ Environment file created from template" $SuccessColor
    } else {
        Write-ColoredOutput "⚠️  env.template not found, creating basic .env file" $WarningColor
        
        $envContent = @"
# Meme Maker Environment Configuration
REDIS_URL=redis://localhost:6379
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=admin12345
AWS_ENDPOINT_URL=http://localhost:9000
S3_BUCKET=clips
ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
WORKER_CONCURRENCY=2
MAX_CLIP_DURATION=180
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-ColoredOutput "✅ Basic environment file created" $SuccessColor
    }
} else {
    Write-ColoredOutput "✅ Environment file already exists" $SuccessColor
}

Write-ColoredOutput ""

# Determine which compose file to use
$composeFile = "docker-compose.yaml"
if ($ProductionMode) {
    $composeFile = "infra/production/docker-compose.prod.yml"
    Write-ColoredOutput "🏭 Starting in production mode..." $InfoColor
} else {
    Write-ColoredOutput "🛠️  Starting in development mode..." $InfoColor
}

# Check if compose file exists
if (-not (Test-Path $composeFile)) {
    Write-ColoredOutput "❌ Docker Compose file not found: $composeFile" $ErrorColor
    exit 1
}

# Start the application
Write-ColoredOutput "🚀 Starting Meme Maker application..." $InfoColor
Write-ColoredOutput "This may take a few minutes the first time (downloading images)..." $WarningColor
Write-ColoredOutput ""

try {
    # Stop any existing containers
    Write-ColoredOutput "🛑 Stopping any existing containers..." $InfoColor
    docker-compose -f $composeFile down --remove-orphans 2>$null
    
    # Start the application
    Write-ColoredOutput "▶️  Starting application..." $InfoColor
    docker-compose -f $composeFile up --build -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColoredOutput "❌ Failed to start application" $ErrorColor
        exit 1
    }
    
    Write-ColoredOutput "✅ Application started successfully!" $SuccessColor
    Write-ColoredOutput ""
    
    # Wait for services to be ready
    Write-ColoredOutput "⏳ Waiting for services to be ready..." $InfoColor
    Start-Sleep -Seconds 30
    
    # Check service health
    $healthChecks = @(
        @{ Name = "Backend API"; Url = "http://localhost:8000/health"; Expected = "healthy" },
        @{ Name = "Frontend"; Url = "http://localhost:3000"; Expected = $null }
    )
    
    foreach ($check in $healthChecks) {
        try {
            $response = Invoke-WebRequest -Uri $check.Url -TimeoutSec 10 -UseBasicParsing 2>$null
            if ($response.StatusCode -eq 200) {
                Write-ColoredOutput "✅ $($check.Name) is running" $SuccessColor
            } else {
                Write-ColoredOutput "⚠️  $($check.Name) returned status $($response.StatusCode)" $WarningColor
            }
        } catch {
            Write-ColoredOutput "⚠️  $($check.Name) is not yet ready" $WarningColor
        }
    }
    
    Write-ColoredOutput ""
    
    # Display access information
    Write-ColoredOutput "🎉 Meme Maker is now running!" $SuccessColor
    Write-ColoredOutput "================================" $SuccessColor
    Write-ColoredOutput ""
    Write-ColoredOutput "📱 Access the application:" $InfoColor
    Write-ColoredOutput "   🌐 Main App:        http://localhost:3000" $InfoColor
    Write-ColoredOutput "   📚 API Docs:        http://localhost:8000/docs" $InfoColor
    Write-ColoredOutput "   💾 Storage Admin:   http://localhost:9001" $InfoColor
    Write-ColoredOutput "   ❤️  Health Check:   http://localhost:8000/health" $InfoColor
    Write-ColoredOutput ""
    Write-ColoredOutput "🔐 MinIO Storage Credentials:" $InfoColor
    Write-ColoredOutput "   Username: admin" $InfoColor
    Write-ColoredOutput "   Password: admin12345" $InfoColor
    Write-ColoredOutput ""
    Write-ColoredOutput "📋 Useful commands:" $InfoColor
    Write-ColoredOutput "   View logs:          docker-compose logs -f" $InfoColor
    Write-ColoredOutput "   Stop application:   docker-compose down" $InfoColor
    Write-ColoredOutput "   Restart:            docker-compose restart" $InfoColor
    Write-ColoredOutput ""
    Write-ColoredOutput "🎬 To use the app:" $InfoColor
    Write-ColoredOutput "   1. Go to http://localhost:3000" $InfoColor
    Write-ColoredOutput "   2. Paste a video URL (YouTube, Instagram, etc.)" $InfoColor
    Write-ColoredOutput "   3. Select the segment you want to clip" $InfoColor
    Write-ColoredOutput "   4. Click 'Create Clip' and download!" $InfoColor
    Write-ColoredOutput ""
    
    # Try to open the app in browser
    try {
        Write-ColoredOutput "🌐 Opening application in your default browser..." $InfoColor
        Start-Process "http://localhost:3000"
    } catch {
        Write-ColoredOutput "⚠️  Couldn't open browser automatically. Please visit http://localhost:3000 manually." $WarningColor
    }
    
} catch {
    Write-ColoredOutput "❌ Error starting application: $($_.Exception.Message)" $ErrorColor
    Write-ColoredOutput ""
    Write-ColoredOutput "🔍 Troubleshooting:" $InfoColor
    Write-ColoredOutput "   1. Make sure Docker Desktop is running" $InfoColor
    Write-ColoredOutput "   2. Check if ports 3000, 8000, 9000, 9001 are available" $InfoColor
    Write-ColoredOutput "   3. Try running: docker-compose logs" $InfoColor
    Write-ColoredOutput "   4. For more help, see docs/getting-started.md" $InfoColor
    exit 1
}

Write-ColoredOutput "Happy clipping! ��✂️" $SuccessColor 