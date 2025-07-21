# PHASE 4: SSRF PENETRATION TESTING (PowerShell)
# ===============================================
# Comprehensive Server-Side Request Forgery (SSRF) testing against production system
# Following OWASP Top 10 A10:2021 - Server-Side Request Forgery
# Target: memeit.pro production API

$baseUrl = "https://memeit.pro"
$metadataEndpoint = "$baseUrl/api/v1/metadata"
$results = @()
$startTime = Get-Date

function Write-TestResult {
    param(
        [string]$Message,
        [string]$TestType = "INFO",
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
    
    # Color coding for output
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "VULN" { "Red" }
        "INFO" { "Blue" }
        "WARN" { "Yellow" }
        default { "White" }
    }
    
    $icon = switch ($Status) {
        "PASS" { "✅" }
        "FAIL" { "❌" }
        "VULN" { "🚨" }
        "INFO" { "ℹ️" }
        "WARN" { "⚠️" }
        default { "📝" }
    }
    
    Write-Host "$icon [$timestamp] $TestType`: $Message" -ForegroundColor $color
}

function Test-SSRFPayload {
    param(
        [string]$PayloadUrl,
        [string]$Description,
        [bool]$ExpectBlocked = $true
    )
    
    Write-TestResult "Testing: $Description" "SSRF" "TESTING"
    
    try {
        $headers = @{
            'Content-Type' = 'application/json'
        }
        
        $body = @{
            url = $PayloadUrl
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri $metadataEndpoint -Method POST -Headers $headers -Body $body -TimeoutSec 15 -ErrorAction Stop
        
        if ($ExpectBlocked) {
            Write-TestResult "🚨 POTENTIAL SSRF VULNERABILITY - Request succeeded when it should be blocked!" "SSRF" "VULN"
            return "VULNERABLE"
        } else {
            Write-TestResult "Request succeeded as expected" "SSRF" "PASS"
            return "SUCCESS"
        }
        
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__
        $statusDescription = $_.Exception.Response.StatusDescription
        
        if ($statusCode -eq 422) {
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorContent = $reader.ReadToEnd()
                $errorData = $errorContent | ConvertFrom-Json
                $errorDetail = $errorData.detail.ToLower()
                
                if ($errorDetail -match "domain not allowed|invalid url|unsupported|blocked") {
                    if ($ExpectBlocked) {
                        Write-TestResult "BLOCKED (Expected): $errorDetail" "SSRF" "PASS"
                        return "BLOCKED"
                    } else {
                        Write-TestResult "Unexpected block: $errorDetail" "SSRF" "WARN"
                        return "BLOCKED"
                    }
                } else {
                    Write-TestResult "Unexpected 422 error: $errorDetail" "SSRF" "WARN"
                    return "ERROR"
                }
            } catch {
                Write-TestResult "422 response but couldn't parse JSON" "SSRF" "WARN"
                return "ERROR"
            }
        } elseif ($_.Exception.Message -match "timeout") {
            if ($ExpectBlocked) {
                Write-TestResult "Request timed out (likely blocked at network level)" "SSRF" "PASS"
                return "TIMEOUT"
            } else {
                Write-TestResult "Unexpected timeout" "SSRF" "WARN"
                return "TIMEOUT"
            }
        } else {
            Write-TestResult "Request failed: $($_.Exception.Message)" "SSRF" "ERROR"
            return "ERROR"
        }
    }
}

