# Instagram Metadata Extraction - Plan of Action (POA)

**Issue**: Instagram video URLs return 503 "Service Unavailable" on production site memeit.pro  
**Root Cause**: yt-dlp Instagram extractor failing due to authentication requirements  
**Created**: 2025-01-07  
**Priority**: HIGH (Production service disruption)

---

## 🎯 **Executive Summary**

The production site memeit.pro is returning HTTP 503 errors when users attempt to extract metadata from Instagram video URLs. Investigation confirms this is a yt-dlp authentication issue where Instagram now requires cookies/login for metadata extraction, but our backend provides no authentication mechanism.

---

## 🔍 **Problem Analysis**

### **Current Failure Chain**
1. User enters Instagram URL in frontend
2. POST to `/api/v1/metadata/extract` 
3. Backend calls `extract_metadata_with_fallback(url)` with yt-dlp
4. yt-dlp throws `DownloadError` (Instagram blocks unauthenticated requests)
5. Backend converts to `HTTPException(503, "service unavailable")`
6. Frontend displays "The video service is currently unavailable"

### **Technical Context**
- **Environment**: Production (memeit.pro) - not local development
- **yt-dlp Version**: ^2025.6.25 (recent but still needs Instagram auth)
- **Current Headers**: Mobile Safari UA + Referer (insufficient)
- **Missing**: Instagram authentication cookies/session

---

## 📋 **Systematic Action Plan**

Following **BP #0** (Lock Environment) and **BP #1** (Establish Ground Truth):

### **Phase 1: Production Diagnosis & Verification** ⚡ *IMMEDIATE*

#### **1.1 Confirm Production Behavior**
```bash
# Test production endpoint directly
curl -X POST https://memeit.pro/api/v1/metadata/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.instagram.com/reel/test"}'

# Expected: 503 response confirming the issue
```

#### **1.2 Verify Branch/Deployment Status**
Following **BP #16** (Verify Branch Architecture):
```bash
# Check which branch production deploys from
grep -r "deploy" .github/workflows/
git log --oneline -5  # Recent commits
git branch -a         # Available branches
```

#### **1.3 Test Local yt-dlp Behavior**
```bash
cd backend
poetry run python -c "
import yt_dlp
ydl = yt_dlp.YoutubeDL({'quiet': True})
try:
    info = ydl.extract_info('https://www.instagram.com/reel/C-test', download=False)
    print('SUCCESS:', info.get('title', 'No title'))
except Exception as e:
    print('EXPECTED FAILURE:', str(e))
"
```

### **Phase 2: Implementation Strategy** 🔧 *CORE FIX*

#### **2.1 Instagram Authentication Solution**
Following **BP #24** (Design for Portability):

**Option A: Cookie-Based Authentication (Recommended)**
```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    INSTAGRAM_COOKIES: Optional[str] = None  # JSON string of cookies
    
    class Config:
        env_file = ".env"
```

**Option B: Alternative Extractor Fallback**
```python
# backend/app/services/metadata.py
async def extract_instagram_metadata_fallback(url: str):
    """Fallback strategy for Instagram when yt-dlp fails"""
    # Implementation for alternative extraction method
    pass
```

#### **2.2 Enhanced Error Handling**
Following **BP #3** (Root Causes vs Symptoms):
```python
# backend/app/api/metadata.py
@router.post("/extract")
async def extract_metadata(request: UrlRequest):
    try:
        result = await extract_metadata_with_fallback(request.url)
        return result
    except yt_dlp.utils.DownloadError as e:
        # Distinguish Instagram auth errors from other failures
        if "instagram" in request.url.lower():
            if "login required" in str(e).lower():
                raise HTTPException(
                    status_code=429,  # Rate Limited (more accurate than 503)
                    detail="Instagram requires authentication. Please try again later."
                )
        # Generic fallback
        raise HTTPException(status_code=503, detail="Video service temporarily unavailable")
```

### **Phase 3: Implementation Execution** 🚀 *DEPLOYMENT*

#### **3.1 Local Development & Testing**
Following **BP #23** (Complete Verification Suite):
```bash
# Backend verification
cd backend
poetry run black --check .
poetry run isort --check-only .
poetry run flake8 . --count
poetry run mypy app/

# Test the fix locally
poetry run pytest tests/test_instagram_integration.py -v
```

