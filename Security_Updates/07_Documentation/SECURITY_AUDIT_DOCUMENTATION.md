# SECURITY AUDIT DOCUMENTATION
## Comprehensive Information Gathering for Meme Maker Security Assessment

> **Status**: Phase 0.3 Documentation Gathering  
> **Date**: July 17, 2025  
> **Purpose**: Complete architectural and security context for security audit  

---

## 🏗️ NETWORK ARCHITECTURE

### **Production Deployment Architecture**
```
Internet (HTTPS) → AWS Lightsail Instance (memeit.pro)
    ↓
    nginx (Reverse Proxy + SSL Termination)
    ↓
    Docker Compose Network (172.18.0.0/24)
    ├── Frontend Container (React/Vite) :3000
    ├── Backend Container (FastAPI) :8000
    ├── Worker Container (yt-dlp + FFmpeg)
    ├── Redis Container (Queue + Cache) :6379
    └── Storage (Local filesystem: /app/clips)
```

### **Network Components**
- **External Access**: HTTPS (443) → Lightsail Public IP
- **Internal Communication**: Docker bridge network
- **Service Discovery**: Container names (backend, redis, frontend)
- **Load Balancing**: nginx upstream configuration
- **SSL/TLS**: Let's Encrypt certificates managed by nginx

### **Port Configuration**
- **Production External**: 443 (HTTPS), 80 (HTTP redirect)
- **Development Local**: 3000 (Frontend), 8000 (Backend), 6379 (Redis)
- **Security Testing**: 3001 (Frontend), 8001 (Backend), 6380 (Redis)

---

## 📡 API DOCUMENTATION

### **Core API Endpoints**

#### **Health & Status**
- `GET /health` - Service health check
- `GET /` - Root endpoint with API information
- `GET /metrics` - Prometheus metrics (if enabled)

#### **Video Metadata**
- `POST /api/v1/metadata` - Get video metadata from URL
  ```json
  Request: {"url": "https://youtube.com/watch?v=..."}
  Response: {
    "title": "Video Title",
    "duration": 180.5,
    "thumbnail_url": "https://...",
    "formats": [{"format_id": "720p", "height": 720, ...}]
  }
  ```

#### **Job Management**
- `POST /api/v1/jobs` - Create video clipping job
  ```json
  Request: {
    "url": "https://youtube.com/watch?v=...",
    "in_ts": 30.0,
    "out_ts": 90.0,
    "format_id": "720p"
  }
  Response: {
    "id": "uuid",
    "status": "queued",
    "created_at": "2025-07-17T19:30:00Z"
  }
  ```

- `GET /api/v1/jobs/{job_id}` - Get job status
  ```json
  Response: {
    "id": "uuid",
    "status": "completed|processing|failed",
    "progress": 85,
    "download_url": "https://...",
    "error_code": null
  }
  ```

#### **Video Proxy**
- `GET /api/v1/video/proxy?url={video_url}` - Proxy video content (CORS bypass)

#### **Admin Endpoints** (Phase 3)
- `GET /api/v1/admin/cache/stats` - Cache statistics
- `POST /api/v1/admin/cache/clear` - Clear cache
- `GET /api/v1/admin/storage/info` - Storage backend information

### **Security Headers Applied**
```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
```

### **CORS Configuration**
- **Development**: `http://localhost:3000`, `http://localhost:8080`
- **Production**: `https://memeit.pro`, `https://www.memeit.pro`
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS, HEAD
- **Allowed Headers**: Content-Type, Authorization, X-Requested-With, Cache-Control

---

## 🛠️ DEPLOYMENT CONFIGURATION

### **Docker Compose Stack**

#### **Production (docker-compose.yaml)**
```yaml
services:
  redis:
    image: redis:7.2.5-alpine
    ports: ["6379:6379"]
    healthcheck: redis-cli ping
  
  backend:
    build: Dockerfile.backend
    ports: ["8000:8000"]
    environment:
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
      - BASE_URL=https://memeit.pro
      - CORS_ORIGINS=["https://memeit.pro", "https://www.memeit.pro"]
  
  frontend:
    build: ./frontend-new
    ports: ["3000:3000"]
    
  worker:
    build: Dockerfile.worker
    depends_on: [redis]
```

#### **Development (docker-compose.dev.yaml)**
```yaml
# Similar structure with:
# - Different ports to avoid conflicts
# - Volume mounts for hot reload
# - Development environment variables
# - Debug logging enabled
```

#### **Security Testing (docker-compose.security-test.yml)**
```yaml
# Isolated network configuration:
# - Custom subnet: 172.30.0.0/24
# - Resource limits: 512MB memory, 0.5 CPU
# - Security options: no-new-privileges, dropped capabilities
# - Enhanced yt-dlp sandboxing
```

