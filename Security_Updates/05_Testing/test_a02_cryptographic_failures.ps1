# A02:2021 Cryptographic Failures Security Testing
# Comprehensive testing of SSL/TLS configuration, data transmission security, 
# password storage analysis, and encryption implementation review

Write-Host "A02:2021 - CRYPTOGRAPHIC FAILURES SECURITY TESTING" -ForegroundColor Yellow
Write-Host "=========================================================" -ForegroundColor Yellow
Write-Host "Testing Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "Target: Meme Maker Production (memeit.pro)" -ForegroundColor Gray
Write-Host ""

# Configuration
$DOMAIN = "memeit.pro"
$API_BASE = "https://$DOMAIN/api"
$LOCAL_API = "http://localhost:8000"
$TEST_RESULTS = @{}
$PASSED_TESTS = 0
$FAILED_TESTS = 0
$TOTAL_TESTS = 0

# Logging function
function Write-TestResult {
    param(
        [string]$TestName,
        [string]$Status,
        [string]$Details = "",
        [string]$Severity = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $TEST_RESULTS[$TestName] = @{
        Status = $Status
        Details = $Details
        Severity = $Severity
        Timestamp = $timestamp
    }
    
    $color = switch ($Status) {
        "PASS" { "Green"; $script:PASSED_TESTS++ }
        "FAIL" { "Red"; $script:FAILED_TESTS++ }
        "WARN" { "Yellow" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    
    $script:TOTAL_TESTS++
    Write-Host "[$timestamp] [$Severity] $TestName : $Status" -ForegroundColor $color
    if ($Details) {
        Write-Host "    Details: $Details" -ForegroundColor Gray
    }
}

# Helper function to test SSL/TLS connection
function Test-SSLConnection {
    param(
        [string]$Hostname,
        [int]$Port = 443
    )
    
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($Hostname, $Port)
        
        $sslStream = New-Object System.Net.Security.SslStream($tcpClient.GetStream())
        $sslStream.AuthenticateAsClient($Hostname)
        
        $cert = $sslStream.RemoteCertificate
        $sslProtocol = $sslStream.SslProtocol
        $cipherAlgorithm = $sslStream.CipherAlgorithm
        $cipherStrength = $sslStream.CipherStrength
        $hashAlgorithm = $sslStream.HashAlgorithm
        $hashStrength = $sslStream.HashStrength
        $keyExchangeAlgorithm = $sslStream.KeyExchangeAlgorithm
        $keyExchangeStrength = $sslStream.KeyExchangeStrength
        
        $sslStream.Close()
        $tcpClient.Close()
        
        return @{
            Success = $true
            Certificate = $cert
            Protocol = $sslProtocol
            CipherAlgorithm = $cipherAlgorithm
            CipherStrength = $cipherStrength
            HashAlgorithm = $hashAlgorithm
            HashStrength = $hashStrength
            KeyExchangeAlgorithm = $keyExchangeAlgorithm
            KeyExchangeStrength = $keyExchangeStrength
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# Helper function to make HTTP requests
function Invoke-SafeWebRequest {
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$TimeoutSec = 30
    )
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            Headers = $Headers
            TimeoutSec = $TimeoutSec
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-WebRequest @params
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Headers = $response.Headers
            Content = $response.Content
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            StatusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode } else { $null }
        }
    }
}

Write-Host "Starting A02:2021 Cryptographic Failures Testing..." -ForegroundColor Yellow
Write-Host ""

# ===============================
# 1. SSL/TLS CONFIGURATION TESTING
# ===============================

Write-Host "1. SSL/TLS CONFIGURATION TESTING" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Test 1.1: SSL/TLS Certificate Validation
Write-Host "Testing SSL/TLS certificate validation..."
$sslTest = Test-SSLConnection -Hostname $DOMAIN

if ($sslTest.Success) {
    $cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]$sslTest.Certificate
    
    # Check certificate validity
    $now = Get-Date
    $certValid = ($cert.NotBefore -le $now) -and ($cert.NotAfter -gt $now)
    
    if ($certValid) {
        Write-TestResult "SSL Certificate Validity" "PASS" "Valid from $($cert.NotBefore) to $($cert.NotAfter)"
    } else {
        Write-TestResult "SSL Certificate Validity" "FAIL" "Certificate expired or not yet valid" "CRITICAL"
    }
    
    # Check certificate issuer (Let's Encrypt expected)
    if ($cert.Issuer -match "Let's Encrypt") {
        Write-TestResult "SSL Certificate Issuer" "PASS" "Let's Encrypt Authority: $($cert.Issuer)"
    } else {
        Write-TestResult "SSL Certificate Issuer" "WARN" "Non-Let's Encrypt issuer: $($cert.Issuer)"
    }
    
    # Check certificate subject
    if ($cert.Subject -match $DOMAIN) {
        Write-TestResult "SSL Certificate Subject" "PASS" "Correct domain in certificate: $($cert.Subject)"
    } else {
        Write-TestResult "SSL Certificate Subject" "FAIL" "Domain mismatch: $($cert.Subject)" "HIGH"
    }
    
} else {
    Write-TestResult "SSL Certificate Test" "FAIL" "Unable to establish SSL connection: $($sslTest.Error)" "CRITICAL"
}

