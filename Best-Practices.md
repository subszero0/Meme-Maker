# 🏆 A Curated Guide to Best Practices

*Based on learnings from systematic production debugging sessions*

This document outlines a hierarchical set of best practices for robust development, debugging, and problem resolution. It is organized by levels of universality, from core principles that always apply to specific, situational guidelines.

---

### **Table of Contents**
1.  [**Level 0: The Golden Rules (Universal Principles)**](#level-0-the-golden-rules-universal-principles)
2.  [**Level 1: Systematic Debugging & Diagnosis**](#level-1-systematic-debugging--diagnosis)
3.  [**Level 2: Environment & Architecture Awareness**](#level-2-environment--architecture-awareness)
4.  [**Level 3: Code Quality & CI/CD Integrity**](#level-3-code-quality--cicd-integrity)
5.  [**Level 4: Implementation-Specific Practices**](#level-4-implementation-specific-practices)
    -   [Git & Repository Management](#git--repository-management)
    -   [Backend & Dependencies (Python/Poetry)](#backend--dependencies-pythonpoetry)
    -   [Frontend & User Interface (React/Vite/Tests)](#frontend--user-interface-reactvitetests)
6.  [**Meta-Practice: The Learning Loop**](#meta-practice-the-learning-loop)

---

## **Level 0: The Golden Rules (Universal Principles)**
*Core, non-negotiable principles that apply to every action taken.*

### **BP #0: The "Ground Zero" Rule - Lock Your Environment Before Acting**
**Principle**: All diagnostic and corrective actions are fundamentally invalid until you have confirmed you are operating in the same environment (Local vs. Production) where the error is reported. Misalignment on this single point invalidates all subsequent work. This is the first check, performed before any other action is taken.

**Implementation**:
1.  **State the Target**: Based on user context (screenshots, URLs, logs), explicitly state the environment you are targeting.
    -   *Example*: "The error is on `meme-maker.pro` at IP `13.126.173.223`. All my actions will target the **production server**."
2.  **Confirm the Locus of Action**: Verify that your tools are pointed at the correct environment.
    -   If the target is **production**, your commands must be `git` (to prepare a fix for deployment) or run via `ssh` on the remote server. Local commands like `docker-compose` are irrelevant.
    -   If the target is **local**, your commands will be `docker-compose` on the local machine.
3.  **The Litmus Test**: Before running a command, ask: "Will this command run on the user's local machine or the remote production server?" If the answer does not match the error's location, **do not run the command**.
4.  **Acknowledge the Deployment Path**: A fix is not a fix until it is deployed. Changes made in the local environment only affect production after a successful `git push` and a deployment pipeline (CI/CD or manual SSH) run.

**Real-World Failure Example from This Session**:
-   **User Context**: `meme-maker.pro` (Production) was showing a `400 Bad Request`.
-   **Assistant Error**: Executed `docker-compose logs backend` and `docker-compose build` on the user's local Windows machine. This was fundamentally incorrect.
-   **Flawed Logic**: Assumed the local container logs were relevant to the production error and that local rebuilds would fix the live site.
-   **Correct Logic**: The first step should have been to establish the deployment path (`git`, CI/CD, SSH) to the production server. All debugging of logs and application of fixes must happen **on the production server** itself, triggered by a deployment.
-   **Lesson**: Debugging a local environment when the error is in production is the most direct path to wasted time and incorrect fixes. **The location of the error dictates the location of the debugging.**

### **BP #22: Always Push Local Fixes to Remote Repository for CI/CD**
**Principle**: Local fixes don't affect CI/CD pipelines until they're pushed to the remote repository. Never assume local test results reflect CI/CD behavior.

**Implementation**:

**Critical Workflow Step**:
1. **Fix issues locally** → Test locally → Commit locally
2. **Push to remote repository** → Trigger CI/CD → Verify pipeline success
3. **Missing Step 2 = CI/CD still fails with old code**

**Common Mistake Pattern**:
```bash
# Fix lint errors locally
poetry run flake8 .  # ✅ 0 errors locally

# User reports: "CI/CD still failing"
# Reality: Fixes not pushed to GitHub yet
```

**Correct Process**:
```bash
# 1. Fix and test locally
poetry run flake8 .  # Verify fixes work

# 2. Stage and commit changes
git add .
git commit -m "Fix lint errors blocking CI/CD"

# 3. CRITICAL: Push to remote
git push origin master

# 4. Verify CI/CD picks up changes
# Check GitHub Actions for new workflow run
```

**Real-World Example**:
- **Problem**: User reports "Actions aren't updated with latest push"
- **Root Cause**: Assistant fixed lint errors locally but never pushed to GitHub
- **CI/CD Status**: Still running against old code with 55 lint errors
- **Solution**: `git push origin master` to trigger new CI/CD run with fixes
- **Lesson**: Local success ≠ CI/CD success until code is pushed

**Verification Steps**:
1. **Confirm push succeeded**: Check git output for "Writing objects" and remote confirmation
2. **Verify GitHub has new commit**: Check GitHub repository for latest commit hash
3. **Monitor CI/CD trigger**: New push should trigger new workflow run
4. **Validate pipeline progression**: Check that workflow progresses past previously failing step

### **BP #23: Execute Complete Verification Suite Before Every Push**
**Principle**: Never push after fixing just one type of issue. Always run the COMPLETE verification suite (linting, formatting, type checking) for both backend and frontend to prevent regression cycles.

**Implementation**:

**Complete Backend Verification Suite**:
```bash
cd backend

# Step 1: Run ALL linting tools together
poetry run black --check .         # ✅ Code formatting
poetry run isort --check-only .    # ✅ Import sorting  
poetry run flake8 . --count        # ✅ Style violations
poetry run mypy app/               # ✅ Type checking

# Step 2: Only proceed if ALL tools pass
# If any tool fails, fix ALL issues before pushing
```

**Complete Frontend Verification Suite**:
```bash
cd frontend

# Step 1: Run ALL linting/formatting tools together
npm run lint                       # ✅ ESLint warnings/errors
npx prettier --check .             # ✅ Code formatting
# Add any other tools your project uses
npm run type-check                 # ✅ TypeScript type checking

# Step 2: Only proceed if ALL tools pass
```

**Critical Anti-Pattern to Avoid**:
```bash
# ❌ WRONG: Single-tool verification
npm run lint     # ✅ ESLint passes
git push         # 💥 CI/CD fails on Prettier

# ❌ WRONG: Sequential fixing
fix ESLint → push → CI/CD fails on Prettier
fix Prettier → push → CI/CD fails on tests
fix tests → push → CI/CD fails on something else

# ✅ RIGHT: Complete verification before any push
npm run lint && npx prettier --check . && echo "All frontend tools pass"
# Only push after complete verification
```

**Real-World Learning Example from This Session**:
- **Issue**: Fixed frontend test mock data and functional behavior
- **Mistake**: Pushed without running complete verification suite
- **Consequence**: CI/CD failed on Prettier formatting (exact same regression pattern)
- **Correct Fix**: Ran `npm run lint` + `npx prettier --check .` together
- **Lesson**: Even after fixing major functional issues, formatting tools can still fail

**Project-Specific Verification Commands**:

**Backend Complete Check**:
```bash
cd backend && \
poetry run black --check . && \
poetry run isort --check-only . && \
poetry run flake8 . --count && \
echo "✅ Backend verification complete"
```

**Frontend Complete Check**:
```bash
cd frontend && \
npm run lint && \
npx prettier --check . && \
npm run type-check && \
echo "✅ Frontend verification complete"
```

---

## **Level 1: Systematic Debugging & Diagnosis**
*A detailed workflow for identifying the root cause of any issue, moving from the outside in.*

### **BP #1: Establish Ground Truth Before Any Changes**
**Principle**: Never assume the problem; prove it exists and understand its exact nature.

**Implementation**:
- Hard refresh browser (Ctrl+Shift+R) and capture exact errors with timestamps
- Test at multiple levels: browser console, network tab, direct server API calls
- Document the "before" state in a debug notes file with specific error messages
- Take screenshots of console and network tabs showing the exact failure

**Example**: 
Instead of assuming "API calls fail" → Test `curl https://domain.com/api/endpoint` vs browser behavior to distinguish browser issues from server issues.

**Why It Matters**: 
Many "fixes" address symptoms rather than root causes because the initial problem assessment was incomplete.

### **BP #2: Use the Layered Diagnosis Approach**
**Principle**: Debug from the outside in - Network → Console → Code, not the reverse. Use systematic layer-by-layer testing to distinguish platform behavior from infrastructure issues.

**Implementation**:
1. **Network Tab First**: Look for HTTP status codes, failed requests, timing issues
2. **Console Stack Traces**: Find where errors originate in your code (not framework code)
3. **Source Code**: Examine the specific line/function that's failing
4. **Environment**: Check configuration, environment variables, and build settings
5. **Platform Layer**: Test external APIs directly to distinguish platform restrictions from infrastructure failures

**Systematic Layer Testing**:
- **Frontend Layer**: Browser network tab, console errors
- **Proxy Layer**: nginx routing, SSL termination
- **Backend Layer**: Direct API testing with curl/Postman
- **Extraction Layer**: Direct yt-dlp/tool testing
- **Platform Layer**: External service APIs (Instagram, YouTube, etc.)

**Example**:
- Network shows 404 → Check nginx routing
- Network shows 422 → Check request payload format
- Console shows mixed content → Check HTTP/HTTPS URL patterns
- API shows "unavailable" → Test external platform directly to confirm if it's platform restrictions vs infrastructure

**Real-World Application**:
In the Production Underscore Investigation, systematic layer testing revealed:
- ✅ Frontend: Properly formatted requests
- ✅ nginx: Correct URL routing
- ✅ Backend: Successful URL processing
- ✅ yt-dlp: Reached Instagram API
- ❌ Instagram: Rate limiting (platform behavior, not infrastructure failure)

**Why It Matters**: 
Starting with code changes without understanding the error source leads to fixing the wrong layer. Future investigations should use this systematic layer-by-layer approach to distinguish platform behavior from infrastructure issues.

### **BP #3: Distinguish Between Root Causes and Symptoms**
**Principle**: Ask "why" three times before implementing any solution.

**Implementation**:
- **First Why**: Why is this error occurring? (e.g., "API calls return 404")
- **Second Why**: Why is that happening? (e.g., "Nginx not routing properly")  
- **Third Why**: Why is that the case? (e.g., "Frontend making wrong URL pattern")
- Test your hypothesis at each level before proceeding

**Example**:
- Symptom: "Website shows connection errors"
- First Why: Frontend calling localhost:8000 instead of relative URLs
- Second Why: Production build using development environment config
- Third Why: Build process not setting MODE=production correctly
- **Root Cause**: Build environment configuration (not nginx, not server setup)

**Why It Matters**: 
Fixing symptoms creates temporary solutions that break again; fixing root causes creates lasting solutions.

### **BP #6: Test Hypotheses at the Lowest Level First**
**Principle**: Validate your assumptions using the simplest possible test before implementing complex solutions.

**Implementation**:
- Use `curl` to test API endpoints before changing nginx configurations
- Check file contents with `grep` before rebuilding entire containers
- Test individual components before testing integrated systems
- Verify environment variables are set correctly before changing application code

**Example**:
Before "fixing" API routing:
```bash
# Test if backend is accessible
curl http://localhost:8000/api/v1/health

# Test if nginx is routing  
curl http://localhost/api/v1/health

# Test if HTTPS is routing
curl https://domain.com/api/v1/health
```
This reveals exactly where the chain breaks.

**Why It Matters**: 
Complex solutions for simple problems create technical debt and hide the real issues.

### **BP #11: Distinguish Server Reality from Browser Perception**
**Principle**: What the browser shows may not reflect what the server is actually doing.

**Implementation**:
- Test server endpoints directly with `curl` to understand true server behavior
- Compare server response codes with browser-reported errors
- Check both request headers and response headers between browser and direct calls
- Be aware that browser caching, CORS, and security policies can mask actual server responses
- When browser shows 404 but server shows 405, investigate the method mismatch

**Real-World Example**:
- **Browser Console**: `POST https://memeit.pro/api/v1/metadata 404 (Not Found)`
- **Server Direct Test**: `curl -I https://memeit.pro/api/v1/metadata` → `405 Method Not Allowed`
- **Reality**: Endpoint exists and routing works, but browser cache or different request format created confusion
- **Lesson**: The browser showing 404 vs server showing 405 revealed the real issue wasn't routing

**Why It Matters**: 
Browser-reported errors can be misleading due to caching, security policies, or request format differences. Always verify server behavior independently.

### **BP #32: Distinguish Platform Behavior from Infrastructure Issues**
**Principle**: When debugging external service integrations, systematically isolate whether errors originate from platform restrictions (rate limiting, authentication) or your infrastructure (routing, configuration).

**Implementation**:

**Step 1: Test Platform APIs Directly**
```bash
# Test the external service directly with the same data your system uses
yt-dlp --print-json --skip-download "https://platform.com/content/12345"
curl -X GET "https://api.platform.com/v1/endpoint" -H "Authorization: Bearer token"
```

**Step 2: Compare Error Patterns Across Multiple URLs**
```bash
# Test multiple URLs from the same platform to identify patterns
# If ALL URLs from a platform fail → Platform issue
# If only specific URL patterns fail → Potential infrastructure issue
```

**Step 3: Verify Error Translation Chain**
```bash
# Trace how platform errors become user-facing messages
# Platform Error → Backend Processing → Frontend Display
# Ensure each step appropriately handles platform restrictions
```

**Platform vs Infrastructure Error Indicators**:

**Platform Behavior (Normal)**:
- Rate limiting messages ("too many requests")
- Authentication requirements ("login required") 
- Regional restrictions ("content not available in your region")
- Temporary blocking ("service temporarily unavailable")
- Content-specific restrictions ("private video", "deleted content")

**Infrastructure Issues (Fixable)**:
- URL encoding/decoding problems
- Proxy routing failures
- Environment configuration mismatches
- Network connectivity issues
- Service discovery failures

**Real-World Example**:
- **Apparent Problem**: "All URLs with underscores fail in production"
- **Systematic Testing**: 
  1. Direct yt-dlp test → Reached Instagram API successfully
  2. Backend API test → Correct error handling and translation
  3. Multiple URL comparison → Same error pattern regardless of underscores
- **Discovery**: Instagram rate limiting (platform behavior) was being misinterpreted as URL processing failure (infrastructure issue)
- **Resolution**: No infrastructure changes needed - system working correctly

**Investigation Strategy**:
1. **Assume Platform Behavior First**: Most external service "failures" are actually normal platform restrictions
2. **Test Infrastructure Only After**: Only investigate infrastructure if direct platform testing shows abnormal behavior
3. **Document Platform Patterns**: Maintain knowledge of each platform's normal restriction behaviors
4. **Verify Error Messaging**: Ensure platform restrictions are translated to helpful user messages

**Common Misattribution Patterns**:
- Assuming all API errors indicate infrastructure problems
- Not testing external services directly before debugging internal systems
- Missing the correlation between error patterns and platform restrictions
- Over-engineering solutions for normal platform behavior

**Why It Matters**: 
Platform restrictions are business constraints, not technical failures. Distinguishing them from infrastructure issues prevents unnecessary technical debt, maintains system confidence, and focuses engineering effort on actual problems rather than platform limitations.

### **BP #13: Comprehensive Cache Clearing Techniques**
**Principle**: Basic cache clearing through browser settings is often insufficient for debugging. Use multiple cache clearing methods to ensure complete cache invalidation.

**Implementation**:

**Level 1: Basic Browser Cache Clearing**
- Chrome Settings → Privacy → Clear browsing data → Cached images and files
- **Limitation**: May not clear all types of cache

**Level 2: Hard Refresh (Recommended for debugging)**
- `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- **Better**: Right-click refresh button → "Empty Cache and Hard Reload"
- **Best**: Open DevTools → Right-click refresh → "Empty Cache and Hard Reload"

**Level 3: Developer Tools Cache Clearing**
```
1. Open DevTools (F12)
2. Go to Network tab
3. Check "Disable cache" checkbox
4. Keep DevTools open while testing
5. This prevents ALL caching while DevTools is open
```

**Level 4: Comprehensive Cache Clearing**
```
1. Open DevTools (F12)
2. Right-click on refresh button
3. Select "Empty Cache and Hard Reload"
4. OR: DevTools → Application tab → Storage → Clear storage
```

**Level 5: Nuclear Option (When nothing else works)**
```
1. Close all browser windows
2. Clear all browsing data (All time)
3. Restart browser
4. Open in Incognito/Private mode
5. Test in different browser entirely
```

**Cache Types to Consider**:
- Browser cache (images, CSS, JS)
- DNS cache (`ipconfig /flushdns` on Windows)
- Service Worker cache (DevTools → Application → Service Workers)
- Local Storage (DevTools → Application → Local Storage)
- Session Storage (DevTools → Application → Session Storage)

**Real-World Example**:
- **Problem**: API calls still showing old error messages after fix deployment
- **Level 1 Clearing**: Chrome settings cache clear → Still failing
- **Level 3 Clearing**: DevTools "Disable cache" → Still failing  
- **Level 5 Clearing**: Incognito mode → Works! (Confirms cache issue)
- **Lesson**: Service Worker was caching API responses, needed Application tab clearing

**When Cache Clearing Doesn't Work**:
- If Level 5 clearing doesn't resolve the issue, the problem is NOT cache-related
- Immediately pivot to server-side investigation
- Don't spend more than 10 minutes total on cache troubleshooting
- Use cache clearing failure as confirmation that the issue is deeper

**Why It Matters**: 
Different types of cache require different clearing methods. Modern web apps use multiple caching layers (browser, service workers, local storage) that basic cache clearing doesn't address.

### **BP #4: Implement the "Change-Test-Analyze" Cycle**
**Principle**: After every change, test specifically for the original problem AND verify you didn't break something else.

**Implementation**:
1. **Make one targeted change**
2. **Test the original failure scenario** 
3. **Analyze the result**:
   - Same problem still exists? → Your change was ineffective, consider reverting
   - Problem gone but new errors? → Your change was wrong, revert immediately  
   - Problem gone, no new errors? → Your change was correct, document it
4. **Run smoke tests** on unrelated functionality

**Example**:
After "fixing" nginx configuration:
- Test: Does the API call still return 404?
- Result: Still 404 → Nginx wasn't the issue
- Analysis: Revert nginx changes OR keep them if they're genuinely beneficial
- Action: Look for the real cause elsewhere

**Why It Matters**: 
Prevents accumulating ineffective changes that complicate future debugging.

### **BP #8: Validate Fixes at Multiple Abstraction Levels**
**Principle**: A real fix should work consistently across different testing approaches.

**Implementation**:
- **Unit Level**: Test individual functions/endpoints
- **Integration Level**: Test component interactions  
- **System Level**: Test full user workflows
- **Browser Level**: Test actual user experience
- **Network Level**: Monitor traffic and responses

**Example**:
After fixing mixed content errors:
- Server test: `curl https://domain.com/api/v1/metadata` → 422 (correct)
- Frontend test: Check browser network tab → Clean HTTPS calls
- User test: Try entering a video URL → Should process successfully
- Security test: No mixed content warnings in console

**Why It Matters**: 
Fixes that work at one level but fail at another indicate incomplete solutions.

### **BP #10: Apply the Principle of Least Change**
**Principle**: Solve problems with the smallest change that addresses the root cause, not the most comprehensive change possible.

**Implementation**:
- Target specific patterns/lines rather than rebuilding entire components
- Use runtime patches (`sed`, configuration updates) before rebuilding
- Change one system at a time, not multiple systems simultaneously
- Prefer configuration changes over code changes when both solve the problem
- Ask: "What's the minimal viable fix?" before implementing

**Example**:
Mixed content issue solutions in order of preference:
1. **Best**: `sed -i 's|http:///api|/api|g'` on existing files (targeted)
2. **Good**: Rebuild frontend with fixed environment variables (component-level)  
3. **Overkill**: Rebuild entire application stack (system-level)

**Why It Matters**: 
Minimal changes are easier to understand, debug, and rollback. They reduce the risk of introducing new problems while solving the original issue.

### **BP #7: Document the Discovery Process, Not Just the Solution**
**Principle**: Future debugging benefits more from understanding the discovery process than just knowing the final fix.

**Implementation**:
- Keep a debug notes file with timestamp, symptoms, tests performed, and results
- Record what you tried that DIDN'T work and why
- Document false leads and dead ends
- Explain the reasoning behind each diagnostic step
- Include the exact commands used and their outputs

**Example**:
```markdown
## Issue: API calls returning 404
### Hypothesis 1: Nginx routing missing
- Test: `curl http://localhost/api/v1/health`  
- Result: 404
- Action: Added nginx proxy config
- Retest: Still 404
- Conclusion: Nginx wasn't the issue, but config was still beneficial

### Hypothesis 2: Frontend calling wrong URLs
- Test: Check browser network tab  
- Result: Calling `http://api/v1/metadata` (mixed content)
- Action: Fixed JavaScript URLs
- Retest: Clean relative URLs
- Conclusion: This was the root cause
```

**Why It Matters**: 
Documentation prevents repeating the same failed debugging paths in future incidents.

---

## **Level 2: Environment & Architecture Awareness**
*Practices for handling the complexities of different environments (dev, prod), deployment pipelines, and architectural variations.*

### **BP #9: Distinguish Between Development and Production Reality**
**Principle**: Production environments have different constraints, configurations, and failure modes than development.

**Implementation**:
- Never assume local behavior matches production behavior
- Test environment-specific configurations (Docker, nginx, SSL, DNS)
- Understand the complete production stack, not just your application code
- Use production-equivalent tooling for testing fixes
- Be aware of caching layers (browser, CDN, reverse proxy) that don't exist locally

**Example**:
- Development: API calls to `localhost:8000` work fine
- Production: Same code calls `localhost:8000` but runs in Docker → connection refused
- Solution: Environment-aware configuration that uses relative URLs in production

**Why It Matters**: 
Development-focused fixes often fail in production due to environmental differences.

### **BP #14: Always Verify Environment Context Before Debugging**
**Principle**: Never assume which environment the user is working in; explicitly confirm production vs development context before applying any fixes.

**Implementation**:
- Ask explicitly: "Are you seeing this error in production or development?"
- Check URLs in screenshots: `memeit.pro` = production, `localhost:3000` = development
- Verify environment indicators: HTTPS vs HTTP, domain names, port numbers
- Match debugging approach to the actual environment being used
- Don't switch environments mid-debugging without explicit user confirmation

**Real-World Example**:
- **User Statement**: "My production console was showing errors"
- **Assistant Error**: Assumed development environment and started Docker containers
- **Correct Approach**: Should have asked "Are you debugging the live production site at memeit.pro or local development?"
- **Lesson**: Environment assumption led to solving the wrong problem entirely

**Why It Matters**: 
Debugging the wrong environment wastes time and can miss critical production-specific issues. Production and development have completely different failure modes, configurations, and constraints.

### **BP #15: Distinguish Between "Service Down" vs "Configuration Error"**
**Principle**: When services aren't running locally, don't assume that explains production errors on live domains.

**Implementation**:
- If user reports production domain errors, test the production domain directly
- Don't pivot to local environment setup unless explicitly asked
- Production issues require production-focused debugging (DNS, CDN, SSL, deployment)
- Local service failures are irrelevant to production domain problems
- Ask: "Is this affecting your live website or your local development setup?"

**Real-World Example**:
- **User Context**: Production website showing API 404 errors
- **Assistant Error**: Found Docker wasn't running locally and "fixed" by starting development environment  
- **Correct Approach**: Should have tested `curl https://memeit.pro/api/v1/health` to diagnose actual production issue
- **Lesson**: Local Docker status is irrelevant to production domain problems

**Why It Matters**: 
Production websites don't depend on local Docker containers. Solving local environment issues doesn't fix live website problems.

### **BP #16: Always Verify Branch Architecture Before Debugging Production Issues**
**Principle**: Different branches may have completely different architectures, deployment mechanisms, and CI/CD configurations. Never assume all branches use the same stack.

**Implementation**:
- **Check CI/CD Configuration First**: Look at `.github/workflows/` to see which branch triggers production deployment
- **Compare Branch Architectures**: Different branches may use different reverse proxies (nginx vs Caddy), frontend frameworks (Next.js vs React/Vite), or deployment strategies
- **Verify Frontend Location**: Check if production uses `frontend/` vs `frontend-new/` vs other directories
- **Understand Deployment Chain**: Map out how code flows from branch → CI/CD → production environment

**Real-World Example**:
- **Problem**: Production showing "Failed to fetch video information" with double `/api/api/` URLs
- **Initial Assumption**: API routing issue, nginx configuration problem
- **Reality Discovery**: 
  - `main` branch: Next.js frontend + FastAPI serving static files + Caddy reverse proxy
  - `master` branch: React/Vite frontend + nginx reverse proxy + separate frontend container
  - **Root Cause**: Production deployed from `main` (old architecture) while fixes were applied to `master` (new architecture)
- **Solution**: Update CI/CD workflow to deploy from `master` branch instead of `main`

**Key Questions to Ask**:
1. Which branch does production actually deploy from?
2. Are there architectural differences between branches?
3. When was the last time production was updated from the current branch?
4. Does the branch I'm debugging match the branch that's actually deployed?

**Why It Matters**: 
You can spend hours debugging the wrong architecture. Production issues must be debugged against the actual deployed branch and its specific architecture, not the development branch you happen to be working on.

### **BP #17: Understand Frontend Update Context and Migration States**
**Principle**: When users mention "recently updated the frontend," this is a critical architectural context that changes everything about debugging approach.

**Implementation**:
- **Ask About Recent Changes**: If debugging frontend issues, explicitly ask "Have you recently updated or migrated the frontend?"
- **Identify Migration States**: 
  - Old frontend still in production but new frontend in development
  - Multiple frontend directories (`frontend/`, `frontend-new/`, `frontend-backup/`)
  - CI/CD pointing to wrong branch after frontend migration
- **Map Frontend-to-Deployment Chain**: Trace from frontend code → build process → deployment → production serving
- **Check Environment Configuration**: New frontends often have different environment variable patterns, API base URLs, or build configurations

**Real-World Example**:
- **User Context**: "We recently updated the frontend to a new one"
- **Critical Insight**: This meant:
  - Production still running old frontend architecture (Next.js + FastAPI static serving)
  - New frontend architecture (React/Vite + nginx) existed but wasn't deployed
  - All debugging efforts on new architecture were irrelevant to production issues
- **Lesson**: Frontend migration context immediately changes debugging from "fix the code" to "fix the deployment pipeline"

**Migration State Indicators**:
- Multiple frontend directories in project structure
- Different package.json files with different frameworks
- Docker configurations mentioning different frontend paths
- CI/CD workflows referencing different branches or build processes

**Why It Matters**: 
Frontend migrations create a gap between development architecture and production architecture. Debugging must target the actually deployed architecture, not the desired future architecture.

### **BP #18: Distinguish Between Code Issues and Deployment Pipeline Issues**
**Principle**: When production shows errors but development works fine, the problem is often in the deployment pipeline, not the application code.

**Implementation**:
- **Check Deployment Recency**: When was production last deployed? From which branch?
- **Compare Branch Timestamps**: Is the deployed branch older than recent fixes?
- **Verify CI/CD Triggers**: Does the CI/CD workflow trigger on the branch you're working on?
- **Trace Deployment Chain**: Code changes → branch push → CI/CD trigger → build → deployment
- **Look for Deployment Gaps**: Are fixes being applied to a branch that doesn't trigger production deployment?

**Real-World Example**:
- **Problem**: Production API calls failing with routing errors
- **Development Status**: Local development working perfectly, all fixes applied
- **Discovery Process**:
  1. Fixes applied to `master` branch ✅
  2. Local development using `master` branch ✅
  3. CI/CD configured to deploy from `main` branch ❌
  4. Production never received the fixes because wrong branch was being deployed
- **Solution**: Update CI/CD to deploy from `master` instead of `main`

**Deployment Pipeline Red Flags**:
- User reports production errors but local development works
- Recent commits exist but production behavior unchanged
- CI/CD workflow hasn't run recently despite code changes
- Multiple active branches with different architectures

**Why It Matters**: 
Code can be perfect but production can still fail if the deployment pipeline isn't connecting the right code to the production environment. Always verify the deployment chain before debugging application logic.

### **BP #19: Use Architecture-Aware Debugging Strategies**
**Principle**: Different frontend architectures require completely different debugging approaches. Tailor your diagnostic strategy to the actual deployed architecture.

**Implementation**:

**For Next.js + FastAPI Static Serving Architecture**:
- Check FastAPI static file mounting configuration
- Verify build output directory (`out/` or `dist/`) matches FastAPI expectations
- Test API base URL resolution in production environment
- Debug relative vs absolute URL patterns

**For React/Vite + nginx Reverse Proxy Architecture**:
- Check nginx proxy_pass configuration
- Verify upstream backend connectivity
- Test nginx routing rules
- Debug CORS and proxy header forwarding

**For Containerized Deployments**:
- Verify container networking between frontend and backend
- Check environment variable injection into containers
- Test inter-container communication
- Debug volume mounts and file serving

**Architecture Detection Methods**:
```bash
# Check Docker configuration
grep -r "nginx" docker-compose.yml
grep -r "static" backend/app/main.py

# Check build configuration
ls -la frontend*/
cat frontend*/package.json | grep -E "(next|vite|react)"

# Check CI/CD deployment strategy
cat .github/workflows/*.yml | grep -A5 -B5 "deploy"
```

**Why It Matters**: 
Using nginx debugging techniques on a FastAPI static-serving architecture (or vice versa) wastes time and can introduce unnecessary configuration changes. Match your debugging strategy to the actual deployed architecture.

### **BP #24: Design for Portability - Eradicate Environment-Specific Code**
**Principle**: When an application is moved from a controlled environment (like Docker) to a different OS (like Windows), hidden environment-specific assumptions become critical failures. Code must be written to be portable and agnostic to the underlying operating system and environment.

**Implementation**:
- **Externalize All Paths and Hostnames**: Never hardcode file paths (`/usr/bin/ffmpeg`) or hostnames (`redis://redis:6379`) directly in the code.
- **Use Platform-Agnostic Defaults**: Provide sensible, cross-platform defaults (e.g., `ffmpeg` instead of `/usr/bin/ffmpeg`) that rely on the system's `PATH`.
- **Centralize Configuration**: Use a single, centralized configuration system (like `pydantic-settings` with `.env` files) for all services (backend, worker, etc.) to ensure consistency. Do not let services have their own independent, hardcoded settings.
- **Verify Working Directories**: When executing scripts or commands, always ensure you are in the correct working directory. Scripts should either be run from the project root or explicitly change to the required directory before execution.

**Real-World Example from This Session**:
- **Problem 1**: The worker failed because its `ffmpeg_path` was hardcoded to the Linux path `/usr/bin/ffmpeg`.
- **Problem 2**: The worker failed to connect to Redis because its `REDIS_URL` was hardcoded to the Docker-specific hostname `redis`, and it wasn't loading the shared `.env` file.
- **Problem 3**: The worker failed because `poetry` commands were run from the `worker/` directory instead of the `backend/` directory where `pyproject.toml` resided.
- **Solution**:
    1. Moved `ffmpeg_path` and `redis_url` into the centralized Pydantic `Settings` model.
    2. Used platform-agnostic defaults (`ffmpeg`, `localhost`).
    3. Refactored the worker to import and use the centralized settings.
    4. Corrected the startup script to `cd` into the `backend` directory before running the worker.

**Why It Matters**: 
Docker and other containerization technologies are excellent at hiding environment-specific issues. A truly robust application must be able to run natively on different operating systems without code changes. This is critical for enabling local development and ensuring portability.

### **BP #12: Verify Configuration Import/Export Consistency**
**Principle**: Ensure configuration files are actually being used where you expect them to be used.

**Implementation**:
- Check that configuration imports are pointing to the correct files
- Verify environment-specific configurations are being loaded in the right contexts
- Trace configuration values from source to consumption to find disconnects
- Don't assume modular configuration files are automatically connected

**Real-World Example**:
- **Problem**: Frontend still using `localhost:8000` despite having correct environment configuration
- **Discovery**: `api.ts` was using hardcoded `import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'`
- **Solution**: Changed to `import { config } from '../config/environment'` and use `config.API_BASE_URL`
- **Lesson**: Having correct configuration in `environment.ts` was useless if `api.ts` wasn't importing it

**Why It Matters**: 
Configuration can exist in the codebase but not be utilized. Always trace the actual import/usage chain, not just the configuration definitions.

---

## **Level 3: Code Quality & CI/CD Integrity**
*Rules for maintaining a clean codebase and ensuring the CI/CD pipeline remains green.*

### **BP #21: Execute Complete Linting Suite Before Any CI/CD Push**
**Principle**: When fixing any linting error, always run the complete linting suite to identify ALL violations before pushing. Never fix one linting tool's errors in isolation.

**Implementation**:

**Critical Comprehensive Check Process**:
```bash
# Step 1: Fix the immediate visible error
poetry run black --check .  # Fix Black formatting

# Step 2: MANDATORY - Run complete linting suite
poetry run black --check .     # ✅ Formatting
poetry run isort --check-only . # ✅ Import sorting  
poetry run flake8 . --count     # ✅ Style violations
poetry run mypy app/            # ✅ Type checking

# Step 3: Address ALL critical violations found
# Step 4: Only push after complete suite passes
```

**Common Mistake Pattern**:
```bash
# ❌ WRONG: Fix only visible error
poetry run black --check .  # Fix and push immediately
git push origin master       # CI/CD fails on flake8/mypy

# ✅ RIGHT: Fix all linting comprehensively  
poetry run black --check .     # Fix Black first
poetry run flake8 . --count    # Discover 34 more violations
# Fix all critical violations systematically
# Push only after complete linting suite passes
```

**Real-World Learning Example**:
- **Initial Issue**: CI/CD failed on Black formatting (1 file)
- **Incomplete Fix**: Fixed Black, pushed immediately 
- **Consequence**: CI/CD still failed on 34 Flake8 violations (E402, E501)
- **Correct Process**: Should have run complete linting suite before first push
- **Result**: Required multiple fix cycles instead of comprehensive single fix

**Priority-Based Resolution**:
1. **Critical Functional**: E402 (imports), F821 (undefined vars), E722 (bare except)
2. **Important Logic**: F601 (duplicate keys), F541 (f-strings), F841 (unused vars)  
3. **Cosmetic**: E501 (line length), E203 (whitespace), W503 (line breaks)

**When to Use Temporary Ignores**:
- For cosmetic issues with >20 violations: Add to `extend-ignore` in setup.cfg
- For systematic refactoring needed: Document in TODO and ignore temporarily
- For legitimate edge cases: Use `# noqa: ERRORCODE` with comment explaining why

**Verification Checklist Before Push**:
```bash
# Complete linting suite must ALL return 0 errors
poetry run black --check . && echo "✅ Black"
poetry run isort --check-only . && echo "✅ isort"  
poetry run flake8 . --count && echo "✅ flake8"
poetry run mypy app/ && echo "✅ mypy"

# Only proceed to git push after all checks pass
```

**Why It Matters**: 
CI/CD workflows typically run multiple linting tools in sequence. Fixing one tool's errors while leaving others failing just moves the failure point later in the pipeline. Best Practice #12 exists specifically to prevent incomplete fixes that require multiple fix cycles.

**Self-Verification Questions**:
- Did I run ALL linting tools mentioned in the CI/CD workflow?
- Are there any remaining critical functional errors?
- Can I explain why any ignored errors are safe to defer?
- Does the complete linting suite pass locally before pushing?

### **BP #20: Systematically Resolve CI/CD Pipeline Errors with Priority-Based Approach**
**Principle**: When CI/CD pipelines fail due to code quality issues, distinguish between critical functional errors and cosmetic issues. Fix functional blockers first, then assess whether cosmetic issues need immediate resolution.

**Implementation**:

**Step 1: Categorize Errors by Criticality**
- **Critical (Must Fix)**: F821 (undefined variables), F401 (unused imports), E722 (bare except), F601 (duplicate keys)
- **Important (Should Fix)**: F541 (f-string placeholders), F841 (unused variables), E402 (import order)
- **Cosmetic (Can Defer)**: E501 (line length), E203 (whitespace), W503 (line breaks)

**Step 2: Use Automated Tools Strategically**
```bash
# Fix critical undefined variables and unused imports first
poetry run flake8 . --select=F821,F401,E722,F601 --count

# Use autoflake for safe automated cleanup
autoflake --remove-all-unused-imports --in-place --recursive .

# Use black for consistent formatting
poetry run black .

# Use isort for import organization
poetry run isort .
```

**Step 3: Fix Critical Issues Manually**
- **F821**: Add missing parameters, imports, or variable definitions
- **E722**: Replace bare `except:` with specific exception types
- **F601**: Remove duplicate dictionary keys in test data
- **F541**: Remove f-string prefix from strings without placeholders

**Step 4: Apply Minimal Changes Principle**
- Don't fix all cosmetic issues if they're not blocking deployment
- Focus on issues that break functionality or security
- Document remaining cosmetic issues for future cleanup

**Real-World Example**:
- **Initial State**: 55 Flake8 errors blocking CI/CD pipeline
- **Priority Analysis**: 
  - 5 critical functional errors (F821, E722, F601, F841)
  - 7 f-string formatting issues (F541)  
  - 35 cosmetic line length issues (E501)
  - 3 import order issues (E402)
- **Systematic Resolution**:
  1. Fixed all F821 undefined variables → enabled functionality
  2. Fixed E722 bare except → improved error handling security
  3. Fixed F601 duplicate keys → corrected test data integrity
  4. Fixed F541/F841 formatting → code consistency
  5. Left 35 E501 issues → cosmetic, non-blocking
- **Result**: CI/CD pipeline unblocked, functionality restored

**Error-Specific Resolution Strategies**:

**F821 (Undefined Variables)**:
```python
# Before: Missing parameter
def cleanup_job(job_id):  # Missing redis parameter
    redis.delete(f"job:{job_id}")

# After: Add required parameter  
def cleanup_job(job_id, redis):
    redis.delete(f"job:{job_id}")
```

**E722 (Bare Except)**:
```python
# Before: Unsafe bare except
try:
    width, height = map(int, fmt.resolution.split("x"))
except:
    return (0, 0)

# After: Specific exception handling
try:
    width, height = map(int, fmt.resolution.split("x"))
except (ValueError, AttributeError):
    return (0, 0)
```

**F601 (Duplicate Dictionary Keys)**:
```python
# Before: Duplicate keys overwrite each other
job_data = {
    "url": "https://youtube.com/watch?v=test",  # Original URL
    "url": "https://s3.amazonaws.com/file.mp4"  # Download URL
}

# After: Use different keys
job_data = {
    "source_url": "https://youtube.com/watch?v=test",
    "url": "https://s3.amazonaws.com/file.mp4"  # Download URL
}
```

**Step 5: Verify Critical Fixes**
```bash
# Ensure all functional errors are resolved
poetry run flake8 . --select=F821,F401,E722,F601 --count
# Should return: 0

# Check remaining cosmetic issues
poetry run flake8 . --count
# Acceptable if only E501, E402, W503 remain
```

**Step 6: Commit and Push Systematically**
```bash
git add .
git commit -m "Fix critical CI/CD lint errors

- Fix F821 undefined variables 
- Fix E722 bare except clauses
- Fix F601 duplicate dictionary keys
- Fix F541 f-string placeholders
- Remaining N cosmetic issues are non-blocking"

git push origin master
```

**Why It Matters**: 
CI/CD pipelines often block on any lint errors, but not all errors are equally critical. Fixing functional errors first ensures the pipeline can proceed while allowing cosmetic improvements to be addressed in follow-up work. This prevents perfectionism from blocking deployment.

**Automation vs Manual Balance**:
- Use automated tools (black, isort, autoflake) for safe, consistent changes
- Manually fix logic errors (undefined variables, bare except) that require human judgment
- Don't use automated formatters that might break working code patterns

### **BP #29: Treat Prettier Violations as Build-Blocking Errors**
**Principle**: In many pipelines Prettier runs after ESLint. A single unformatted file will fail `npm run lint` _even when ESLint has only warnings_. Always run `npx prettier --check .` locally before committing.

**Implementation**:
- Integrate Prettier into the pre-commit hook or IDE "save" action.
- Before each push run: `npm run lint && npx prettier --check .`.
- Use `--write` to fix and **re-stage** the file in the same commit.

**Real-World Example**: The CI Docker build aborted at `npm run build:production` because Prettier found two un-formatted files (`Index.tsx` and `svg.d.ts`).  Running Prettier locally and pushing the formatted files unblocked the build.

---

## **Level 4: Implementation-Specific Practices**
*Guidelines for specific technologies and layers of the stack.*

### **Git & Repository Management**
#### **BP #5: Maintain Rollback Safety Nets**
**Principle**: Always have a clear path back to the last known working state.

**Implementation**:
- Tag production-worthy commits: `git tag pre-fix-attempt`
- Keep previous commit hash handy: `git rev-parse HEAD~1`  
- Create configuration backups before changes
- Document what each change was supposed to fix
- If fix fails, `git revert <hash>` immediately, don't pile on more fixes

**Example**:
```bash
# Before attempting fix
git tag pre-metadata-fix
docker cp container:/etc/nginx/nginx.conf ./nginx.conf.backup

# After failed fix
git revert HEAD  # or git reset --hard pre-metadata-fix
docker cp ./nginx.conf.backup container:/etc/nginx/nginx.conf
```

**Why It Matters**: 
Failed fixes that aren't properly reverted create compound problems that are exponentially harder to debug.

### **Backend & Dependencies (Python/Poetry)**
#### **BP #25: Systematic Dependency Resolution for Cross-Platform Setups**
**Principle**: Migrating to a local, non-containerized setup often reveals deep-seated dependency conflicts. Resolving them requires a systematic approach, as a single change can have cascading effects.

**Implementation**:

**The "Add → Lock → Install → Verify" Cycle**:
1.  **Add/Update Dependency**: Make the smallest necessary change in `pyproject.toml`.
2.  **Lock Dependencies**: Run `poetry lock` to resolve the entire dependency tree. This is the most critical step. **Do not skip it.**
3.  **Install from Lock File**: Run `poetry install`. This ensures the environment exactly matches the newly generated lock file.
4.  **Verify Functionality**: Run the application to ensure the primary functionality that depends on the new package works as expected.

**Common Pitfalls and Solutions**:
- **Conflict During `lock`**: If `poetry lock` fails, resist the urge to use overly broad version constraints like `*`. Instead:
    - Read the error to see which packages are in conflict.
    - Try upgrading the *other* packages involved in the conflict.
    - If a package that interacts with external services (like `yt-dlp`) is involved, it often needs to be pinned to the *latest* version, as its functionality depends on external APIs.
- **Missing Dependency in Code**: If you add a new `import`, immediately add the corresponding package to `pyproject.toml`. A `ModuleNotFoundError` is a direct sign this step was missed.

**Real-World Example from This Session**:
- **Problem**: A series of cascading dependency failures.
- **Sequence**:
    1.  `ModuleNotFoundError: pydantic_settings` → Added `pydantic-settings` to `pyproject.toml`.
    2.  `poetry install` failed → Realized `poetry lock` was needed.
    3.  `poetry lock` failed due to an `rq` version conflict.
    4.  Changed `rq` to `*`, which caused `yt-dlp` to be downgraded.
    5.  The old `yt-dlp` failed to download from Facebook.
- **Systematic Solution**:
    1.  Pinned `yt-dlp` to the latest version (`^2025.6.25`) in `pyproject.toml`.
    2.  Ran `poetry lock` which successfully resolved the tree around the new `yt-dlp` version.
    3.  Ran `poetry install` to apply the changes.

**Why It Matters**: 
The `poetry.lock` file is the single source of truth for a reproducible environment. Bypassing or mismanaging it leads to unpredictable behavior, especially when moving between environments.

### **Frontend & User Interface (React/Vite/Tests)**
#### **BP #26: Ensure Frontend Data Models are Synchronized with Backend Payloads**
**Principle**: Frontend components often fail silently or with confusing errors if their data models (e.g., TypeScript interfaces) do not perfectly match the JSON schema of the API responses they consume.

**Implementation**:
- **Schema-First Approach**: Ideally, use a shared schema (e.g., OpenAPI) to generate both backend models and frontend types.
- **Manual Verification**: When creating or updating a frontend interface, have the backend API response open and verify every field, paying close attention to optional (`?`) vs. required fields and their data types (`string`, `number`, etc.).
- **Defensive Frontend Coding**: Never assume a field will be present, even if the type definition says it's required. Use optional chaining (`?.`) and provide sensible fallbacks for potentially missing data.

**Real-World Example from This Session**:
- **Problem**: The frontend failed to render video formats correctly because the backend added an `audio_merged` property to the format object, but the frontend's `VideoFormat` TypeScript type was not updated to include it. In a previous session, a `filesize_approx` property was also missing.
- **Symptom**: Type errors during the build process, or components failing to render data correctly.
- **Solution**: Update the TypeScript `interface VideoFormat` to include `audio_merged?: boolean;` and any other new or changed fields from the API.

**Why It Matters**: 
A mismatch between the frontend's expectation and the backend's reality is a common source of bugs that can be difficult to trace. Keeping data contracts in sync is fundamental to the stability of a full-stack application.

#### **BP #27: Implement Robust and Idempotent Event Listeners in React**
**Principle**: Incorrectly managed event listeners in React are a common source of memory leaks, performance issues, and unexpected behavior. Listeners, especially those on the `window` object, must be added and removed correctly.

**Implementation**:
- **Symmetry in `useEffect`**: When adding an event listener in a `useEffect` hook, the cleanup function (`return () => ...`) must call `removeEventListener` with the *exact same arguments*, including the options object (e.g., `{ passive: false }`).
- **Eliminate Redundancy**: Avoid attaching the same event handlers in multiple places (e.g., once in JSX like `onTouchMove` and again with `window.addEventListener` in a `useEffect`). Choose one authoritative source for the event listener. For global drag events that should work outside a component's bounds, `useEffect` is the correct choice.
- **Explicitly Handle Passive Listeners**: For events like `touchmove` where you intend to call `preventDefault()`, you **must** register the listener with `{ passive: false }`. Failure to do so will result in console warnings and may prevent your code from blocking native browser behavior like scrolling.

**Real-World Example from This Session**:
- **Problem**: A `Unable to preventDefault inside passive event listener invocation` warning appeared when dragging the timeline slider on touch devices.
- **Root Cause**:
    1.  A `touchmove` listener was added in `useEffect` with `{ passive: false }`.
    2.  The cleanup function tried to remove it *without* the options object, meaning the listener was never removed.
    3.  A redundant `onTouchMove` handler was also present in the JSX, which did not have the `passive: false` option.
- **Solution**:
    1.  Corrected the `removeEventListener` call to include `{ passive: false }`.
    2.  Removed the redundant `onTouchMove` and other drag-related handlers from the JSX, making the `useEffect` hook the single source of truth for these global listeners.

**Why It Matters**: 
Modern browsers aggressively optimize touch events for smooth scrolling. Developers must explicitly opt-out of this optimization when needed. Incorrectly cleaned-up listeners are a silent killer of application performance and stability.

#### **BP #28: Keep Tests Synchronized with UI Copy**
**Principle**: Whenever user-facing copy (placeholders, headings, descriptions) is changed, _update the corresponding unit/integration tests in the same commit_. Out-of-sync tests will explode in CI and block merges even though the application works fine.

**Implementation**:
1. Grep the test suite for the previous text (e.g. `youtube.*watch`).
2. Replace hard-coded strings or regexes with the new wording.
3. If copy will change frequently, prefer **semantic queries** (`getByRole`, `getByLabelText`) over brittle exact-match strings.
4. Run the full test suite locally before pushing.

**Real-World Example**:
- We shortened the UrlInput description and placeholder to be Facebook-only.  All Vitest specs that expected the old YouTube copy began failing.  Updating two test files and re-running `npm test` restored green status.

**Why It Matters**: CI failures caused by stale tests create noise and slow delivery.  Aligning tests with intentional UI copy changes keeps the pipeline green and the team confident.

**Real-World Pitfall (2025-07-01):** Updating the `UrlInput` placeholder from "video URL" to "facebook.com / instagram.com" broke three Vitest specs (`url-input-simple`, `components-fixed`, `accessibility-fixed`) and failed CI. Always grep for the old copy and update `getByPlaceholderText(...)` or switch to semantic queries before pushing.

#### **BP #30: Verify Static Assets Are Part of the Repository & Build**
**Principle**: A local build can silently load images from `public/`, but production Docker builds only include what the Docker context copies. Missing assets cause broken images and, if referenced in code, build failures.

**Implementation**:
1. After adding/renaming images, run `git status` and ensure they are tracked.
2. For multi-stage Dockerfiles, confirm the `COPY` step includes the asset path.
3. Use the production build command (`npm run build:production` or `vite build --mode production`) locally to catch missing-file errors early.

**Real-World Example**: The white logo rendered locally because it sat in `public/`, but failed in Lightsail build as the file wasn't added to Git.  Staging `Logos/white.svg` (and retina PNGs) fixed the issue.

#### **BP #31: Prefer URL Imports over `ReactComponent` for Simple SVGs in Vite**
**Principle**: Importing SVGs as React components (`import { ReactComponent as Logo } from "logo.svg"`) requires a compatible SVGR plugin. In production builds without the plugin, compilation fails. Importing the asset URL (`import logo from "logo.svg"`) and rendering with `<img>` avoids that risk.

**Implementation**:
- Use URL import (`import logoUrl from '.../logo.svg'`) for non-interactive icons.
- Only opt-in to SVGR when you need inline styling or dynamic fill; configure the plugin in `vite.config.ts` first.

**Real-World Example**: CI failed during `vite build` because SVGR wasn't enabled in the Docker image.  Switching to a plain URL import eliminated the dependency and unblocked the build.

**Why It Matters**: Minimizing build-time plugins keeps the production image smaller and the build process simpler.

---

## **Meta-Practice: The Learning Loop**
*The final, overarching principle of continuous improvement.*

### **🔄 Meta Best Practice: Continuous Learning Integration**
**Implementation**:
After each debugging session:
1. **What did we fix that was actually broken?** (Real progress)
2. **What did we change that wasn't actually broken?** (Wasted effort)  
3. **What assumptions proved wrong?** (Learning opportunities)
4. **What diagnostic approaches worked best?** (Methodology improvement)
5. **How can we prevent this class of issue in the future?** (Systemic improvement)
6. **What architectural context was missing initially?** (Context improvement)
7. **How did deployment pipeline issues mask/create the problem?** (Pipeline awareness)

**📝 Note**: This document is continuously updated with new best practices from real debugging sessions to improve precision in problem identification and resolution. Each new scenario adds learnings that prevent similar mistakes in future debugging efforts.

---

## 🎯 **Summary Principles**

1. **Prove before acting** - Establish ground truth first
2. **Layer your diagnosis** - Network → Console → Code  
3. **Find root causes** - Ask why three times
4. **Test every change** - Change-Test-Analyze cycle
5. **Maintain rollback** - Always have an escape route
6. **Test simply first** - Validate at lowest level
7. **Document discovery** - Process matters more than solutions
8. **Validate comprehensively** - Test at multiple levels
9. **Respect production** - Different constraints than development
10. **Minimize changes** - Smallest fix that solves root cause
11. **Verify server reality** - Browser perception vs server truth
12. **Check configuration chains** - Ensure configs are actually imported/used
13. **Use comprehensive cache clearing** - Multiple levels from hard refresh to incognito mode
14. **Verify environment context** - Production vs development confirmation required
15. **Service vs configuration** - Local service status irrelevant to production domain issues
16. **Verify branch architecture** - Different branches may have completely different deployment architectures
17. **Understand frontend migration context** - Recent frontend updates change entire debugging approach
18. **Distinguish code vs deployment issues** - Production errors with working development often indicate deployment pipeline problems
19. **Use architecture-aware debugging** - Match debugging strategy to actual deployed architecture
20. **Prioritize CI/CD errors systematically** - Fix critical functional errors before cosmetic issues
21. **Execute complete linting suite** - Run ALL linting tools before any CI/CD push, never fix in isolation
22. **Always push fixes to remote** - Local fixes don't affect CI/CD until pushed to repository
23. **Execute complete verification suite** - Run ALL backend AND frontend verification tools before every push to prevent regression cycles
24. **Design for portability** - Eradicate environment-specific code
25. **Systematic dependency resolution** - Resolve cross-platform setup conflicts
26. **Frontend data model synchronization** - Ensure API payloads are consumed correctly
27. **Robust event listeners in React** - Implement correct event handling
28. **Keep tests synchronized with UI copy** - Update tests in the same commit as copy changes
29. **Verify static assets are part of the repository & build** - Catch missing files in local and production builds
31. **Prefer URL imports over `ReactComponent` for simple SVGs in Vite** - Avoid build failures in production
32. **Distinguish platform behavior from infrastructure issues** - Use systematic layer-by-layer testing to prevent misattributing platform restrictions to infrastructure problems

These practices work together to create a systematic, safe, and effective approach to production problem resolution that minimizes system disruption while maximizing learning and long-term stability. Future investigations should use systematic layer-by-layer approaches to distinguish platform behavior from infrastructure issues. 