#### **3.2 Frontend Update (if needed)**
```bash
# Frontend verification  
cd frontend
npm run lint
npx prettier --check .
npm run type-check

# Test UI error handling
npm test -- --testNamePattern="instagram"
```

#### **3.3 Deployment Process**
Following **BP #22** (Push Local Fixes):
```bash
# Stage changes
git add .
git commit -m "Fix Instagram metadata extraction 503 errors

- Add Instagram cookie authentication support
- Improve error handling for auth failures  
- Return 429 instead of 503 for rate limits
- Add fallback mechanisms for Instagram

Fixes production issue on memeit.pro"

# Push to trigger CI/CD
git push origin master

# Monitor deployment
# Check GitHub Actions for workflow success
# Verify production behavior after deployment
```

### **Phase 4: Production Verification** ✅ *VALIDATION*

#### **4.1 Immediate Post-Deployment Testing**
```bash
# Test production fix
curl -X POST https://memeit.pro/api/v1/metadata/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.instagram.com/reel/test"}'

# Expected: Either success OR improved error message (not generic 503)
```

#### **4.2 User Experience Testing**
- Navigate to memeit.pro
- Enter Instagram video URL
- Verify improved error messaging
- Test with valid Instagram URLs (if cookies configured)

---

## 🛡️ **Risk Assessment & Mitigation**

### **High Risk Items**
1. **Instagram Cookie Management**: Cookies may expire requiring rotation
2. **Rate Limiting**: Instagram may still block high-volume requests
3. **API Changes**: Instagram frequently updates their blocking mechanisms

### **Mitigation Strategies**
1. **Graceful Degradation**: Return user-friendly error messages
2. **Monitoring**: Add logging for Instagram extraction attempts/failures
3. **Alternative Sources**: Focus on Facebook/other platforms that work reliably

### **Rollback Plan**
Following **BP #5** (Rollback Safety):
```bash
# Tag current state before deployment
git tag pre-instagram-fix

# If fix fails, immediate rollback
git revert HEAD
git push origin master
```

---

## 📊 **Success Criteria**

### **Primary Goals**
- [ ] Instagram URLs no longer return generic 503 errors
- [ ] Users receive clear, actionable error messages
- [ ] Production stability maintained

### **Secondary Goals**  
- [ ] Some Instagram URLs successfully extract metadata (if cookies work)
- [ ] Improved error categorization in logs
- [ ] Better user experience messaging

### **Measurement**
- Monitor `/api/v1/metadata/extract` error rates
- Track user-reported Instagram extraction issues
- Verify no regression in other video platform support

---

## 🔄 **Follow-Up Actions**

### **Short Term (1-2 weeks)**
1. Monitor Instagram extraction success/failure rates
2. Gather user feedback on error messaging improvements
3. Investigate cookie rotation automation if needed

### **Medium Term (1-2 months)**
1. Evaluate alternative Instagram extraction methods
2. Consider Instagram Graph API integration
3. Implement user authentication for personal Instagram access

### **Long Term (3+ months)**
1. Diversify video platform support to reduce Instagram dependency
2. Build robust fallback mechanisms for all major platforms
3. Consider premium video extraction service integration

---

## 📝 **Implementation Notes**

### **Environment Variables Required**
```bash
# Production .env additions
INSTAGRAM_COOKIES={"sessionid":"...", "csrftoken":"..."}  # JSON format
INSTAGRAM_AUTH_ENABLED=true
```

### **Dependencies to Add**
```toml
# pyproject.toml
[tool.poetry.dependencies]
# No new dependencies required - using existing yt-dlp
```

### **Configuration Files to Update**
- `backend/app/core/config.py` - Add Instagram settings
- `backend/app/services/metadata.py` - Enhanced error handling
- `backend/app/api/metadata.py` - Better HTTP status codes

---

## 🎯 **Best Practices Applied**

This POA follows key principles from the Best Practices guide:

- **BP #0**: Environment locked to production (memeit.pro)
- **BP #1**: Ground truth established through direct API testing  
- **BP #3**: Root cause identified (yt-dlp auth) vs symptom (503 errors)
- **BP #22**: Complete push workflow to trigger CI/CD
- **BP #23**: Full verification suite before deployment
- **BP #24**: Portable configuration via environment variables

---

**Document Status**: DRAFT - Ready for Implementation  
**Next Action**: Execute Phase 1 production diagnosis
**Owner**: Development Team  
**Reviewer**: [To be assigned] 