# Test 1.2: TLS Protocol Version Testing
Write-Host "Testing TLS protocol versions..."
if ($sslTest.Success) {
    $protocol = $sslTest.Protocol.ToString()
    
    if ($protocol -match "Tls12|Tls13") {
        Write-TestResult "TLS Protocol Version" "PASS" "Using secure protocol: $protocol"
    } elseif ($protocol -match "Tls11") {
        Write-TestResult "TLS Protocol Version" "WARN" "Using TLS 1.1 (deprecated): $protocol"
    } else {
        Write-TestResult "TLS Protocol Version" "FAIL" "Using insecure protocol: $protocol" "HIGH"
    }
}

# Test 1.3: Cipher Suite Analysis
Write-Host "Testing cipher suite strength..."
if ($sslTest.Success) {
    $cipherStrength = $sslTest.CipherStrength
    $hashStrength = $sslTest.HashStrength
    $keyExchangeStrength = $sslTest.KeyExchangeStrength
    
    # Check cipher strength
    if ($cipherStrength -ge 256) {
        Write-TestResult "Cipher Strength" "PASS" "Strong encryption: $cipherStrength bits"
    } elseif ($cipherStrength -ge 128) {
        Write-TestResult "Cipher Strength" "WARN" "Moderate encryption: $cipherStrength bits"
    } else {
        Write-TestResult "Cipher Strength" "FAIL" "Weak encryption: $cipherStrength bits" "HIGH"
    }
    
    # Check hash algorithm strength
    if ($hashStrength -ge 256) {
        Write-TestResult "Hash Algorithm Strength" "PASS" "Strong hashing: $hashStrength bits"
    } elseif ($hashStrength -ge 160) {
        Write-TestResult "Hash Algorithm Strength" "WARN" "Moderate hashing: $hashStrength bits"
    } else {
        Write-TestResult "Hash Algorithm Strength" "FAIL" "Weak hashing: $hashStrength bits" "HIGH"
    }
    
    # Check key exchange strength
    if ($keyExchangeStrength -ge 2048) {
        Write-TestResult "Key Exchange Strength" "PASS" "Strong key exchange: $keyExchangeStrength bits"
    } elseif ($keyExchangeStrength -ge 1024) {
        Write-TestResult "Key Exchange Strength" "WARN" "Moderate key exchange: $keyExchangeStrength bits"
    } else {
        Write-TestResult "Key Exchange Strength" "FAIL" "Weak key exchange: $keyExchangeStrength bits" "HIGH"
    }
}

# Test 1.4: HTTP to HTTPS Redirect Testing
Write-Host "Testing HTTP to HTTPS redirect..."
$httpTest = Invoke-SafeWebRequest -Uri "http://$DOMAIN/"

if ($httpTest.Success -and $httpTest.StatusCode -eq 301) {
    $location = $httpTest.Headers.Location
    if ($location -and $location.StartsWith("https://")) {
        Write-TestResult "HTTP to HTTPS Redirect" "PASS" "Proper redirect to: $location"
    } else {
        Write-TestResult "HTTP to HTTPS Redirect" "FAIL" "Invalid redirect location: $location" "MEDIUM"
    }
} else {
    Write-TestResult "HTTP to HTTPS Redirect" "FAIL" "No proper redirect found (Status: $($httpTest.StatusCode))" "MEDIUM"
}

# Test 1.5: HSTS Header Testing
Write-Host "Testing HSTS (HTTP Strict Transport Security) headers..."
$httpsTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN/"

