# Meme Maker – Product Requirements Document (PRD)  
**Version 2.0 – Production Ready ✅**  
*Last Updated: January 2025*

---

## 1 · Product summary  

> **Paste an Instagram, Facebook, Twitter/X, Threads, Reddit or YouTube link → drag In/Out → download up to 3 min, loss-free, no signup, file self-destructs after download.**

---

## 2 · Scope (Current Implementation)  

| Axis | Implementation |
|------|----------|
| **Supported sources** | YouTube, Instagram, Facebook (public videos & Reels), Threads, Reddit, Twitter/X |
| **Clip-length cap** | ≤ 3 minutes (enforced client & server side) |
| **Accounts / history** | 100 % anonymous; no login, no stored clip history |
| **Monetisation** | Free-only MVP (no ads, no paywall) |
| **Output** | Container-copy – keep original resolution / fps / codec / container; re-encode only the first GOP if required |
| **Retention** | Job-based cleanup; processed file deleted after successful download or timeout |
| **Concurrency budget** | 20 simultaneous jobs (T-003 DoS protection reduces to 15 during high load) |
| **Mobile** | Responsive web app; React-based UI optimized for mobile |
| **Legal stance** | "Tool vendor" – user must tick *"I have the right to download this content"* for every job |
| **Authentication** | Cookie-based authentication for Instagram/Facebook; Browser cookie extraction support |
| **Storage** | Local storage with daily organization (ISO-8601 structure) |

---

## 3 · User flow  

### 3.1 Paste  
* User pastes a public video URL from supported platforms.  
* Back-end validates the link and fetches metadata (title, duration, resolutions, thumbnail).
* Multiple fallback strategies ensure platform compatibility and avoid bot detection.
* Video proxy bypasses CORS restrictions for seamless preview playback.

### 3.2 Trim  
* Dual-handle timeline slider **and** exact `hh:mm:ss.mmm` input boxes.  
* Live muted preview updates while scrubbing using react-player.
* Clip-length validator blocks selections over 3 min.
* Real-time validation with visual feedback.

### 3.3 Render  
* Command: `ffmpeg -ss {in} -to {out} -c copy`.  
* If IN-point is not a key-frame, back-end re-encodes only the first GOP, then continues `-c copy`.
* Progress tracking with detailed stages (downloading, trimming, finalizing).
* Job status polling with real-time updates.

### 3.4 Download & cleanup  
* Browser polls for job status using TanStack Query.  
* When ready, server returns a **direct download URL**.  
* File is deleted immediately after successful download; job record removed.
* Integrity validation using SHA256 checksums.

---

## 4 · Error states & UX copy  

| Condition | User message |
|-----------|--------------|
| Selection > 3 min | "Trim to three minutes or less to proceed." |
| Private / geo-blocked video | "We can't access this URL – is the video public?" |
| Rights checkbox unticked | "Please confirm you have the right to download this video." |
| Worker queue full (> 20 jobs) | "Busy right now. Try again in a minute." |
| T-003 DoS protection active | "Queue at capacity. T-003 DoS protection active. Try again later." |
| Unsupported platform | "Please enter a valid URL from Facebook, Instagram, Twitter/X, YouTube, Reddit, or Threads" |
| Network/CORS issues | "Video proxy unavailable. Please try again." |
| File integrity failure | "File integrity check failed. Please retry the download." |
| Instagram/Facebook authentication | "Authentication required. Please check cookie configuration." |

---

## 5 · Non-functional requirements  

| Category | Target |
|----------|--------|
| **Latency** | ≤ 30 s wall-time for a 3 min 1080 p clip on a 50 Mbps connection |
| **Throughput** | 20 concurrent jobs without performance degradation; T-003 DoS protection for queue management |
| **Security** | TLS everywhere; security headers middleware; admin API key authentication; file integrity validation |
| **Observability** | Structured logging with job tracking; Prometheus/Grafana endpoints available (currently disabled) |
| **Cost guard-rail** | Local storage with daily cleanup; configurable retention policy; storage stats monitoring |
| **Authentication** | Cookie-based authentication for Instagram/Facebook; browser cookie extraction |
| **CORS** | Video proxy service for seamless cross-origin video playback |
| **Data Privacy** | No PII stored; anonymous job processing; automatic file cleanup |

---

## 6 · Technical architecture  

