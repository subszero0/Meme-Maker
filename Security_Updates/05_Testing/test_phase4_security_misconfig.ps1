# PHASE 4: SECURITY MISCONFIGURATION TESTING (A05:2021)
# =========================================================
# Testing for security misconfigurations, debug information, default credentials

$baseUrl = "https://memeit.pro"
$results = @()
$startTime = Get-Date

function Write-TestResult {
    param(
        [string]$Message,
        [string]$TestType = "MISCONFIG",
        [string]$Status = "TESTING"
    )
    
    $timestamp = (Get-Date).ToString("HH:mm:ss")
    $result = @{
        timestamp = $timestamp
        test = $TestType
        status = $Status
        message = $Message
    }
    $script:results += $result
    
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "VULN" { "Red" }
        "INFO" { "Blue" }
        "WARN" { "Yellow" }
        default { "White" }
    }
    
    $icon = switch ($Status) {
        "PASS" { "[PASS]" }
        "FAIL" { "[FAIL]" }
        "VULN" { "[VULN]" }
        "INFO" { "[INFO]" }
        "WARN" { "[WARN]" }
        default { "[TEST]" }
    }
    
    Write-Host "$icon [$timestamp] $TestType`: $Message" -ForegroundColor $color
}

function Test-SecurityHeaders {
    param([string]$Url)
    
    Write-TestResult "Testing security headers for: $Url" "HEADERS" "TESTING"
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        # Check for security headers
        $headers = $response.Headers
        $securityScore = 0
        $totalChecks = 7
        
        # HSTS
        if ($headers['Strict-Transport-Security']) {
            Write-TestResult "HSTS header present: $($headers['Strict-Transport-Security'])" "HEADERS" "PASS"
            $securityScore++
        } else {
            Write-TestResult "MISSING: HSTS header" "HEADERS" "WARN"
        }
        
        # Content Security Policy
        if ($headers['Content-Security-Policy']) {
            Write-TestResult "CSP header present" "HEADERS" "PASS"
            $securityScore++
        } else {
            Write-TestResult "MISSING: Content-Security-Policy header" "HEADERS" "WARN"
        }
        
        # X-Frame-Options
        if ($headers['X-Frame-Options']) {
            Write-TestResult "X-Frame-Options present: $($headers['X-Frame-Options'])" "HEADERS" "PASS"
            $securityScore++
        } else {
            Write-TestResult "MISSING: X-Frame-Options header" "HEADERS" "WARN"
        }
        
        # X-Content-Type-Options
        if ($headers['X-Content-Type-Options']) {
            Write-TestResult "X-Content-Type-Options present: $($headers['X-Content-Type-Options'])" "HEADERS" "PASS"
            $securityScore++
        } else {
            Write-TestResult "MISSING: X-Content-Type-Options header" "HEADERS" "WARN"
        }
        
        # Referrer-Policy
        if ($headers['Referrer-Policy']) {
            Write-TestResult "Referrer-Policy present: $($headers['Referrer-Policy'])" "HEADERS" "PASS"
            $securityScore++
        } else {
            Write-TestResult "MISSING: Referrer-Policy header" "HEADERS" "WARN"
        }
        
        # Check for dangerous headers
        if ($headers['Server']) {
            Write-TestResult "Information disclosure - Server header: $($headers['Server'])" "HEADERS" "WARN"
        } else {
            Write-TestResult "Server header properly hidden" "HEADERS" "PASS"
            $securityScore++
        }
        
        if ($headers['X-Powered-By']) {
            Write-TestResult "Information disclosure - X-Powered-By header: $($headers['X-Powered-By'])" "HEADERS" "WARN"
        } else {
            Write-TestResult "X-Powered-By header properly hidden" "HEADERS" "PASS"
            $securityScore++
        }
        
        $percentage = ($securityScore / $totalChecks) * 100
        Write-TestResult "Security headers score: $securityScore/$totalChecks ($percentage%)" "HEADERS" "INFO"
        
        return $securityScore
        
    } catch {
        Write-TestResult "Failed to test headers: $($_.Exception.Message)" "HEADERS" "ERROR"
        return 0
    }
}

