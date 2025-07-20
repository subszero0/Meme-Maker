# Security Headers Verification Script
# A02:2021 Cryptographic Failures - Security Headers Testing

param(
    [string]$BaseUrl = "https://memeit.pro",
    [string]$HttpUrl = "http://memeit.pro",
    [switch]$Verbose
)

Write-Host "=== SECURITY HEADERS VERIFICATION SCRIPT ===" -ForegroundColor Green
Write-Host "Target URL: $BaseUrl" -ForegroundColor Cyan
Write-Host "HTTP URL: $HttpUrl" -ForegroundColor Cyan
Write-Host ""

# Test results tracking
$testResults = @()
$criticalFindings = @()
$passed = 0
$failed = 0

function Test-SecurityHeader {
    param(
        [string]$Url,
        [string]$HeaderName,
        [string]$ExpectedPattern,
        [string]$Severity = "MEDIUM",
        [string]$Description
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -ErrorAction Stop
        $headerValue = $response.Headers[$HeaderName]
        
        if ($headerValue) {
            if ($ExpectedPattern -and $headerValue -notmatch $ExpectedPattern) {
                Write-Host "FAIL: $HeaderName header present but incorrect value" -ForegroundColor Red
                Write-Host "  Expected pattern: $ExpectedPattern" -ForegroundColor Yellow
                Write-Host "  Actual value: $headerValue" -ForegroundColor Yellow
                $script:failed++
                $script:testResults += "FAIL: $HeaderName - Incorrect value"
                
                if ($Severity -eq "HIGH" -or $Severity -eq "CRITICAL") {
                    $script:criticalFindings += "$Severity`: $HeaderName - $Description"
                }
                return $false
            } else {
                Write-Host "PASS: $HeaderName header present and correct" -ForegroundColor Green
                if ($Verbose) {
                    Write-Host "  Value: $headerValue" -ForegroundColor Gray
                }
                $script:passed++
                $script:testResults += "PASS: $HeaderName"
                return $true
            }
        } else {
            Write-Host "FAIL: $HeaderName header missing" -ForegroundColor Red
            Write-Host "  Description: $Description" -ForegroundColor Yellow
            $script:failed++
            $script:testResults += "FAIL: $HeaderName - Missing"
            
            if ($Severity -eq "HIGH" -or $Severity -eq "CRITICAL") {
                $script:criticalFindings += "$Severity`: $HeaderName missing - $Description"
            }
            return $false
        }
    }
    catch {
        Write-Host "ERROR: Failed to test $Url - $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
        $script:testResults += "ERROR: $HeaderName - Request failed"
        return $false
    }
}

function Test-HTTPSRedirect {
    param([string]$HttpUrl, [string]$ExpectedHttpsUrl)
    
    Write-Host "`n--- HTTP to HTTPS Redirect Test ---" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri $HttpUrl -Method GET -UseBasicParsing -MaximumRedirection 0 -ErrorAction SilentlyContinue
        
        if ($response.StatusCode -eq 301 -or $response.StatusCode -eq 302) {
            $location = $response.Headers.Location
            if ($location -and $location.StartsWith("https://")) {
                Write-Host "PASS: HTTP redirects to HTTPS ($($response.StatusCode))" -ForegroundColor Green
                Write-Host "  Redirect location: $location" -ForegroundColor Gray
                $script:passed++
                $script:testResults += "PASS: HTTPS Redirect"
                return $true
            } else {
                Write-Host "FAIL: HTTP redirects but not to HTTPS" -ForegroundColor Red
                Write-Host "  Redirect location: $location" -ForegroundColor Yellow
                $script:failed++
                $script:testResults += "FAIL: HTTPS Redirect - Wrong destination"
                $script:criticalFindings += "HIGH: HTTP not redirecting to HTTPS"
                return $false
            }
        } else {
            Write-Host "FAIL: HTTP does not redirect (Status: $($response.StatusCode))" -ForegroundColor Red
            $script:failed++
            $script:testResults += "FAIL: HTTPS Redirect - No redirect"
            $script:criticalFindings += "HIGH: HTTP accessible without redirect"
            return $false
        }
    }
    catch {
        Write-Host "ERROR: Failed to test HTTP redirect - $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
        $script:testResults += "ERROR: HTTPS Redirect - Request failed"
        return $false
    }
}