if ($httpsTest.Success) {
    $hstsHeader = $httpsTest.Headers['Strict-Transport-Security']
    
    if ($hstsHeader) {
        # Check HSTS configuration
        $maxAge = if ($hstsHeader -match "max-age=(\d+)") { [int]$matches[1] } else { 0 }
        $includeSubDomains = $hstsHeader -match "includeSubDomains"
        $preload = $hstsHeader -match "preload"
        
        if ($maxAge -ge 31536000) { # 1 year
            Write-TestResult "HSTS Max-Age" "PASS" "Long max-age: $maxAge seconds"
        } elseif ($maxAge -ge 86400) { # 1 day
            Write-TestResult "HSTS Max-Age" "WARN" "Short max-age: $maxAge seconds"
        } else {
            Write-TestResult "HSTS Max-Age" "FAIL" "Very short or missing max-age: $maxAge" "MEDIUM"
        }
        
        if ($includeSubDomains) {
            Write-TestResult "HSTS includeSubDomains" "PASS" "includeSubDomains directive present"
        } else {
            Write-TestResult "HSTS includeSubDomains" "WARN" "includeSubDomains directive missing"
        }
        
        if ($preload) {
            Write-TestResult "HSTS Preload" "PASS" "Preload directive present"
        } else {
            Write-TestResult "HSTS Preload" "INFO" "Preload directive not set (optional)"
        }
        
    } else {
        Write-TestResult "HSTS Header" "FAIL" "HSTS header missing" "MEDIUM"
    }
}

Write-Host ""

# ===============================
# 2. SENSITIVE DATA TRANSMISSION
# ===============================

Write-Host "2. SENSITIVE DATA TRANSMISSION TESTING" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Test 2.1: API Endpoint HTTPS Enforcement
Write-Host "Testing API endpoint HTTPS enforcement..."

$apiEndpoints = @(
    "/health",
    "/api/v1/metadata",
    "/api/v1/jobs"
)

foreach ($endpoint in $apiEndpoints) {
    # Test HTTP access (should be blocked/redirected)
    $httpApiTest = Invoke-SafeWebRequest -Uri "http://$DOMAIN$endpoint"
    
    if ($httpApiTest.StatusCode -eq 301 -or $httpApiTest.StatusCode -eq 302) {
        Write-TestResult "API HTTPS Enforcement: $endpoint" "PASS" "HTTP properly redirected to HTTPS"
    } elseif ($httpApiTest.StatusCode -eq 404 -or !$httpApiTest.Success) {
        Write-TestResult "API HTTPS Enforcement: $endpoint" "PASS" "HTTP access blocked"
    } else {
        Write-TestResult "API HTTPS Enforcement: $endpoint" "FAIL" "HTTP access allowed (Status: $($httpApiTest.StatusCode))" "HIGH"
    }
    
    # Test HTTPS access (should work)
    $httpsApiTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN$endpoint"
    
    if ($httpsApiTest.Success) {
        Write-TestResult "API HTTPS Access: $endpoint" "PASS" "HTTPS access working (Status: $($httpsApiTest.StatusCode))"
    } else {
        Write-TestResult "API HTTPS Access: $endpoint" "FAIL" "HTTPS access failed: $($httpsApiTest.Error)" "MEDIUM"
    }
}

# Test 2.2: Cookie Security Attributes
Write-Host "Testing cookie security attributes..."
if ($httpsTest.Success) {
    $setCookieHeaders = $httpsTest.Headers['Set-Cookie']
    
    if ($setCookieHeaders) {
        foreach ($cookie in $setCookieHeaders) {
            $cookieName = ($cookie -split '=')[0]
            
            $isSecure = $cookie -match "Secure"
            $isHttpOnly = $cookie -match "HttpOnly"
            $sameSite = $cookie -match "SameSite=(?:Strict|Lax)"
            
            if ($isSecure) {
                Write-TestResult "Cookie Secure Flag: $cookieName" "PASS" "Secure flag present"
            } else {
                Write-TestResult "Cookie Secure Flag: $cookieName" "FAIL" "Secure flag missing" "MEDIUM"
            }
            
            if ($isHttpOnly) {
                Write-TestResult "Cookie HttpOnly Flag: $cookieName" "PASS" "HttpOnly flag present"
            } else {
                Write-TestResult "Cookie HttpOnly Flag: $cookieName" "WARN" "HttpOnly flag missing"
            }
            
            if ($sameSite) {
                Write-TestResult "Cookie SameSite Attribute: $cookieName" "PASS" "SameSite attribute present"
            } else {
                Write-TestResult "Cookie SameSite Attribute: $cookieName" "WARN" "SameSite attribute missing"
            }
        }
    } else {
        Write-TestResult "Cookie Analysis" "INFO" "No cookies set by the application"
    }
}