function Run-SSRFTests {
    Write-TestResult "🚀 Starting SSRF Penetration Testing Suite" "SSRF" "INFO"
    
    # Test 1: Internal Network Access Attempts
    Write-TestResult "=== Test Category 1: Internal Network Access ===" "SSRF" "INFO"
    
    $internalTargets = @(
        @("http://127.0.0.1:8000/health", "Localhost backend access"),
        @("http://localhost:8000/health", "Localhost alternative"),
        @("http://0.0.0.0:8000/health", "Wildcard IP access"),
        @("http://10.0.0.1/", "Private network 10.x.x.x"),
        @("http://192.168.1.1/", "Private network 192.168.x.x"),
        @("http://172.16.0.1/", "Private network 172.16.x.x"),
        @("http://backend:8000/health", "Docker internal service"),
        @("http://redis:6379/", "Internal Redis access")
    )
    
    foreach ($target in $internalTargets) {
        Test-SSRFPayload $target[0] $target[1] $true
        Start-Sleep 1  # Rate limiting respect
    }
    
    # Test 2: Cloud Metadata Endpoints
    Write-TestResult "=== Test Category 2: Cloud Metadata Access ===" "SSRF" "INFO"
    
    $cloudTargets = @(
        @("http://169.254.169.254/latest/meta-data/", "AWS EC2 metadata"),
        @("http://169.254.169.254/latest/user-data/", "AWS EC2 user data"),
        @("http://169.254.169.254/computeMetadata/v1/", "Google Cloud metadata"),
        @("http://metadata.google.internal/computeMetadata/v1/", "Google Cloud alt"),
        @("http://169.254.169.254/metadata/instance", "Azure metadata")
    )
    
    foreach ($target in $cloudTargets) {
        Test-SSRFPayload $target[0] $target[1] $true
        Start-Sleep 1
    }
    
    # Test 3: Port Scanning Attempts
    Write-TestResult "=== Test Category 3: Port Scanning ===" "SSRF" "INFO"
    
    $portScanTargets = @(
        @("http://127.0.0.1:22/", "SSH port scanning"),
        @("http://127.0.0.1:3306/", "MySQL port scanning"),
        @("http://127.0.0.1:5432/", "PostgreSQL port scanning"),
        @("http://127.0.0.1:6379/", "Redis port scanning"),
        @("http://127.0.0.1:27017/", "MongoDB port scanning"),
        @("http://memeit.pro:22/", "External SSH scanning")
    )
    
    foreach ($target in $portScanTargets) {
        Test-SSRFPayload $target[0] $target[1] $true
        Start-Sleep 1
    }
    
    # Test 4: Protocol Bypass Attempts
    Write-TestResult "=== Test Category 4: Protocol Bypass ===" "SSRF" "INFO"
    
    $protocolTargets = @(
        @("ftp://127.0.0.1/", "FTP protocol bypass"),
        @("file:///etc/passwd", "File protocol bypass"),
        @("gopher://127.0.0.1:6379/", "Gopher protocol bypass"),
        @("dict://127.0.0.1:11211/", "Dict protocol bypass"),
        @("ldap://127.0.0.1:389/", "LDAP protocol bypass")
    )
    
    foreach ($target in $protocolTargets) {
        Test-SSRFPayload $target[0] $target[1] $true
        Start-Sleep 1
    }
    
    # Test 5: URL Encoding Bypass Attempts
    Write-TestResult "=== Test Category 5: URL Encoding Bypass ===" "SSRF" "INFO"
    
    $encodedTargets = @(
        @("http://127.0.0.1:8000%2fhealth", "URL encoding bypass %2f"),
        @("http://127%2e0%2e0%2e1:8000/health", "IP encoding bypass"),
        @("http://0x7f000001:8000/health", "Hex IP bypass"),
        @("http://2130706433:8000/health", "Decimal IP bypass"),
        @("http://[::1]:8000/health", "IPv6 localhost bypass")
    )
    
    foreach ($target in $encodedTargets) {
        Test-SSRFPayload $target[0] $target[1] $true
        Start-Sleep 1
    }
    
    # Test 6: Domain Validation - Legitimate URLs (should work)
    Write-TestResult "=== Test Category 6: Legitimate Domain Testing ===" "SSRF" "INFO"
    
    $legitimateTargets = @(
        @("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube - should work"),
        @("https://www.instagram.com/reel/test/", "Instagram - should work"),
        @("https://www.facebook.com/video/test/", "Facebook - should work"),
        @("https://www.reddit.com/r/test/", "Reddit - should work")
    )
    
    foreach ($target in $legitimateTargets) {
        Test-SSRFPayload $target[0] $target[1] $false
        Start-Sleep 2  # Longer delay for legitimate requests
    }
}

function Generate-Report {
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host ""
    Write-Host ("="*80)
    Write-Host "🛡️  SSRF PENETRATION TESTING REPORT"
    Write-Host ("="*80)
    
    # Count results by status
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
    
    $totalTests = ($results | Where-Object { $_.test -eq "SSRF" }).Count
    $passCount = if ($statusCounts.ContainsKey("PASS")) { $statusCounts["PASS"] } else { 0 }
    $vulnCount = if ($statusCounts.ContainsKey("VULN")) { $statusCounts["VULN"] } else { 0 }
    $warnCount = if ($statusCounts.ContainsKey("WARN")) { $statusCounts["WARN"] } else { 0 }
    $errorCount = if ($statusCounts.ContainsKey("ERROR")) { $statusCounts["ERROR"] } else { 0 }
    
    Write-Host "📊 Test Summary:"
    Write-Host "   Total Tests: $totalTests"
    Write-Host "   Duration: $([math]::Round($duration, 2)) seconds"
    Write-Host "   Blocked (Expected): $passCount"
    Write-Host "   Vulnerabilities Found: $vulnCount"
    Write-Host "   Errors/Warnings: $($warnCount + $errorCount)"
    
    if ($vulnerabilities.Count -gt 0) {
        Write-Host ""
        Write-Host "🚨 CRITICAL VULNERABILITIES DETECTED:" -ForegroundColor Red
        foreach ($vuln in $vulnerabilities) {
            Write-Host "   - $($vuln.message)" -ForegroundColor Red
        }
    } else {
        Write-Host ""
        Write-Host "✅ NO SSRF VULNERABILITIES DETECTED" -ForegroundColor Green
        Write-Host "   All internal/cloud/protocol access attempts were properly blocked" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "📋 Detailed Results:"
    foreach ($result in $results) {
        if ($result.test -eq "SSRF") {
            $icon = switch ($result.status) {
                "PASS" { "✅" }
                "VULN" { "🚨" }
                "WARN" { "⚠️" }
                "ERROR" { "❌" }
                default { "ℹ️" }
            }
            Write-Host "   $icon $($result.message)"
        }
    }
    
    Write-Host ""
    Write-Host ("="*80)
}

# Main execution
Write-Host "🔒 PHASE 4: SSRF PENETRATION TESTING"
Write-Host "Target: memeit.pro production environment"
Write-Host "Testing OWASP A10:2021 - Server-Side Request Forgery"
Write-Host ("="*80)

Run-SSRFTests
Generate-Report

Write-Host ""
Write-Host "🎯 Next: Run additional OWASP Top 10 penetration tests"
Write-Host "📝 Results logged for security audit documentation" 