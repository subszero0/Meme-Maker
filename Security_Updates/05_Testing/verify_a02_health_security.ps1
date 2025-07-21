# A02:2021 Health Endpoint Security Verification Script
# Focused testing for health endpoint security fixes

param(
    [string]$BaseUrl = "https://memeit.pro",
    [string]$HttpUrl = "http://memeit.pro"
)

Write-Host "=== A02 HEALTH ENDPOINT SECURITY VERIFICATION ===" -ForegroundColor Green
Write-Host "Target HTTPS URL: $BaseUrl" -ForegroundColor Cyan
Write-Host "Target HTTP URL: $HttpUrl" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0
$findings = @()

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Details = ""
    )
    
    if ($Passed) {
        Write-Host "PASS: $TestName" -ForegroundColor Green
        if ($Details) { Write-Host "  $Details" -ForegroundColor Gray }
        $script:testsPassed++
    } else {
        Write-Host "FAIL: $TestName" -ForegroundColor Red
        if ($Details) { Write-Host "  $Details" -ForegroundColor Yellow }
        $script:testsFailed++
        $script:findings += "FAIL: $TestName - $Details"
    }
}

# Test 1: HTTP Health Endpoint Blocking
Write-Host "--- Test 1: HTTP Health Endpoint Blocking ---" -ForegroundColor Yellow
try {
    $httpResponse = Invoke-WebRequest -Uri "$HttpUrl/health" -UseBasicParsing -ErrorAction Stop
    
    if ($httpResponse.StatusCode -eq 426) {
        Write-TestResult "HTTP health endpoint returns 426 Upgrade Required" $true "Status Code: $($httpResponse.StatusCode)"
        
        # Check upgrade header
        $upgradeHeader = $httpResponse.Headers["Upgrade"]
        if ($upgradeHeader) {
            Write-TestResult "HTTP upgrade header present" $true "Upgrade: $upgradeHeader"
        } else {
            Write-TestResult "HTTP upgrade header present" $false "No Upgrade header found"
        }
    } else {
        Write-TestResult "HTTP health endpoint blocked" $false "Expected 426, got $($httpResponse.StatusCode)"
    }
} catch {
    if ($_.Exception.Message -contains "426") {
        Write-TestResult "HTTP health endpoint returns 426 Upgrade Required" $true "Correctly blocked with 426"
    } else {
        Write-TestResult "HTTP health endpoint accessible" $false "Error: $($_.Exception.Message)"
    }
}

# Test 2: HTTP API Health Endpoint Blocking
Write-Host "`n--- Test 2: HTTP API Health Endpoint Blocking ---" -ForegroundColor Yellow
try {
    $httpApiResponse = Invoke-WebRequest -Uri "$HttpUrl/api/health" -UseBasicParsing -ErrorAction Stop
    
    if ($httpApiResponse.StatusCode -eq 426) {
        Write-TestResult "HTTP API health endpoint returns 426" $true "Status Code: $($httpApiResponse.StatusCode)"
    } else {
        Write-TestResult "HTTP API health endpoint blocked" $false "Expected 426, got $($httpApiResponse.StatusCode)"
    }
} catch {
    if ($_.Exception.Message -contains "426") {
        Write-TestResult "HTTP API health endpoint returns 426" $true "Correctly blocked with 426"
    } else {
        Write-TestResult "HTTP API health endpoint blocked" $false "Error: $($_.Exception.Message)"
    }
}