# Test 2.3: Content Security Policy (CSP)
Write-Host "Testing Content Security Policy headers..."
if ($httpsTest.Success) {
    $cspHeader = $httpsTest.Headers['Content-Security-Policy']
    
    if ($cspHeader) {
        # Check for critical CSP directives
        $defaultSrc = $cspHeader -match "default-src"
        $scriptSrc = $cspHeader -match "script-src"
        $styleSrc = $cspHeader -match "style-src"
        $imgSrc = $cspHeader -match "img-src"
        $connectSrc = $cspHeader -match "connect-src"
        
        if ($defaultSrc) {
            Write-TestResult "CSP default-src" "PASS" "default-src directive present"
        } else {
            Write-TestResult "CSP default-src" "WARN" "default-src directive missing"
        }
        
        # Check for unsafe directives
        $unsafeInline = $cspHeader -match "'unsafe-inline'"
        $unsafeEval = $cspHeader -match "'unsafe-eval'"
        
        if ($unsafeInline) {
            Write-TestResult "CSP Unsafe Inline" "WARN" "unsafe-inline directive found"
        } else {
            Write-TestResult "CSP Unsafe Inline" "PASS" "No unsafe-inline directive"
        }
        
        if ($unsafeEval) {
            Write-TestResult "CSP Unsafe Eval" "FAIL" "unsafe-eval directive found" "MEDIUM"
        } else {
            Write-TestResult "CSP Unsafe Eval" "PASS" "No unsafe-eval directive"
        }
        
    } else {
        Write-TestResult "Content Security Policy" "WARN" "CSP header missing"
    }
}

Write-Host ""

# ===============================
# 3. PASSWORD STORAGE ANALYSIS
# ===============================

Write-Host "3. PASSWORD STORAGE ANALYSIS" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Test 3.1: Authentication Mechanism Analysis
Write-Host "Analyzing authentication mechanisms..."

# Check if the application has user authentication
$loginEndpoints = @("/login", "/auth", "/signin", "/api/auth", "/api/login")
$hasAuthentication = $false

foreach ($endpoint in $loginEndpoints) {
    $authTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN$endpoint"
    if ($authTest.Success -and $authTest.StatusCode -ne 404) {
        $hasAuthentication = $true
        Write-TestResult "Authentication Endpoint Found" "INFO" "Endpoint: $endpoint (Status: $($authTest.StatusCode))"
    }
}

if (-not $hasAuthentication) {
    Write-TestResult "User Authentication System" "INFO" "No user authentication endpoints found - appears to be anonymous service"
    Write-TestResult "Password Storage Risk" "PASS" "No password storage as no user authentication system"
} else {
    Write-TestResult "Authentication System Detected" "WARN" "Authentication endpoints found - password security review needed"
}

# Test 3.2: Admin Authentication Analysis
Write-Host "Testing admin authentication security..."

$adminEndpoints = @(
    "/api/v1/admin/cache/stats",
    "/api/v1/admin/cache/clear",
    "/api/v1/admin/storage/info"
)

foreach ($endpoint in $adminEndpoints) {
    # Test unauthenticated access
    $unauthTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN$endpoint"
    
    if ($unauthTest.StatusCode -eq 401) {
        Write-TestResult "Admin Auth Protection: $endpoint" "PASS" "Properly protected with 401 Unauthorized"
    } elseif ($unauthTest.StatusCode -eq 403) {
        Write-TestResult "Admin Auth Protection: $endpoint" "PASS" "Properly protected with 403 Forbidden"
    } elseif ($unauthTest.StatusCode -eq 404) {
        Write-TestResult "Admin Endpoint: $endpoint" "INFO" "Endpoint not found (may be disabled)"
    } else {
        Write-TestResult "Admin Auth Protection: $endpoint" "FAIL" "Admin endpoint accessible without authentication" "CRITICAL"
    }
}

# Test 3.3: Session Token Security
Write-Host "Testing session token security..."

# Test for JWT tokens in responses
$jwtPattern = "eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*"