```text
Browser → FastAPI (Python) → Redis queue → Worker (yt-dlp + FFmpeg) → Local Storage
   ↑                                            │
   └─────────── direct download URL ←───────────┘
   
Video Proxy ← Browser (for CORS bypass)
```

**Front-end:** React 18 + Vite + TypeScript, Tailwind CSS + Radix UI, TanStack Query for state management, React Router for navigation, react-player for video preview. ✅ **Fully Integrated**

**API / gateway:** FastAPI (Python 3.12) in Docker with comprehensive middleware stack (CORS, security headers, DoS protection, admin auth).

**Task queue:** Redis + RQ for job processing and metadata caching.

**Workers:** Alpine container bundling latest yt-dlp (auto-updated) and FFmpeg; multiple fallback strategies for platform compatibility; cookie-based authentication for protected platforms.

**Storage:** Local storage with daily ISO-8601 organization and atomic file operations; SHA256 integrity validation on AWS Lightsail instance.

**Video Proxy:** Dedicated CORS bypass service for seamless video preview playback across all supported platforms.

**TLS & Reverse Proxy:** nginx reverse proxy configuration for production deployment with TLS termination.

**Observability:** Structured logging with correlation IDs; Prometheus/Grafana endpoints prepared for future implementation.

**Security:** Multi-layer protection including security headers, admin authentication, file integrity validation, and T-003 DoS protection.

---

## 7 · Key-frame fallback – why it exists

Video streams contain key-frames (full images) followed by many delta-frames (only changes).

Cutting on a delta-frame causes playback glitches because the initial reference frame is missing.

The worker therefore re-encodes only the first group-of-pictures (≈ 1–2 s) so the very first frame of the clip is a key-frame, then copies the rest loss-lessly.

Extra CPU cost ≈ 0.3 s per job; quality and file size remain virtually unchanged.

---

## 8 · Stack overview

| Layer | Technology |
|-------|------------|
| **Front-end** | React 18 + Vite, TypeScript, Tailwind CSS + Radix UI, TanStack Query ✅ |
| **Back-end** | FastAPI (Python 3.12) with middleware stack ✅ |
| **Download engine** | yt-dlp + FFmpeg with platform-specific optimizations ✅ |
| **Queue** | Redis + RQ with job tracking ✅ |
| **Storage** | AWS Lightsail local storage with daily organization ✅ |
| **Video Proxy** | FastAPI CORS bypass service ✅ |
| **Authentication** | Cookie-based for Instagram/Facebook ✅ |
| **TLS & Reverse Proxy** | nginx with TLS termination ✅ |
| **Observability** | Structured logging + Prometheus endpoints (planned) ⏳ |
| **Security** | Multi-layer middleware protection ✅ |
| **State Management** | TanStack Query + React hooks ✅ |
| **UI Components** | Radix UI primitives + custom components ✅ |
| **Deployment** | Docker Compose + GitHub Actions CI/CD ✅ | 

---

## 9 · Enhanced features beyond MVP

### 9.1 Platform-specific optimizations
* **Instagram/Facebook:** Cookie-based authentication with browser extraction support
* **Multiple fallback strategies:** Automatic retry with different headers/configurations 
* **Bot detection avoidance:** Platform-specific user agents and request patterns
* **Format prioritization:** Merged formats preferred over DASH streams for audio compatibility

### 9.2 Advanced video processing
* **Keyframe detection:** Automatic GOP re-encoding when cutting on non-keyframes
* **Video rotation correction:** Automatic detection and correction of mobile video orientation
* **Format validation:** Comprehensive format checking and fallback selection
* **Progress tracking:** Real-time job progress with detailed processing stages

### 9.3 Enhanced security & reliability
* **T-003 DoS protection:** Dynamic queue limits during high load periods
* **Admin API endpoints:** Secure administrative access with API key authentication
* **File integrity validation:** SHA256 checksums for download verification
* **Security headers middleware:** Comprehensive HTTP security headers
* **Atomic file operations:** Write-then-move strategy for corruption prevention

### 9.4 Developer experience
* **Comprehensive logging:** Structured logs with correlation IDs for debugging
* **Health check endpoints:** Container and service health monitoring
* **Environment-aware configuration:** Development/staging/production environment support
* **CI/CD pipeline:** Automated testing and deployment with GitHub Actions
* **Error boundary:** React error boundaries for graceful frontend error handling

--- 

## 10 · Security Implementation

