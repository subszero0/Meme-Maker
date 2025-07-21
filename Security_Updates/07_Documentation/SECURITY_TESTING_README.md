# Security Testing Environment

This document describes the isolated security testing environment for the Meme Maker application.

## Overview

The security testing environment is completely isolated from production and development environments to ensure safe security testing without affecting live services.

## Components

### 🐳 Docker Compose Configuration
- **File**: `docker-compose.security-test.yml`
- **Network**: `security-test-network` (172.30.0.0/24)
- **Ports**: Different ports to avoid conflicts
  - Backend: `8001:8000`
  - Frontend: `3001:3000`
  - Redis: `6380:6379`

### 📁 Isolated Data Directories
- `storage-security-test/` - Isolated file storage
- `logs-security-test/` - Security test logs
- `temp-security-test/` - Temporary files for testing

### 🔧 Environment Configuration
- **File**: `.env.security-test`
- Contains safe test values and security testing flags
- Includes test injection payloads for validation testing

## Security Features

### Container Security
- **Resource Limits**: 512MB memory, 0.5 CPU cores
- **Capabilities**: Dropped ALL, added only NET_BIND_SERVICE
- **Security Options**: `no-new-privileges:true`
- **Network Isolation**: Custom bridge network

### yt-dlp Sandboxing
- **Strict Sandbox Mode**: Enhanced containment
- **Memory Limits**: 256MB for yt-dlp processes
- **Timeout Limits**: 30-second maximum execution
- **Domain Restrictions**: Limited to approved domains

## Usage

### Starting the Security Test Environment
```bash
# Start all services
docker-compose -f docker-compose.security-test.yml --env-file .env.security-test up -d

# Check status
docker-compose -f docker-compose.security-test.yml ps

# View logs
docker-compose -f docker-compose.security-test.yml logs -f
```

### Accessing Services
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **Redis**: localhost:6380

### Stopping the Environment
```bash
# Stop all services
docker-compose -f docker-compose.security-test.yml down

# Remove volumes (clean slate)
docker-compose -f docker-compose.security-test.yml down -v
```

## Test Data

### Safe Test URLs
- YouTube: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Instagram: `https://www.instagram.com/p/test/`
- Facebook: `https://www.facebook.com/watch/?v=test`

### Security Test Payloads
The environment includes pre-configured test payloads for:
- SQL Injection testing
- XSS payload testing
- Command injection testing
- Path traversal testing

## Monitoring

### Log Collection
All security test activities are logged to:
- Container logs: `docker-compose logs`
- Application logs: `logs-security-test/`
- System logs: Docker daemon logs

### Network Monitoring
- Isolated network prevents external access
- All traffic contained within security-test-network
- No production data exposure risk

## Security Testing Phases

### Phase 1: Static Analysis
Run security scanners against the isolated codebase:
```bash
# Backend security scanning
cd backend
poetry run bandit -r . -f json -o ../logs-security-test/bandit_report.json
poetry run safety check --json > ../logs-security-test/safety_report.json
```

### Phase 2: Dynamic Analysis
Test running services in the isolated environment:
```bash
# API endpoint testing
curl http://localhost:8001/api/v1/health

# Frontend vulnerability testing
# Use browser developer tools against http://localhost:3001
```

### Phase 3: Penetration Testing
Conduct security tests against the isolated environment:
- Input validation testing
- Authentication bypass attempts
- Rate limiting validation
- File upload security testing

## Cleanup

### Regular Cleanup
```bash
# Clean test data
rm -rf storage-security-test/*
rm -rf logs-security-test/*
rm -rf temp-security-test/*

# Reset containers
docker-compose -f docker-compose.security-test.yml down -v
docker-compose -f docker-compose.security-test.yml up -d
```

### Complete Removal
```bash
# Remove all security test artifacts
docker-compose -f docker-compose.security-test.yml down -v --rmi all
rm -rf storage-security-test/
rm -rf logs-security-test/
rm -rf temp-security-test/
```

## Safety Notes

⚠️ **IMPORTANT SAFETY REMINDERS**

1. **Isolated Environment**: This environment is completely isolated from production
2. **Test Data Only**: Never use real user data or production credentials
3. **Network Isolation**: Custom network prevents external exposure
4. **Resource Limits**: Containers have strict resource limitations
5. **Clean State**: Always start with clean state for each test session
6. **Log Security**: Security test logs may contain sensitive test data

## Integration with Security Audit

This environment supports all phases of the comprehensive security audit:
- **Phase 0**: Tool setup and environment preparation
- **Phase 1**: Discovery and reconnaissance
- **Phase 2**: Automated security scanning
- **Phase 3**: Manual code security review
- **Phase 4**: Penetration testing
- **Phase 5**: Infrastructure security review

The isolated environment ensures all security testing can be conducted safely without risk to production systems. 