foreach ($endpoint in $apiEndpoints) {
    $tokenTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN$endpoint"
    
    if ($tokenTest.Success -and $tokenTest.Content -match $jwtPattern) {
        $foundToken = $matches[0]
        Write-TestResult "JWT Token Exposure: $endpoint" "WARN" "JWT token found in response (length: $($foundToken.Length))"
        
        # Basic JWT validation
        try {
            $parts = $foundToken.Split('.')
            if ($parts.Length -eq 3) {
                Write-TestResult "JWT Structure: $endpoint" "PASS" "Valid JWT structure (3 parts)"
            } else {
                Write-TestResult "JWT Structure: $endpoint" "FAIL" "Invalid JWT structure" "MEDIUM"
            }
        } catch {
            Write-TestResult "JWT Analysis: $endpoint" "FAIL" "Error analyzing JWT: $($_.Exception.Message)" "MEDIUM"
        }
    }
}

Write-Host ""

# ===============================
# 4. ENCRYPTION IMPLEMENTATION REVIEW
# ===============================

Write-Host "4. ENCRYPTION IMPLEMENTATION REVIEW" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Test 4.1: File Storage Encryption
Write-Host "Analyzing file storage security..."

# Test file download endpoint for encryption headers
$fileEndpoints = @("/api/v1/jobs/test", "/downloads/", "/clips/")

foreach ($endpoint in $fileEndpoints) {
    $fileTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN$endpoint"
    
    if ($fileTest.Success) {
        $contentEncoding = $fileTest.Headers['Content-Encoding']
        $cacheControl = $fileTest.Headers['Cache-Control']
        
        if ($contentEncoding) {
            Write-TestResult "File Content Encoding: $endpoint" "INFO" "Content encoding: $contentEncoding"
        }
        
        if ($cacheControl -and $cacheControl -match "no-store|private") {
            Write-TestResult "File Cache Security: $endpoint" "PASS" "Secure cache control: $cacheControl"
        } elseif ($cacheControl) {
            Write-TestResult "File Cache Security: $endpoint" "WARN" "Cache control present but may cache sensitive data: $cacheControl"
        } else {
            Write-TestResult "File Cache Security: $endpoint" "WARN" "No cache control headers"
        }
    }
}

# Test 4.2: Database Connection Security
Write-Host "Testing database connection security..."

# Redis connection test (should not be directly accessible)
try {
    $redisTest = Test-NetConnection -ComputerName $DOMAIN -Port 6379 -WarningAction SilentlyContinue
    
    if ($redisTest.TcpTestSucceeded) {
        Write-TestResult "Redis Port Exposure" "FAIL" "Redis port 6379 is accessible from external network" "CRITICAL"
    } else {
        Write-TestResult "Redis Port Security" "PASS" "Redis port 6379 is not accessible externally"
    }
} catch {
    Write-TestResult "Redis Port Security" "PASS" "Redis port 6379 is not accessible externally"
}

# Test 4.3: Environment Variable Security
Write-Host "Testing for exposed environment variables..."

$envTestEndpoints = @(
    "/api/env",
    "/api/config",
    "/debug",
    "/status",
    "/.env",
    "/config.json"
)

foreach ($endpoint in $envTestEndpoints) {
    $envTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN$endpoint"
    
    if ($envTest.Success -and $envTest.StatusCode -eq 200) {
        # Check for sensitive data patterns
        $sensitivePatterns = @(
            "password",
            "secret",
            "key",
            "token",
            "redis",
            "database",
            "db_",
            "api_key"
        )
        
        $foundSensitive = $false
        foreach ($pattern in $sensitivePatterns) {
            if ($envTest.Content -match $pattern) {
                $foundSensitive = $true
                break
            }
        }
        
        if ($foundSensitive) {
            Write-TestResult "Environment Exposure: $endpoint" "FAIL" "Sensitive configuration data exposed" "CRITICAL"
        } else {
            Write-TestResult "Config Endpoint: $endpoint" "WARN" "Configuration endpoint accessible but no sensitive data detected"
        }
    }
}

# Test 4.4: API Key Security
Write-Host "Testing API key security implementation..."

# Test API endpoints with common API key patterns
$apiKeyHeaders = @{
    "X-API-Key" = "test123"
    "Authorization" = "Bearer test123"
    "API-Key" = "test123"
}

foreach ($header in $apiKeyHeaders.GetEnumerator()) {
    $headers = @{ $header.Key = $header.Value }
    $apiKeyTest = Invoke-SafeWebRequest -Uri "https://$DOMAIN/api/v1/metadata" -Headers $headers -Method "POST"
    
    if ($apiKeyTest.StatusCode -eq 401 -or $apiKeyTest.StatusCode -eq 403) {
        Write-TestResult "API Key Validation: $($header.Key)" "PASS" "Invalid API key properly rejected"
    } elseif ($apiKeyTest.Success) {
        Write-TestResult "API Key Security: $($header.Key)" "WARN" "Endpoint accepts unknown API key header"
    }
}