### **Container Security Configuration**
- **Base Images**: Alpine Linux (minimal attack surface)
- **Non-root users**: All services run as non-root
- **Resource limits**: Memory and CPU constraints
- **Security options**: `no-new-privileges:true`, capability dropping
- **Network isolation**: Custom bridge networks

### **Environment Variables**
- **SECRET_KEY**: Application secret (production)
- **REDIS_URL**: Redis connection string
- **INSTAGRAM_COOKIES_B64**: Base64-encoded authentication cookies
- **CORS_ORIGINS**: Allowed origins for CORS
- **LOG_LEVEL**: Logging verbosity
- **MAX_CONCURRENT_JOBS**: Queue capacity limit

---

## 🔗 THIRD-PARTY INTEGRATIONS

### **Core Dependencies**

#### **Backend Dependencies (Python)**
```toml
[tool.poetry.dependencies]
fastapi = "^0.112.0"          # Web framework
uvicorn = "^0.30.3"           # ASGI server
redis = "^5.0.4"              # Queue and caching
rq = "*"                      # Job queue
yt-dlp = "^2025.6.25"         # Video extraction
pydantic = "^2.7.1"           # Data validation
boto3 = "^1.34.0"             # AWS SDK (legacy, not used)
httpx = "^0.25.2"             # HTTP client
requests = "^2.32.4"          # HTTP requests
prometheus-client = "^0.19.0"  # Metrics
loguru = "^0.7.2"             # Logging

[tool.poetry.group.dev.dependencies]
bandit = "^1.8.6"             # Security linting
safety = "^3.6.0"             # Vulnerability scanning
pytest = "^8.3.2"             # Testing
mypy = "^1.7.1"               # Type checking
black = "^23.11.0"            # Code formatting
```

