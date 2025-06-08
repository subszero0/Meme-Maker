# 🧪 Testing Guide

**Meme Maker Testing Strategy**  
*Simple, Fast, Reliable*

---

## 📋 Overview

Our testing strategy follows the **Test Pyramid** principle with a focus on **business value** over implementation details.

### Test Distribution
- 🟦 **Unit Tests (70%)**: Fast, focused, business logic
- 🔸 **Integration Tests (20%)**: API contracts, system behavior  
- 🔺 **E2E Tests (5%)**: Critical user journeys
- 📊 **Static Analysis (5%)**: Linting, type checking

### Core Principles
1. **Fast Feedback**: Unit tests complete in < 1 minute
2. **Reliable**: Tests don't flake or depend on external services
3. **Maintainable**: Simple structure, minimal mocking
4. **Business Focused**: Test what users care about

---

## 🚀 Quick Start

### Running Tests Locally

```bash
# Quick feedback (< 1 minute)
./scripts/test-quick.sh

# Full validation (< 3 minutes)  
./scripts/test-full.sh

# Include E2E tests
./scripts/test-full.sh --with-e2e
```

### Windows Users

```powershell
# Quick feedback
.\scripts\test-quick.ps1

# Or run directly
cd backend && python -m pytest tests/test_business_logic.py tests/test_simple.py
cd frontend && npm test
```

---

## 🏗️ Test Structure

### Backend Tests (`backend/tests/`)

#### Unit Tests
- `test_business_logic.py` - Core business logic validation
- `test_simple.py` - Basic functionality tests

#### Integration Tests  
- `test_api_contracts.py` - API endpoint behavior
- `test_jobs.py` - Job workflow integration

#### E2E Tests
- `test_critical_path.py` - Complete user journey (URL → Download)

### Frontend Tests (`frontend/`)

#### Unit Tests
- `src/lib/__tests__/api.test.ts` - API client behavior
- `src/components/__tests__/` - Component logic (future)

#### E2E Tests
- `cypress/e2e/smoke.cy.ts` - Critical user flows

---

## 🧪 Test Categories Explained

### 🟦 Unit Tests
**Purpose**: Test individual functions and business logic  
**Speed**: < 1 second per test  
**Examples**:
- Duration validation logic
- Time format parsing
- Job status transitions
- URL validation

```python
def test_duration_validation_clips_too_long():
    """Test that clips over 30 minutes are rejected"""
    job_data = {
        "url": "https://youtube.com/watch?v=test",
        "start": 0,
        "end": 1801,  # Over 30 minutes
        "accepted_terms": True
    }
    
    with pytest.raises(ValueError, match="Clip too long"):
        JobCreate(**job_data)
```

### 🔸 Integration Tests
**Purpose**: Test API contracts and system integration  
**Speed**: < 10 seconds per test  
**Examples**:
- API endpoint response formats
- Error handling behavior
- Security headers
- CORS configuration

```python
def test_metadata_endpoint_contract_valid_youtube(client):
    """Test metadata endpoint returns correct structure"""
    response = client.post("/api/v1/metadata", json={
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    })
    
    assert response.status_code in [200, 400, 422]
    if response.status_code == 200:
        data = response.json()
        assert "title" in data
        assert "duration" in data
```

### 🔺 E2E Tests
**Purpose**: Test complete user journeys  
**Speed**: < 60 seconds per test  
**Examples**:
- Complete video clipping flow
- Error scenarios users encounter

```python
def test_complete_user_journey():
    """Test URL → Metadata → Job → Download flow"""
    # Step 1: Fetch metadata
    # Step 2: Create job
    # Step 3: Poll until complete
    # Step 4: Verify download URL
```

---

## 🎯 CI/CD Pipeline

### GitHub Actions Workflow
**File**: `.github/workflows/ci-simple.yml`

#### Stage 1: Unit Tests (< 1 minute)
- Backend unit tests
- Frontend unit tests
- Runs on all PRs

#### Stage 2: Integration Tests (< 1 minute)  
- API contract tests
- Job workflow tests
- Runs after unit tests pass

#### Stage 3: E2E Tests (< 1 minute)
- Critical user flow tests
- **Main branch only** (saves CI time)

### Pipeline Features
- ✅ **Fast**: < 3 minutes total
- ✅ **Parallel**: Unit tests run simultaneously
- ✅ **Fail Fast**: Stops on first failure
- ✅ **Clear**: Emoji indicators for easy scanning