### 10.1 Application Security Headers
**Implemented via SecurityHeadersMiddleware**
* **Strict-Transport-Security:** `max-age=63072000; includeSubDomains; preload` - Forces HTTPS connections
* **Content-Security-Policy:** Environment-aware CSP with strict default policies, allows localhost in development
* **X-Content-Type-Options:** `nosniff` - Prevents MIME type sniffing attacks
* **X-Frame-Options:** `DENY` - Prevents clickjacking attacks
* **Referrer-Policy:** `no-referrer` - Prevents referrer information leakage
* **Permissions-Policy:** Restricts camera, microphone, geolocation, and interest-cohort access

### 10.2 Authentication & Authorization
**Implemented via AdminAuthMiddleware**
* **Admin API Protection:** All `/api/v1/admin/*` endpoints secured with Bearer token authentication
* **API Key Validation:** Configurable admin API key via `ADMIN_API_KEY` environment variable
* **Secure Error Handling:** Generic error messages to prevent information disclosure
* **Request Logging:** Failed authentication attempts logged with client IP for monitoring
* **Graceful Degradation:** Admin endpoints return 503 if API key not configured (fail-secure)

### 10.3 DoS Protection & Rate Limiting
**Implemented via QueueDosProtectionMiddleware (T-003 Protection)**

#### Circuit Breaker Pattern
* **Failure Threshold:** Opens circuit at 50% error rate with minimum 10 requests
* **Recovery Testing:** Half-open state for gradual service recovery
* **Timeout:** 30-second circuit breaker timeout before retry attempts

#### Advanced Rate Limiting
* **Request Burst Detection:** 
  - GET requests: 25 requests/30 seconds
  - POST requests: 20 requests/30 seconds
  - Penalty: 1-5 minute cooldown periods
* **Job Submission Limits:**
  - 3 concurrent jobs per IP
  - 10 jobs per hour per IP
  - 50 jobs per day per IP
* **Queue Health Monitoring:** Maximum 20 jobs in queue depth

#### IP Behavior Tracking
* **Real IP Detection:** Supports X-Forwarded-For, X-Real-IP, CF-Connecting-IP headers
* **Behavioral Analysis:** Tracks request patterns, burst violations, and penalty periods
* **Automatic Cleanup:** Expires old tracking data every 5 minutes

### 10.4 Data Protection & Privacy
* **No PII Storage:** No personal information collected or stored
* **Anonymous Processing:** All job processing is anonymous with no user tracking
* **Automatic Cleanup:** Files deleted immediately after successful download
* **Integrity Validation:** SHA256 checksums for download verification
* **Atomic Operations:** Write-then-move file operations prevent corruption

### 10.5 Input Validation & Sanitization
* **URL Validation:** Strict validation of supported platform URLs
* **Filename Sanitization:** File system safe filename generation with invalid character replacement
* **Path Traversal Prevention:** Security checks in file operations (`..`, `/`, `\` blocked)
* **Request Validation:** Comprehensive Pydantic models for all API inputs
* **Error Boundaries:** React error boundaries for graceful frontend error handling

### 10.6 CORS & Cross-Origin Security
* **Explicit CORS Configuration:** Environment-specific allowed origins
* **Development Support:** Localhost origins automatically allowed in development
* **Video Proxy Security:** Controlled domain whitelist for video proxy service
* **Header Controls:** Strict control of allowed headers and methods

### 10.7 Infrastructure Security
* **Container Isolation:** Docker containers with restricted privileges
* **Health Checks:** Comprehensive health monitoring for all services
* **Environment Separation:** Distinct configuration for development/staging/production
* **Secure Defaults:** Production documentation disabled, debug mode controlled
* **TLS Termination:** nginx reverse proxy with proper TLS configuration

### 10.8 Logging & Monitoring
* **Security Event Logging:** Failed authentication attempts and DoS protection events
* **Structured Logging:** JSON logging with correlation IDs for security auditing
* **Error Tracking:** Comprehensive error logging without sensitive information exposure
* **Performance Monitoring:** Queue depth and processing time metrics for anomaly detection

### 10.9 Configuration Security
* **Environment Variable Protection:** Sensitive configuration via environment variables
* **Cookie Security:** Secure handling of Instagram/Facebook authentication cookies
* **API Key Management:** Configurable admin API keys with proper validation
* **Debug Mode Controls:** Debug features automatically disabled in production

--- 