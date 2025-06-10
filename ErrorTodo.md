# 🚨 Production Error Investigation & Resolution Plan

**Version:** 1.0  
**Created:** January 2025  
**Status:** Investigation Phase  
**Environment:** memeit.pro Production

---

## 📋 Error Summary

Based on the production screenshots and error logs, we have **three critical errors** blocking user functionality:

1. **CSP "connect-src" violation** - Blocking API calls to metadata endpoint
2. **React minified error #418** - React component crashing during data fetching
3. **YouTube "content blocked" embed** - Video previews not loading

---

## 🔍 Current System Analysis

### ✅ Backend Security Configuration Found
**File:** `backend/app/middleware/security_headers.py`
- **Current CSP:** `"connect-src 'self' https:;"`
- **Frame handling:** `"frame-ancestors 'none';"`
- **Environment access:** ✅ Has `settings.debug` access
- **Swagger exceptions:** ✅ Already implemented for `/docs`, `/redoc`

### ✅ Frontend Error Handling Analysis  
**File:** `frontend/src/app/page.tsx` (lines 94-125)
- **Current pattern:** Basic try/catch with fallback mock data
- **Issue:** No React error boundary for minified error #418
- **YouTube handling:** Uses ReactPlayer with minimal config

### ✅ Caddy Configuration Analysis
**File:** `Caddyfile` 
- **Current headers:** Basic security headers, no CSP
- **Issue:** No `Content-Security-Policy` header in Caddy
- **YouTube support:** No `frame-src` configuration

---

# 🎯 Investigation Plan & Hypotheses

## Phase 1: Immediate Diagnosis (30 minutes)

### H1: CSP connect-src Blocking API Calls
**Root Cause:** Current CSP only allows `https:` but production API calls to `/api/v1/metadata` need localhost/same-origin permissions.

**Evidence:**
- CSP in middleware: `"connect-src 'self' https:;"`
- Error shows: Refused to connect because it violates CSP `connect-src`
- API call pattern in frontend: `fetch('/api/v1/metadata')`

**Test Plan:**
```bash
# 1. Check active CSP header
curl -I https://memeit.pro/api/v1/metadata | grep -i content-security-policy

# 2. Test API endpoint directly
curl -f https://memeit.pro/api/v1/metadata

# 3. Check frontend API call in DevTools Network tab
# Expected: CSP violation when calling metadata endpoint
```

### H2: React Error #418 - Hydration/State Mismatch
**Root Cause:** React minified error #418 typically indicates hydration mismatch or improper error handling during async operations.

**Evidence:**
- Error occurs during metadata loading phase
- Error happens after CSP blocks the API call
- No React Error Boundary in place

**Test Plan:**
```javascript
// 1. Inspect error in browser console (non-minified)
// 2. Add temporary error boundary logging
// 3. Check if error occurs AFTER CSP violation
```

### H3: YouTube Content Blocked - Missing frame-src
**Root Cause:** YouTube embeds require specific `frame-src` permissions in CSP.

**Evidence:**
- Current CSP: `"frame-ancestors 'none'"` but no `frame-src`
- ReactPlayer config for YouTube minimal
- Screenshot shows "content blocked" message

**Test Plan:**
```bash
# 1. Test YouTube embed in isolation
echo '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>' > test.html

# 2. Check YouTube's X-Frame-Options
curl -I https://www.youtube.com/embed/dQw4w9WgXcQ | grep -i x-frame-options

# 3. Test with youtube-nocookie.com domain
curl -I https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ
```

---

## Phase 2: Targeted Fixes (2 hours)

### 🔧 Fix 1: CSP connect-src Resolution
**Priority:** P0 (Critical) - Blocking all API calls

#### Option A: Backend Middleware Fix (Recommended)
**File:** `backend/app/middleware/security_headers.py`

```python
# Add environment-aware CSP configuration
def __init__(self, app: ASGIApp):
    super().__init__(app)
    # CSP will be built dynamically based on environment

async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
    from ..config import settings
    
    # Build CSP based on environment
    connect_src = "'self' https:"
    if settings.debug:
        connect_src += " http://localhost:8000 ws://localhost:*"
    
    self.csp_header = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "script-src 'self' 'unsafe-inline' https:; "
        "font-src 'self' https:; "
        f"connect-src {connect_src}; "
        "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'"
    )
```

#### Option B: Caddy Header Override (Quick Fix)
**File:** `Caddyfile`

```caddyfile
# Add CSP header in Caddy (overrides backend)
header {
    Content-Security-Policy "default-src 'self'; connect-src 'self' https: wss:; frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' https:; frame-ancestors 'none'; base-uri 'self'"
}
```

### 🔧 Fix 2: React Error Boundary
**Priority:** P1 (High) - Prevent UI crashes

**File:** `frontend/src/app/page.tsx`

```typescript
// Wrap fetchVideoMetadata with better error handling
const handleUrlSubmit = async (url: string) => {
  setState({ phase: "loading-metadata", url });

  try {
    const metadata = await fetchVideoMetadata(url);
    setState({ phase: "trim", metadata });
    pushToast({ type: "success", message: "Video loaded successfully!" });
  } catch (error) {
    // Prevent React error #418
    console.error('Metadata fetch failed:', error);
    setState({ phase: "idle" });
    
    if (isRateLimitError(error)) {
      showNotification(error.message, error.retryAfter, error.limitType);
    } else {
      // More specific error handling
      const errorMessage = error instanceof Error 
        ? `Failed to load video: ${error.message}`
        : "Failed to load video. Please check the URL and try again.";
      
      pushToast({ type: "error", message: errorMessage });
    }
  }
};
```