Write-Host ""

# ===============================
# SUMMARY AND REPORTING
# ===============================

Write-Host "TEST SUMMARY AND RESULTS" -ForegroundColor Yellow
Write-Host "=========================" -ForegroundColor Yellow

Write-Host "Total Tests Executed: $TOTAL_TESTS" -ForegroundColor White
Write-Host "Tests Passed: $PASSED_TESTS" -ForegroundColor Green
Write-Host "Tests Failed: $FAILED_TESTS" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round(($PASSED_TESTS / $TOTAL_TESTS) * 100, 2))%" -ForegroundColor Cyan

Write-Host ""
Write-Host "DETAILED FINDINGS BY SEVERITY:" -ForegroundColor Yellow

# Critical findings
$criticalFindings = $TEST_RESULTS.GetEnumerator() | Where-Object { $_.Value.Severity -eq "CRITICAL" -and $_.Value.Status -eq "FAIL" }
if ($criticalFindings.Count -gt 0) {
    Write-Host ""
    Write-Host "CRITICAL ISSUES (Fix Immediately):" -ForegroundColor Red
    foreach ($finding in $criticalFindings) {
        Write-Host "  - $($finding.Key): $($finding.Value.Details)" -ForegroundColor Red
    }
}

# High findings
$highFindings = $TEST_RESULTS.GetEnumerator() | Where-Object { $_.Value.Severity -eq "HIGH" -and $_.Value.Status -eq "FAIL" }
if ($highFindings.Count -gt 0) {
    Write-Host ""
    Write-Host "HIGH PRIORITY ISSUES (Fix This Week):" -ForegroundColor Magenta
    foreach ($finding in $highFindings) {
        Write-Host "  - $($finding.Key): $($finding.Value.Details)" -ForegroundColor Magenta
    }
}

# Medium findings
$mediumFindings = $TEST_RESULTS.GetEnumerator() | Where-Object { $_.Value.Severity -eq "MEDIUM" -and $_.Value.Status -eq "FAIL" }
if ($mediumFindings.Count -gt 0) {
    Write-Host ""
    Write-Host "MEDIUM PRIORITY ISSUES (Fix This Month):" -ForegroundColor Yellow
    foreach ($finding in $mediumFindings) {
        Write-Host "  - $($finding.Key): $($finding.Value.Details)" -ForegroundColor Yellow
    }
}

# Warnings
$warnings = $TEST_RESULTS.GetEnumerator() | Where-Object { $_.Value.Status -eq "WARN" }
if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "WARNINGS (Consider Addressing):" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  - $($warning.Key): $($warning.Value.Details)" -ForegroundColor Yellow
    }
}

# Generate JSON report
$report = @{
    TestDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    TestType = "A02:2021 - Cryptographic Failures"
    Target = $DOMAIN
    Summary = @{
        TotalTests = $TOTAL_TESTS
        PassedTests = $PASSED_TESTS
        FailedTests = $FAILED_TESTS
        SuccessRate = [math]::Round(($PASSED_TESTS / $TOTAL_TESTS) * 100, 2)
    }
    Results = $TEST_RESULTS
    CriticalIssues = $criticalFindings.Count
    HighPriorityIssues = $highFindings.Count
    MediumPriorityIssues = $mediumFindings.Count
    Warnings = $warnings.Count
}

$reportPath = "Security_Updates/05_Testing/a02_cryptographic_failures_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host ""
Write-Host "A02:2021 CRYPTOGRAPHIC FAILURES TESTING COMPLETE" -ForegroundColor Green
Write-Host "Detailed report saved to: $reportPath" -ForegroundColor Cyan
Write-Host ""

# Set exit code based on critical/high issues
if ($criticalFindings.Count -gt 0) {
    Write-Host "CRITICAL ISSUES FOUND - Immediate action required!" -ForegroundColor Red
    exit 2
} elseif ($highFindings.Count -gt 0) {
    Write-Host "HIGH PRIORITY ISSUES FOUND - Action required this week!" -ForegroundColor Magenta  
    exit 1
} else {
    Write-Host "No critical or high priority cryptographic issues found." -ForegroundColor Green
    exit 0
} 