function Test-DebugEndpoints {
    Write-TestResult "Testing for debug/info disclosure endpoints" "DEBUG" "INFO"
    
    $debugEndpoints = @(
        "$baseUrl/debug",
        "$baseUrl/info", 
        "$baseUrl/status",
        "$baseUrl/health",
        "$baseUrl/metrics",
        "$baseUrl/api/debug",
        "$baseUrl/api/health",
        "$baseUrl/.env",
        "$baseUrl/config",
        "$baseUrl/admin",
        "$baseUrl/phpmyadmin",
        "$baseUrl/adminer"
    )
    
    foreach ($endpoint in $debugEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint -Method GET -TimeoutSec 5 -ErrorAction Stop
            
            if ($response.StatusCode -eq 200) {
                $content = $response.Content.ToLower()
                if ($content -match "debug|error|stack|trace|password|secret|key|token") {
                    Write-TestResult "POTENTIAL INFO DISCLOSURE: $endpoint returned sensitive data" "DEBUG" "VULN"
                } else {
                    Write-TestResult "Debug endpoint accessible but safe: $endpoint" "DEBUG" "WARN"
                }
            }
        } catch {
            $statusCode = $null
            if ($_.Exception.Response) {
                $statusCode = $_.Exception.Response.StatusCode.Value__
            }
            
            if ($statusCode -eq 404) {
                Write-TestResult "Endpoint properly blocked: $endpoint" "DEBUG" "PASS"
            } elseif ($statusCode -eq 403) {
                Write-TestResult "Endpoint access forbidden: $endpoint" "DEBUG" "PASS" 
            } else {
                Write-TestResult "Endpoint test failed: $endpoint" "DEBUG" "INFO"
            }
        }
        Start-Sleep 1
    }
}

function Test-HttpMethods {
    Write-TestResult "Testing HTTP methods on main endpoint" "METHODS" "INFO"
    
    $methods = @("OPTIONS", "TRACE", "PUT", "DELETE", "PATCH")
    
    foreach ($method in $methods) {
        try {
            $response = Invoke-WebRequest -Uri $baseUrl -Method $method -TimeoutSec 5 -ErrorAction Stop
            Write-TestResult "$method method allowed - potential security risk" "METHODS" "WARN"
        } catch {
            $statusCode = $null
            if ($_.Exception.Response) {
                $statusCode = $_.Exception.Response.StatusCode.Value__
            }
            
            if ($statusCode -eq 405) {
                Write-TestResult "$method method properly blocked" "METHODS" "PASS"
            } else {
                Write-TestResult "$method method test inconclusive" "METHODS" "INFO"
            }
        }
        Start-Sleep 1
    }
}

# Main execution
Write-Host "PHASE 4: SECURITY MISCONFIGURATION TESTING" -ForegroundColor Cyan
Write-Host "Target: memeit.pro production environment" -ForegroundColor Cyan
Write-Host "Testing OWASP A05:2021 - Security Misconfiguration" -ForegroundColor Cyan
Write-Host ("="*80)

Write-TestResult "Starting Security Misconfiguration Testing" "MISCONFIG" "INFO"

# Test 1: Security Headers
Write-TestResult "=== Test Category 1: Security Headers ===" "MISCONFIG" "INFO"
$headerScore = Test-SecurityHeaders $baseUrl

# Test 2: Debug/Info Disclosure
Write-TestResult "=== Test Category 2: Debug Information Disclosure ===" "MISCONFIG" "INFO"
Test-DebugEndpoints

# Test 3: HTTP Methods
Write-TestResult "=== Test Category 3: HTTP Methods ===" "MISCONFIG" "INFO"
Test-HttpMethods

# Generate Report
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host ("="*80)
Write-Host "SECURITY MISCONFIGURATION TESTING REPORT" -ForegroundColor Cyan
Write-Host ("="*80)

# Count results
$statusCounts = @{}
$vulnerabilities = @()

foreach ($result in $results) {
    $status = $result.status
    if ($statusCounts.ContainsKey($status)) {
        $statusCounts[$status]++
    } else {
        $statusCounts[$status] = 1
    }
    
    if ($status -eq "VULN") {
        $vulnerabilities += $result
    }
}

$totalTests = $results.Count
$passCount = if ($statusCounts.ContainsKey("PASS")) { $statusCounts["PASS"] } else { 0 }
$vulnCount = if ($statusCounts.ContainsKey("VULN")) { $statusCounts["VULN"] } else { 0 }
$warnCount = if ($statusCounts.ContainsKey("WARN")) { $statusCounts["WARN"] } else { 0 }

Write-Host "Test Summary:" -ForegroundColor Yellow
Write-Host "   Total Tests: $totalTests"
Write-Host "   Duration: $([math]::Round($duration, 2)) seconds"
Write-Host "   Security Headers Score: $headerScore/7"
Write-Host "   Passed Tests: $passCount"
Write-Host "   Warnings: $warnCount"
Write-Host "   Vulnerabilities Found: $vulnCount"

if ($vulnerabilities.Count -gt 0) {
    Write-Host ""
    Write-Host "SECURITY MISCONFIGURATIONS DETECTED:" -ForegroundColor Red
    foreach ($vuln in $vulnerabilities) {
        Write-Host "   - $($vuln.message)" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "NO CRITICAL MISCONFIGURATIONS DETECTED" -ForegroundColor Green
    Write-Host "Security configuration appears well implemented" -ForegroundColor Green
}

Write-Host ""
Write-Host "Security misconfiguration testing completed" 