### 🔧 Fix 3: YouTube Embed Fallback
**Priority:** P1 (High) - Restore video previews

**File:** `frontend/src/components/video/video-preview.tsx`

```typescript
// Add error handling and fallback
export default function VideoPreview({ url, onProgress, playing = false, muted = true, className = "w-full h-64" }: VideoPreviewProps) {
  const [embedError, setEmbedError] = useState(false);
  
  if (embedError) {
    return (
      <div className={`relative ${className} bg-gray-100 flex items-center justify-center`}>
        <div className="text-center">
          <p className="text-gray-600 mb-4">Video preview unavailable</p>
          <a 
            href={url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Watch on YouTube
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <ReactPlayer
        url={url}
        width="100%"
        height="100%"
        playing={playing}
        muted={muted}
        controls={false}
        onProgress={onProgress}
        onError={(error) => {
          console.error('ReactPlayer error:', error);
          setEmbedError(true);
        }}
        config={{
          youtube: {
            playerVars: { 
              showinfo: 1,
              origin: window.location.origin 
            },
          },
        }}
      />
    </div>
  );
}
```

---

## Phase 3: Testing & Validation (45 minutes)

### 🧪 Test Sequence

#### Test 1: CSP Fix Validation
```bash
# 1. Deploy CSP fix
# 2. Test API endpoint
curl -f https://memeit.pro/api/v1/metadata -X POST -H "Content-Type: application/json" -d '{"url":"https://youtube.com/watch?v=test"}'

# 3. Check browser DevTools Console
# Expected: No CSP violations
```

#### Test 2: React Error Resolution
```javascript
// 1. Open DevTools Console
// 2. Paste YouTube URL
// 3. Submit form
// Expected: No React error #418, proper error handling
```

#### Test 3: YouTube Embed Test
```html
<!-- Create test page -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>YouTube Embed Test</title>
</head>
<body>
    <iframe 
        width="560" 
        height="315" 
        src="https://www.youtube.com/embed/dQw4w9WgXcQ" 
        frameborder="0" 
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
        allowfullscreen>
    </iframe>
</body>
</html>
```

### 🔍 End-to-End Validation
```bash
# Complete user journey test
1. Visit https://memeit.pro
2. Paste: https://www.youtube.com/watch?v=dQw4w9WgXcQ
3. Click "Start"
4. Verify: Metadata loads successfully
5. Verify: Video preview shows
6. Set trim times: 00:00:10 to 00:00:20
7. Check terms and click "Create Clip"
8. Verify: Job processing starts

# Expected result: Complete flow without errors
```

---

## 📊 Priority Matrix

| Error | Impact | Effort | Priority | ETA |
|-------|--------|--------|----------|-----|
| **CSP connect-src** | 🔴 Critical | 🟡 Medium | P0 | 30 min |
| **React Error #418** | 🟠 High | 🟢 Low | P1 | 15 min |
| **YouTube Embeds** | 🟠 High | 🟡 Medium | P1 | 45 min |

**Total Estimated Fix Time:** 90 minutes

---

## 🛡️ Rollback Plan

### Emergency Rollback Procedures

#### CSP Rollback
```bash
# Revert to original CSP
git checkout HEAD~1 -- backend/app/middleware/security_headers.py
# OR
# Remove CSP header from Caddyfile and restart
```

#### Frontend Rollback
```bash
# Revert React changes
git checkout HEAD~1 -- frontend/src/app/page.tsx
git checkout HEAD~1 -- frontend/src/components/video/video-preview.tsx
```

### Backup Strategy
```bash
# Before starting fixes
cp backend/app/middleware/security_headers.py backend/app/middleware/security_headers.py.backup
cp Caddyfile Caddyfile.backup
cp frontend/src/app/page.tsx frontend/src/app/page.tsx.backup
```

---

## 📝 Implementation Checklist

### Pre-Implementation
- [ ] **Backup current files** (`security_headers.py`, `Caddyfile`, `page.tsx`)
- [ ] **Document current CSP** via `curl -I https://memeit.pro`
- [ ] **Test current failure** to confirm reproduction
- [ ] **Check backend logs** for any related errors

### Implementation Order
- [ ] **Fix 1: CSP connect-src** (Backend middleware update)
- [ ] **Test API calls** work without CSP violations
- [ ] **Fix 2: React Error Boundary** (Frontend error handling)
- [ ] **Test form submission** doesn't crash React
- [ ] **Fix 3: YouTube frame-src** (CSP update for embeds)
- [ ] **Test video previews** load correctly

### Post-Implementation
- [ ] **Full E2E test** of user journey
- [ ] **Check browser console** for any remaining errors
- [ ] **Verify all three errors** are resolved
- [ ] **Monitor for 24h** for any regression issues
- [ ] **Update documentation** with new CSP configuration

---

## 🚨 Emergency Contacts & Resources

### Quick Commands
```bash
# Check current CSP
curl -I https://memeit.pro | grep -i content-security-policy

# Test API endpoint
curl -X POST https://memeit.pro/api/v1/metadata -H "Content-Type: application/json" -d '{"url":"https://youtube.com/watch?v=test"}'

# Restart backend
docker-compose restart backend

# View logs
docker-compose logs backend --tail=50
```

### Related Documentation
- **CSP Reference:** https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
- **React Error #418:** Hydration mismatch - typically async data loading issues
- **YouTube Embed Policy:** https://developers.google.com/youtube/iframe_api_reference

---

**Next Action:** Begin Phase 1 Investigation immediately - start with CSP header inspection via curl command. 