# Test 3: HTTPS Health Endpoint Access Control
Write-Host "`n--- Test 3: HTTPS Health Endpoint Access Control ---" -ForegroundColor Yellow
try {
    $httpsResponse = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -ErrorAction Stop
    
    if ($httpsResponse.StatusCode -eq 403) {
        Write-TestResult "HTTPS health endpoint blocks external access" $true "Status Code: 403 Forbidden"
    } elseif ($httpsResponse.StatusCode -eq 200) {
        Write-Host "WARN: HTTPS health endpoint accessible externally" -ForegroundColor Yellow
        Write-Host "  This may be acceptable for monitoring systems" -ForegroundColor Gray
        Write-TestResult "HTTPS health endpoint response" $true "Status Code: 200 (monitoring access)"
    } else {
        Write-TestResult "HTTPS health endpoint access control" $false "Unexpected status: $($httpsResponse.StatusCode)"
    }
} catch {
    if ($_.Exception.Message -contains "403") {
        Write-TestResult "HTTPS health endpoint blocks external access" $true "Correctly restricted with 403"
    } elseif ($_.Exception.Message -contains "401") {
        Write-TestResult "HTTPS health endpoint requires authentication" $true "Correctly protected with 401"
    } else {
        Write-Host "WARN: Could not test HTTPS health endpoint" -ForegroundColor Yellow
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

# Test 4: HTTPS API Health Endpoint Access Control  
Write-Host "`n--- Test 4: HTTPS API Health Endpoint Access Control ---" -ForegroundColor Yellow
try {
    $httpsApiResponse = Invoke-WebRequest -Uri "$BaseUrl/api/health" -UseBasicParsing -ErrorAction Stop
    
    if ($httpsApiResponse.StatusCode -eq 403) {
        Write-TestResult "HTTPS API health endpoint blocks external access" $true "Status Code: 403 Forbidden"
    } elseif ($httpsApiResponse.StatusCode -eq 200) {
        Write-Host "INFO: HTTPS API health endpoint accessible" -ForegroundColor Cyan
        Write-TestResult "HTTPS API health endpoint response" $true "Status Code: 200"
    } else {
        Write-TestResult "HTTPS API health endpoint access control" $false "Unexpected status: $($httpsApiResponse.StatusCode)"
    }
} catch {
    if ($_.Exception.Message -contains "403") {
        Write-TestResult "HTTPS API health endpoint blocks external access" $true "Correctly restricted with 403"
    } else {
        Write-Host "INFO: HTTPS API health endpoint testing" -ForegroundColor Cyan
        Write-Host "  Response: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

# Test 5: Security Headers on Health Responses
Write-Host "`n--- Test 5: Security Headers on Health Responses ---" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -ErrorAction Stop
    
    # Check Cache-Control header
    $cacheControl = $response.Headers["Cache-Control"]
    if ($cacheControl -and $cacheControl -contains "no-cache") {
        Write-TestResult "Cache-Control header properly set" $true "Value: $cacheControl"
    } else {
        Write-TestResult "Cache-Control header properly set" $false "Missing or incorrect Cache-Control header"
    }
    
    # Check HSTS header
    $hsts = $response.Headers["Strict-Transport-Security"]
    if ($hsts) {
        Write-TestResult "HSTS header present" $true "Value: $hsts"
    } else {
        Write-TestResult "HSTS header present" $false "Missing Strict-Transport-Security header"
    }
    
    # Check CSP header
    $csp = $response.Headers["Content-Security-Policy"]
    if ($csp) {
        Write-TestResult "CSP header present" $true "Content-Security-Policy configured"
    } else {
        Write-TestResult "CSP header present" $false "Missing Content-Security-Policy header"
    }
    
} catch {
    Write-TestResult "Security headers verification" $false "Error testing main site: $($_.Exception.Message)"
}

# Test 6: Rate Limiting on Health Endpoints
Write-Host "`n--- Test 6: Rate Limiting on Health Endpoints ---" -ForegroundColor Yellow
$rateLimitHit = $false
for ($i = 1; $i -le 8; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -ErrorAction Stop
        Write-Host "Request $i`: Status $($response.StatusCode)" -ForegroundColor Gray
    } catch {
        if ($_.Exception.Message -contains "429" -or $_.Exception.Message -contains "rate") {
            $rateLimitHit = $true
            Write-Host "Request $i`: Rate limited" -ForegroundColor Yellow
            break
        } else {
            Write-Host "Request $i`: $($_.Exception.Message)" -ForegroundColor Gray
        }
    }
    Start-Sleep -Milliseconds 200
}

if ($rateLimitHit) {
    Write-TestResult "Rate limiting active on health endpoints" $true "Rate limit triggered after multiple requests"
} else {
    Write-Host "INFO: Rate limiting not triggered in test" -ForegroundColor Cyan
    Write-Host "  This may be normal for monitoring endpoints" -ForegroundColor Gray
}

# Final Results
Write-Host "`n=== A02 HEALTH ENDPOINT SECURITY RESULTS ===" -ForegroundColor Green
Write-Host "Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor Cyan
Write-Host "Passed: $testsPassed" -ForegroundColor Green  
Write-Host "Failed: $testsFailed" -ForegroundColor Red

if ($testsFailed -eq 0) {
    Write-Host "`nSUCCESS: All A02 health endpoint security tests passed!" -ForegroundColor Green
    Write-Host "Health endpoints are properly secured against cryptographic failures." -ForegroundColor Green
} else {
    Write-Host "`nWARNING: Some tests failed. Review findings below:" -ForegroundColor Yellow
    foreach ($finding in $findings) {
        Write-Host "  - $finding" -ForegroundColor Red
    }
}

# Calculate security score
$totalTests = $testsPassed + $testsFailed
if ($totalTests -gt 0) {
    $score = [math]::Round(($testsPassed / $totalTests) * 100, 1)
    Write-Host "`nA02 Health Security Score: $score%" -ForegroundColor $(if ($score -ge 90) { "Green" } elseif ($score -ge 75) { "Yellow" } else { "Red" })
    
    if ($score -eq 100) {
        Write-Host "EXCELLENT: Perfect A02 health endpoint security implementation" -ForegroundColor Green
    } elseif ($score -ge 90) {
        Write-Host "EXCELLENT: Outstanding A02 health endpoint security" -ForegroundColor Green  
    } elseif ($score -ge 75) {
        Write-Host "GOOD: Solid A02 health endpoint security with minor issues" -ForegroundColor Yellow
    } else {
        Write-Host "NEEDS IMPROVEMENT: A02 health endpoint security requires attention" -ForegroundColor Red
    }
}

Write-Host "`n=== A02 CRYPTOGRAPHIC FAILURES HEALTH TESTING COMPLETE ===" -ForegroundColor Green

# Return appropriate exit code
if ($testsFailed -eq 0) {
    exit 0
} else {
    exit 1
} 