function Test-A02HealthEndpointSecurity {
    Write-Host "`n--- A02 HEALTH ENDPOINT SECURITY TEST ---" -ForegroundColor Yellow
    
    # Test 1: HTTP health endpoint should return 426
    Write-Host "Testing HTTP health endpoint blocking..."
    try {
        $httpHealthResponse = Invoke-WebRequest -Uri "$HttpUrl/health" -Method GET -UseBasicParsing -ErrorAction Stop
        if ($httpHealthResponse.StatusCode -eq 426) {
            Write-Host "PASS: HTTP health endpoint returns 426 Upgrade Required" -ForegroundColor Green
            $script:passed++
            $script:testResults += "PASS: A02 HTTP Health Blocking"
        } else {
            Write-Host "FAIL: HTTP health endpoint accessible (Status: $($httpHealthResponse.StatusCode))" -ForegroundColor Red
            $script:failed++
            $script:testResults += "FAIL: A02 HTTP Health Blocking"
            $script:criticalFindings += "HIGH: Health endpoint accessible via HTTP"
        }
    }
    catch {
        Write-Host "WARN: Could not test HTTP health endpoint - $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Test 2: HTTPS health endpoint external access should be restricted
    Write-Host "Testing HTTPS health endpoint access restrictions..."
    try {
        $httpsHealthResponse = Invoke-WebRequest -Uri "$BaseUrl/health" -Method GET -UseBasicParsing -ErrorAction Stop
        if ($httpsHealthResponse.StatusCode -eq 403) {
            Write-Host "PASS: HTTPS health endpoint blocks external access (403)" -ForegroundColor Green
            $script:passed++
            $script:testResults += "PASS: A02 HTTPS Health Access Control"
        } elseif ($httpsHealthResponse.StatusCode -eq 200) {
            Write-Host "WARN: HTTPS health endpoint accessible externally" -ForegroundColor Yellow
            Write-Host "  This may be acceptable for monitoring systems" -ForegroundColor Gray
            $script:testResults += "WARN: A02 HTTPS Health External Access"
        } else {
            Write-Host "INFO: HTTPS health endpoint status: $($httpsHealthResponse.StatusCode)" -ForegroundColor Cyan
        }
    }
    catch {
        if ($_.Exception.Message -contains "403") {
            Write-Host "PASS: HTTPS health endpoint properly restricted (403)" -ForegroundColor Green
            $script:passed++
            $script:testResults += "PASS: A02 HTTPS Health Access Control"
        } else {
            Write-Host "WARN: Could not test HTTPS health endpoint - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # Test 3: API health endpoint restrictions
    Write-Host "Testing API health endpoint access..."
    try {
        $apiHealthResponse = Invoke-WebRequest -Uri "$BaseUrl/api/health" -Method GET -UseBasicParsing -ErrorAction Stop
        Write-Host "INFO: API health endpoint status: $($apiHealthResponse.StatusCode)" -ForegroundColor Cyan
    }
    catch {
        if ($_.Exception.Message -contains "403") {
            Write-Host "PASS: API health endpoint properly restricted (403)" -ForegroundColor Green
            $script:passed++
            $script:testResults += "PASS: A02 API Health Access Control"
        } else {
            Write-Host "WARN: Could not test API health endpoint - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# Main testing sequence
Write-Host "=== TESTING HTTP TO HTTPS REDIRECT ===" -ForegroundColor Magenta
Test-HTTPSRedirect -HttpUrl $HttpUrl -ExpectedHttpsUrl $BaseUrl

Write-Host "`n=== TESTING SECURITY HEADERS ===" -ForegroundColor Magenta

# Test HSTS (HTTP Strict Transport Security)
Test-SecurityHeader -Url $BaseUrl -HeaderName "Strict-Transport-Security" -ExpectedPattern "max-age=\d+" -Severity "HIGH" -Description "Prevents protocol downgrade attacks"

# Test CSP (Content Security Policy)
Test-SecurityHeader -Url $BaseUrl -HeaderName "Content-Security-Policy" -ExpectedPattern "default-src" -Severity "HIGH" -Description "Prevents XSS and code injection attacks"

# Test X-Content-Type-Options
Test-SecurityHeader -Url $BaseUrl -HeaderName "X-Content-Type-Options" -ExpectedPattern "nosniff" -Severity "MEDIUM" -Description "Prevents MIME type sniffing attacks"

# Test X-Frame-Options
Test-SecurityHeader -Url $BaseUrl -HeaderName "X-Frame-Options" -ExpectedPattern "(DENY|SAMEORIGIN)" -Severity "MEDIUM" -Description "Prevents clickjacking attacks"

# Test X-XSS-Protection (legacy)
Test-SecurityHeader -Url $BaseUrl -HeaderName "X-XSS-Protection" -ExpectedPattern "1; mode=block" -Severity "LOW" -Description "Legacy XSS protection for older browsers"

# Test Referrer-Policy
Test-SecurityHeader -Url $BaseUrl -HeaderName "Referrer-Policy" -ExpectedPattern "(no-referrer|strict-origin)" -Severity "MEDIUM" -Description "Controls referrer information disclosure"

# Test Permissions-Policy
Test-SecurityHeader -Url $BaseUrl -HeaderName "Permissions-Policy" -ExpectedPattern "camera=\(\)" -Severity "LOW" -Description "Restricts browser feature access"

# A02 Specific Tests
Test-A02HealthEndpointSecurity

Write-Host "`n=== ADDITIONAL SECURITY TESTS ===" -ForegroundColor Magenta

# Test for server information disclosure
Write-Host "Testing server information disclosure..."
try {
    $response = Invoke-WebRequest -Uri $BaseUrl -Method GET -UseBasicParsing -ErrorAction Stop
    $server = $response.Headers.Server
    if ($server) {
        if ($server -match "nginx/[\d\.]+") {
            Write-Host "FAIL: Server version disclosed: $server" -ForegroundColor Red
            $script:failed++
            $script:testResults += "FAIL: Server version disclosure"
            $script:criticalFindings += "MEDIUM: Server version information disclosed"
        } else {
            Write-Host "PASS: Server header present but version hidden" -ForegroundColor Green
            $script:passed++
            $script:testResults += "PASS: Server version hiding"
        }
    } else {
        Write-Host "PASS: Server header hidden" -ForegroundColor Green
        $script:passed++
        $script:testResults += "PASS: Server header hiding"
    }
}
catch {
    Write-Host "ERROR: Failed to test server disclosure - $($_.Exception.Message)" -ForegroundColor Red
}

# Test for X-Powered-By disclosure
Write-Host "Testing X-Powered-By header disclosure..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/health" -Method GET -UseBasicParsing -ErrorAction SilentlyContinue
    $poweredBy = $response.Headers["X-Powered-By"]
    if ($poweredBy) {
        Write-Host "FAIL: X-Powered-By header disclosed: $poweredBy" -ForegroundColor Red
        $script:failed++
        $script:testResults += "FAIL: X-Powered-By disclosure"
    } else {
        Write-Host "PASS: X-Powered-By header hidden" -ForegroundColor Green
        $script:passed++
        $script:testResults += "PASS: X-Powered-By hiding"
    }
}
catch {
    Write-Host "INFO: Could not test X-Powered-By (API may be restricted)" -ForegroundColor Gray
}

# Final Results Summary
Write-Host "`n=== SECURITY HEADERS VERIFICATION SUMMARY ===" -ForegroundColor Green
Write-Host "Total Tests: $($passed + $failed)" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

if ($criticalFindings.Count -gt 0) {
    Write-Host "`nCRITICAL FINDINGS:" -ForegroundColor Red
    foreach ($finding in $criticalFindings) {
        Write-Host "  - $finding" -ForegroundColor Yellow
    }
}

# Calculate security score
$totalTests = $passed + $failed
if ($totalTests -gt 0) {
    $securityScore = [math]::Round(($passed / $totalTests) * 100, 1)
    Write-Host "`nSecurity Score: $securityScore%" -ForegroundColor $(if ($securityScore -ge 80) { "Green" } elseif ($securityScore -ge 60) { "Yellow" } else { "Red" })
    
    if ($securityScore -ge 90) {
        Write-Host "EXCELLENT: Security headers implementation is outstanding" -ForegroundColor Green
    } elseif ($securityScore -ge 75) {
        Write-Host "GOOD: Security headers implementation is solid with minor improvements needed" -ForegroundColor Green
    } elseif ($securityScore -ge 60) {
        Write-Host "MODERATE: Security headers need significant improvements" -ForegroundColor Yellow
    } else {
        Write-Host "POOR: Security headers implementation requires immediate attention" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: No tests could be completed" -ForegroundColor Red
}

Write-Host "`nTEST RESULTS DETAILS:" -ForegroundColor Cyan
foreach ($result in $testResults) {
    $color = if ($result.StartsWith("PASS")) { "Green" } elseif ($result.StartsWith("FAIL")) { "Red" } elseif ($result.StartsWith("WARN")) { "Yellow" } else { "Gray" }
    Write-Host "  $result" -ForegroundColor $color
}

Write-Host "`n=== A02 CRYPTOGRAPHIC FAILURES VERIFICATION COMPLETE ===" -ForegroundColor Green

# Return exit code based on critical findings
if ($criticalFindings.Count -gt 0) {
    exit 1
} else {
    exit 0
} 