---

## 📊 Test Performance

### Current Benchmarks
- **Unit Tests**: ~15 seconds
- **Integration Tests**: ~30 seconds  
- **E2E Tests**: ~45 seconds
- **Total**: < 3 minutes

### Performance Tips
1. **Use pytest-xdist** for parallel execution
2. **Mock external dependencies** in unit tests
3. **Use fixtures** for test data setup
4. **Skip slow tests** in quick runs

---

## 🛠️ Writing Good Tests

### Naming Convention
```python
def test_[component]_[scenario]_[expected_result]():
    """Clear description of what this test validates"""
```

### Structure: Arrange-Act-Assert
```python
def test_job_creation_with_valid_data():
    """Test that valid job data creates a job successfully"""
    # Arrange
    job_data = {
        "url": "https://youtube.com/watch?v=test",
        "start": 10,
        "end": 70,
        "accepted_terms": True
    }
    
    # Act
    job = JobCreate(**job_data)
    
    # Assert
    assert job.start_seconds == 10.0
    assert job.end_seconds == 70.0
```

### What to Test
✅ **Business logic** (duration validation, platform detection)  
✅ **Error conditions** (invalid URLs, long clips)  
✅ **API contracts** (response formats, status codes)  
✅ **Critical paths** (user signup, payment flow)  

❌ **Implementation details** (internal function calls)  
❌ **Framework behavior** (React rendering, FastAPI routing)  
❌ **External services** (YouTube API, S3 responses)  

---

## 🔧 Debugging Tests

### Running Individual Tests
```bash
# Single test file
pytest tests/test_business_logic.py -v

# Single test function
pytest tests/test_business_logic.py::test_duration_validation_clips_too_long -v

# With debugging
pytest tests/test_business_logic.py -v -s --pdb
```

### Common Issues

#### "FastAPILimiter not initialized"
```python
# Solution: Mock the limiter in tests
@pytest.fixture(autouse=True)
def mock_rate_limiter():
    with patch('fastapi_limiter.FastAPILimiter.init'):
        yield
```

#### "Cannot connect to Redis"
```python
# Solution: Use fakeredis
import fakeredis
redis_client = fakeredis.FakeRedis()
```

#### Frontend test timeouts
```javascript
// Solution: Increase timeout
test('api call', async () => {
  // Test code
}, 10000); // 10 second timeout
```

---

## 📈 Migration from Legacy Tests

### What We Removed (Phase 1)
- ❌ 6 test infrastructure files (testing the tests)
- ❌ 416-line worker integration test (FFmpeg internals)
- ❌ Complex mocking patterns with minimal business value
- ❌ 25+ redundant E2E tests

### What We Added (Phase 2)
- ✅ Business logic unit tests
- ✅ API contract integration tests
- ✅ Focused E2E tests for critical paths

### Benefits Achieved
- **52% fewer test files** to maintain
- **48% reduction** in test count
- **80% faster** CI pipeline
- **100% focus** on business value

---

## 🎯 Future Improvements

### Short Term
- [ ] Add component tests for complex React components
- [ ] Implement visual regression testing
- [ ] Add performance benchmarking tests

### Long Term  
- [ ] Contract testing with Pact.js
- [ ] Chaos engineering tests
- [ ] Load testing for scale validation

---

## 💡 Best Practices

### Do's
- ✅ Test behavior, not implementation
- ✅ Write descriptive test names
- ✅ Use real data when possible
- ✅ Keep tests independent and isolated
- ✅ Run tests before every commit

### Don'ts
- ❌ Test framework internals
- ❌ Over-mock external dependencies
- ❌ Write tests that depend on order
- ❌ Ignore flaky tests
- ❌ Skip tests in CI

---

## 🆘 Getting Help

### Resources
- 📖 **pytest docs**: https://docs.pytest.org/
- 📖 **Cypress docs**: https://docs.cypress.io/
- 📖 **Testing Library**: https://testing-library.com/

### Internal
- 💬 **Slack**: #engineering-testing
- 📧 **Email**: engineering-team@example.com
- 🎯 **TestsToDo.md**: Implementation roadmap

---

**Remember**: Tests are documentation. They should clearly express what your system does and give confidence to make changes. 🚀 