#### **Frontend Dependencies (Node.js)**
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.10.0",
    "@tanstack/react-query": "^5.56.2",
    "react-player": "^2.16.0",
    "react-router-dom": "^6.26.2",
    "@radix-ui/react-*": "Various UI components",
    "tailwindcss": "^3.4.11",
    "typescript": "^5.5.3"
  },
  "devDependencies": {
    "vite": "^5.4.1",
    "vitest": "^3.2.3",
    "cypress": "^14.4.1",
    "@testing-library/react": "^16.3.0"
  }
}
```

### **External Services**

#### **Video Platform APIs**
- **YouTube**: Via yt-dlp (no direct API integration)
- **Instagram**: Via yt-dlp with cookie authentication
- **Facebook**: Via yt-dlp with cookie authentication  
- **Reddit**: Via yt-dlp
- **TikTok**: Via yt-dlp (if supported)

#### **Content Delivery**
- **Video Proxy**: Internal proxy service for CORS bypass
- **Thumbnail Caching**: Redis-based caching
- **File Storage**: Local filesystem (migrated from S3)

#### **Monitoring & Observability**
- **Prometheus**: Metrics collection (optional)
- **Grafana**: Metrics visualization (not deployed)
- **Application Logs**: Loguru + stdout/stderr

#### **Development Tools**
- **Docker**: Containerization platform
- **GitHub Actions**: CI/CD pipeline
- **AWS Lightsail**: Production hosting
- **Let's Encrypt**: SSL certificate management

### **Authentication & Authorization**
- **No user authentication**: Anonymous service
- **API authentication**: None (public endpoints)
- **Instagram cookies**: For private video access
- **Rate limiting**: IP-based (middleware level)

---

## 🔒 SECURITY CONFIGURATION

### **Current Security Measures**

#### **Transport Security**
- **HTTPS Everywhere**: TLS 1.2+ required
- **HSTS**: Strict Transport Security enabled
- **Certificate Pinning**: Not implemented
- **Perfect Forward Secrecy**: Enabled via nginx

#### **Application Security**
- **Input Validation**: Pydantic models for all endpoints
- **Output Encoding**: JSON responses properly encoded
- **CSRF Protection**: Not implemented (stateless API)
- **XSS Prevention**: CSP headers configured
- **SQL Injection**: N/A (no SQL database)
- **Command Injection**: Partially mitigated (yt-dlp sandboxing needed)

#### **Infrastructure Security**
- **Container Isolation**: Docker with limited capabilities
- **Network Segmentation**: Docker bridge networks
- **Resource Limits**: Memory and CPU constraints
- **File System**: Read-only containers where possible
- **Secrets Management**: Environment variables (not secure)

### **Security Gaps Identified**
1. **No authentication** on admin endpoints
2. **Basic secrets management** (environment variables)
3. **Limited yt-dlp sandboxing** (command injection risk)
4. **No Web Application Firewall**
5. **Basic rate limiting** implementation
6. **No security monitoring** or alerting
7. **No backup encryption** or integrity verification

---

## 📊 MONITORING & LOGGING

### **Application Monitoring**
- **Health Checks**: `/health` endpoint with Redis connectivity
- **Metrics**: Prometheus metrics (optional)
- **Queue Monitoring**: Redis queue depth and job status
- **Performance**: Response time and error rate tracking

### **Security Logging**
- **Access Logs**: nginx access logs
- **Application Logs**: FastAPI request/response logs
- **Error Logs**: Application and container error logs
- **Audit Logs**: No dedicated audit logging

### **Log Management**
- **Storage**: Local files and Docker logs
- **Retention**: No explicit retention policy
- **Analysis**: Manual log review only
- **Alerting**: No automated alerting configured

---

## 🎯 BUSINESS LOGIC & DATA FLOW

### **Core Business Process**
1. **User Input**: Video URL submission
2. **Metadata Extraction**: yt-dlp video information retrieval
3. **Job Creation**: Queue job for video processing
4. **Video Processing**: Download, trim, and process video
5. **File Delivery**: Provide download link
6. **Cleanup**: Automatic file deletion after download

### **Data Classification**
- **Public Data**: Video metadata, thumbnails
- **Temporary Data**: Downloaded videos, processed clips
- **User Data**: IP addresses (logs only), no PII stored
- **Configuration Data**: Environment variables, cookies

### **Data Flow Security**
- **Input Sanitization**: URL validation, parameter checking
- **Data in Transit**: HTTPS for all communications
- **Data at Rest**: Local file storage, no encryption
- **Data Retention**: Immediate deletion after download
- **Cross-Border**: No specific data residency requirements

---

## ⚡ PERFORMANCE & SCALABILITY

### **Current Capacity**
- **Concurrent Jobs**: 20 maximum
- **Job Timeout**: 2 hours maximum
- **File Size Limits**: 50MB typical, no hard limit
- **Clip Duration**: 3 minutes maximum
- **Storage**: 60GB local storage capacity

### **Resource Constraints**
- **CPU**: Limited by Lightsail instance
- **Memory**: 2GB instance memory
- **Disk I/O**: Local SSD performance
- **Network**: Lightsail bandwidth limits
- **Queue**: Redis memory limitations

### **Scaling Considerations**
- **Horizontal Scaling**: Not implemented
- **Load Balancing**: Single instance only
- **Auto-scaling**: Not configured
- **Caching**: Redis for metadata only

---

## 🚨 THREAT LANDSCAPE ANALYSIS

### **High-Risk Attack Vectors**
1. **Command Injection**: yt-dlp parameter manipulation
2. **Server-Side Request Forgery**: URL parameter abuse
3. **Denial of Service**: Queue flooding, resource exhaustion
4. **Data Exfiltration**: Local file access via path traversal
5. **Container Escape**: Docker security misconfigurations

### **Medium-Risk Concerns**
1. **Information Disclosure**: Error message leakage
2. **Rate Limiting Bypass**: IP spoofing, distributed attacks
3. **Cache Poisoning**: Redis manipulation
4. **File Upload Abuse**: Large file attacks
5. **API Abuse**: Unauthorized bulk usage

### **Compliance Considerations**
- **GDPR**: Minimal due to no PII storage
- **DMCA**: Copyright compliance for video processing
- **Regional Laws**: Content filtering requirements
- **Platform ToS**: Video platform terms compliance

---

## 📋 SECURITY TESTING SCOPE

### **In-Scope Components**
- ✅ Frontend React application
- ✅ Backend FastAPI application  
- ✅ Worker video processing
- ✅ Redis queue and cache
- ✅ Docker container configuration
- ✅ nginx reverse proxy
- ✅ Local file storage
- ✅ yt-dlp integration

### **Out-of-Scope Components**
- ❌ AWS Lightsail host OS (managed service)
- ❌ Docker Engine security
- ❌ Let's Encrypt certificate authority
- ❌ Third-party video platforms
- ❌ Client browser security
- ❌ DNS provider security

### **Testing Environments**
- **Primary**: Isolated security testing environment
- **Secondary**: Local development environment
- **Reference**: Production environment (read-only analysis)

---

**Document Status**: ✅ COMPLETE - Ready for Phase 0.4 Threat Modeling  
**Next Phase**: Threat Modeling Workshop with stakeholder session  
**Security Audit Progress**: Phase 0.3/6 Complete 