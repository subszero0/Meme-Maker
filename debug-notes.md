# Debug Notes - Metadata API 404 Issue

## Timestamp: Initial Investigation
- **Error Observed**: Multiple 404 errors on POST requests to `http://localhost:8000/api/metadata`
- **Trigger**: User inputs YouTube link, clicks "Let's Go" button
- **Console Output**: 
  - Unchecked runtime.lastError: The message port closed before a response was received
  - Multiple POST 404 (Not Found) errors to metadata endpoint
  - getBasicMetadata calls failing

## Investigation Steps:
1. [ ] Hard-refresh and reproduce error
2. [ ] Check Network tab for failed requests
3. [ ] Examine console stack trace
4. [ ] Check existing tests and code comments
5. [✅] Verify environment values  
6. [✅] Write failing test first - CONFIRMED: Test fails with 404 errors as expected
7. [✅] Apply minimal viable change - FIXED: Updated all API endpoints to use /api/v1 prefix
8. [✅] Run full test suite - PASSED: All 28 tests passing, build successful
9. [✅] Smoke test in browser - SUCCESS: API endpoint returns 200 with valid metadata
10. [ ] Commit and document

## Root Cause Identified:
**MISMATCH IN API ROUTES**

### Frontend Calls:
- `POST /api/metadata` (getBasicMetadata)
- `POST /api/metadata/extract` (getDetailedMetadata)

### Backend Serves:
- `POST /api/v1/metadata` (with /api/v1 prefix)
- `POST /api/v1/metadata/extract` (with /api/v1 prefix)

### Problem:
- Backend uses `/api/v1` prefix for metadata routes (line 54 in main.py)
- Frontend calls `/api/metadata` without the version prefix
- This causes 404 errors

### Solution:
Need to update frontend API calls to use `/api/v1` prefix to match backend routes 