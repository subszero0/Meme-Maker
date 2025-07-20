# PHASE 4: A01 BROKEN ACCESS CONTROL PENETRATION TESTING (PowerShell)
# ===================================================================
# Comprehensive testing for OWASP A01:2021 - Broken Access Control
# Target: memeit.pro production API

$baseUrl = "https://memeit.pro"
$results = @()
$startTime = Get-Date

function Write-TestResult {
    param(
        [string]$Message,
        [string]$TestType = "ACCESS",
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

function Test-EndpointAccess {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [hashtable]$Data = $null
    )
    
    try {
        $url = "$baseUrl$Endpoint"
        $requestParams = @{
            Uri = $url
            Method = $Method
            Headers = $Headers
            TimeoutSec = 10
        }
        
        if ($Data -and ($Method -eq "POST" -or $Method -eq "PUT")) {
            $requestParams.Body = ($Data | ConvertTo-Json)
            $requestParams.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @requestParams
        
        return @{
            StatusCode = $response.StatusCode
            ContentLength = $response.Content.Length
            Headers = $response.Headers
            Content = $response.Content.Substring(0, [Math]::Min(500, $response.Content.Length))
        }
    } catch {
        $statusCode = $null
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.Value__
        }
        
        return @{
            StatusCode = $statusCode
            Error = $_.Exception.Message
        }
    }
}

function Test-HorizontalPrivilegeEscalation {
    Write-TestResult "=== Testing Horizontal Privilege Escalation ===" "ACCESS" "INFO"
    
    # Test 1: User-specific resource access patterns
    Write-TestResult "Testing user-specific resource enumeration..." "ACCESS" "TESTING"
    
    $userPatterns = @(
        "/api/v1/jobs/1",
        "/api/v1/jobs/user/123",
        "/api/v1/clips/user_123", 
        "/api/v1/profile/456",
        "/api/v1/history/789"
    )
    
    foreach ($pattern in $userPatterns) {
        $result = Test-EndpointAccess -Endpoint $pattern
        
        switch ($result.StatusCode) {
            200 { Write-TestResult "POTENTIAL VULNERABILITY: User resource accessible at $pattern" "ACCESS" "VULN" }
            404 { Write-TestResult "User resource properly not found: $pattern" "ACCESS" "PASS" }
            401 { Write-TestResult "Authentication required for: $pattern" "ACCESS" "PASS" }
            default { Write-TestResult "Unexpected response for $pattern`: $($result.StatusCode)" "ACCESS" "WARN" }
        }
        Start-Sleep 1
    }
    
    # Test 2: Parameter-based user access (IDOR)
    Write-TestResult "Testing Insecure Direct Object Reference (IDOR)..." "ACCESS" "TESTING"
    
    $idorTests = @(
        @{ Endpoint = "/api/v1/metadata"; Data = @{ url = "https://youtube.com/watch?v=test"; user_id = "1" } },
        @{ Endpoint = "/api/v1/jobs"; Data = @{ url = "https://youtube.com/watch?v=test"; owner = "admin" } },
        @{ Endpoint = "/api/v1/clips"; Data = @{ file_id = "123"; user = "other_user" } }
    )
    
    foreach ($test in $idorTests) {
        $result = Test-EndpointAccess -Endpoint $test.Endpoint -Method "POST" -Data $test.Data
        
        switch ($result.StatusCode) {
            200 { Write-TestResult "POTENTIAL IDOR: Accepted user parameter at $($test.Endpoint)" "ACCESS" "WARN" }
            {$_ -in @(400, 422)} { Write-TestResult "User parameter validation working: $($test.Endpoint)" "ACCESS" "PASS" }
            default { Write-TestResult "IDOR test response $($result.StatusCode) for $($test.Endpoint)" "ACCESS" "INFO" }
        }
        Start-Sleep 1
    }
}

function Test-VerticalPrivilegeEscalation {
    Write-TestResult "=== Testing Vertical Privilege Escalation ===" "ACCESS" "INFO"
    
    # Test 1: Admin endpoint access without authentication
    Write-TestResult "Testing admin endpoint access without authentication..." "ACCESS" "TESTING"
    
    $adminEndpoints = @(
        "/api/v1/admin/metrics",
        "/api/v1/admin/health",
        "/api/v1/admin/users", 
        "/api/v1/admin/system",
        "/api/v1/admin/logs",
        "/api/v1/admin/config"
    )
    
    foreach ($endpoint in $adminEndpoints) {
        $result = Test-EndpointAccess -Endpoint $endpoint
        
        switch ($result.StatusCode) {
            200 { Write-TestResult "CRITICAL: Admin endpoint accessible without auth: $endpoint" "ACCESS" "VULN" }
            401 { Write-TestResult "Admin endpoint properly protected: $endpoint" "ACCESS" "PASS" }
            403 { Write-TestResult "Admin endpoint forbidden (good): $endpoint" "ACCESS" "PASS" }
            404 { Write-TestResult "Admin endpoint not found: $endpoint" "ACCESS" "INFO" }
            default { Write-TestResult "Admin endpoint response $($result.StatusCode): $endpoint" "ACCESS" "INFO" }
        }
        Start-Sleep 1
    }
    
    # Test 2: Role injection via headers
    Write-TestResult "Testing role injection via headers..." "ACCESS" "TESTING"
    
    $roleHeaders = @(
        @{ "X-User-Role" = "admin" },
        @{ "X-Role" = "administrator" },
        @{ "User-Role" = "admin" },
        @{ "Authorization" = "Bearer admin" },
        @{ "X-Admin" = "true" },
        @{ "Is-Admin" = "1" }
    )
    
    foreach ($headers in $roleHeaders) {
        $result = Test-EndpointAccess -Endpoint "/api/v1/admin/metrics" -Headers $headers
        
        if ($result.StatusCode -eq 200) {
            Write-TestResult "CRITICAL: Role injection successful with headers: $($headers | ConvertTo-Json)" "ACCESS" "VULN"
        } else {
            Write-TestResult "Role injection blocked for headers: $($headers.Keys -join ',')" "ACCESS" "PASS"
        }
        Start-Sleep 1
    }
    
    # Test 3: Parameter-based role elevation
    Write-TestResult "Testing role elevation via parameters..." "ACCESS" "TESTING"
    
    $roleParams = @(
        @{ role = "admin" },
        @{ is_admin = "true" },
        @{ admin = "1" },
        @{ privileges = "admin" },
        @{ access_level = "admin" }
    )
    
    foreach ($params in $roleParams) {
        $testData = @{ url = "https://youtube.com/watch?v=test" }
        $params.GetEnumerator() | ForEach-Object { $testData[$_.Key] = $_.Value }
        
        $result = Test-EndpointAccess -Endpoint "/api/v1/metadata" -Method "POST" -Data $testData
        
        if ($result.Content -and $result.Content.ToLower().Contains("admin")) {
            Write-TestResult "POTENTIAL: Admin context in response with params: $($params | ConvertTo-Json)" "ACCESS" "WARN"
        } else {
            Write-TestResult "Role parameter ignored: $($params.Keys -join ',')" "ACCESS" "PASS"
        }
        Start-Sleep 1
    }
}

function Test-DirectObjectReference {
    Write-TestResult "=== Testing Direct Object Reference Attacks ===" "ACCESS" "INFO"
    
    # Test 1: Numeric ID enumeration
    Write-TestResult "Testing numeric ID enumeration..." "ACCESS" "TESTING"
    
    $idEndpoints = @(
        "/api/v1/jobs/{0}",
        "/api/v1/clips/{0}",
        "/api/v1/files/{0}",
        "/api/v1/download/{0}"
    )
    
    $testIds = @(1, 2, 100, 999, "admin", "../etc/passwd", "NULL", "0")
    
    foreach ($endpointTemplate in $idEndpoints) {
        foreach ($testId in $testIds) {
            $endpoint = $endpointTemplate -f $testId
            $result = Test-EndpointAccess -Endpoint $endpoint
            
            switch ($result.StatusCode) {
                200 { Write-TestResult "POTENTIAL: Direct access to object $testId at $endpoint" "ACCESS" "WARN" }
                404 { Write-TestResult "Object $testId not found (expected): $endpoint" "ACCESS" "PASS" }
                401 { Write-TestResult "Authentication required for $testId`: $endpoint" "ACCESS" "PASS" }
                default { Write-TestResult "Object access test $testId response $($result.StatusCode)" "ACCESS" "INFO" }
            }
            Start-Sleep 0.5
        }
    }
    
    # Test 2: File path traversal
    Write-TestResult "Testing file path traversal..." "ACCESS" "TESTING"
    
    $traversalPayloads = @(
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
        "/etc/passwd",
        "../../app/config.py",
        "../.env",
        "../../docker-compose.yml"
    )
    
    foreach ($payload in $traversalPayloads) {
        $encodedPayload = [System.Web.HttpUtility]::UrlEncode($payload)
        $result = Test-EndpointAccess -Endpoint "/api/v1/clips/$encodedPayload"
        
        if ($result.StatusCode -eq 200) {
            $content = $result.Content.ToLower()
            if ($content.Contains("root:") -or $content.Contains("passwd") -or $content.Contains("[users]")) {
                Write-TestResult "CRITICAL: Path traversal successful with $payload" "ACCESS" "VULN"
            } else {
                Write-TestResult "Path traversal blocked: $payload" "ACCESS" "PASS"
            }
        } else {
            Write-TestResult "Path traversal properly rejected: $payload" "ACCESS" "PASS"
        }
        Start-Sleep 1
    }
}

function Test-AdministrativeFunctionAccess {
    Write-TestResult "=== Testing Administrative Function Access ===" "ACCESS" "INFO"
    
    # Test 1: Administrative operations
    Write-TestResult "Testing administrative operations..." "ACCESS" "TESTING"
    
    $adminOperations = @(
        @{ Endpoint = "/api/v1/admin/restart"; Method = "POST" },
        @{ Endpoint = "/api/v1/admin/shutdown"; Method = "POST" },
        @{ Endpoint = "/api/v1/admin/clear-cache"; Method = "POST" },
        @{ Endpoint = "/api/v1/admin/delete-all"; Method = "DELETE" },
        @{ Endpoint = "/api/v1/admin/backup"; Method = "POST" },
        @{ Endpoint = "/api/v1/admin/logs"; Method = "GET" },
        @{ Endpoint = "/api/v1/system/status"; Method = "GET" },
        @{ Endpoint = "/api/v1/system/health"; Method = "GET" }
    )
    
    foreach ($operation in $adminOperations) {
        $result = Test-EndpointAccess -Endpoint $operation.Endpoint -Method $operation.Method
        
        switch ($result.StatusCode) {
            200 { Write-TestResult "CRITICAL: Admin operation accessible: $($operation.Method) $($operation.Endpoint)" "ACCESS" "VULN" }
            401 { Write-TestResult "Admin operation properly protected: $($operation.Method) $($operation.Endpoint)" "ACCESS" "PASS" }
            404 { Write-TestResult "Admin operation not found: $($operation.Method) $($operation.Endpoint)" "ACCESS" "INFO" }
            default { Write-TestResult "Admin operation response $($result.StatusCode): $($operation.Endpoint)" "ACCESS" "INFO" }
        }
        Start-Sleep 1
    }
    
    # Test 2: Debug and development endpoints
    Write-TestResult "Testing debug and development endpoints..." "ACCESS" "TESTING"
    
    $debugEndpoints = @(
        "/debug",
        "/debug/cors",
        "/debug/redis",
        "/test",
        "/dev", 
        "/development",
        "/.env",
        "/config",
        "/status",
        "/info",
        "/version"
    )
    
    foreach ($endpoint in $debugEndpoints) {
        $result = Test-EndpointAccess -Endpoint $endpoint
        
        if ($result.StatusCode -eq 200) {
            $content = $result.Content.ToLower()
            $sensitiveKeywords = @("debug", "config", "password", "secret", "key")
            $hasSensitive = $sensitiveKeywords | Where-Object { $content.Contains($_) }
            
            if ($hasSensitive) {
                Write-TestResult "HIGH: Debug endpoint exposing sensitive info: $endpoint" "ACCESS" "VULN"
            } else {
                Write-TestResult "Debug endpoint accessible but safe: $endpoint" "ACCESS" "WARN"
            }
        } elseif ($result.StatusCode -eq 404) {
            Write-TestResult "Debug endpoint properly disabled: $endpoint" "ACCESS" "PASS"
        }
        Start-Sleep 1
    }
}

function Test-ForceBrowsing {
    Write-TestResult "=== Testing Force Browsing Attacks ===" "ACCESS" "INFO"
    
    # Test 1: Common hidden directories and files
    Write-TestResult "Testing common hidden directories..." "ACCESS" "TESTING"
    
    $hiddenPaths = @(
        "/.git",
        "/.git/config",
        "/.env",
        "/.env.production",
        "/backup",
        "/backups",
        "/tmp",
        "/logs",
        "/config",
        "/admin",
        "/administrator",
        "/management",
        "/internal",
        "/private",
        "/restricted"
    )
    
    foreach ($path in $hiddenPaths) {
        $result = Test-EndpointAccess -Endpoint $path
        
        switch ($result.StatusCode) {
            200 { Write-TestResult "WARNING: Hidden path accessible: $path" "ACCESS" "WARN" }
            403 { Write-TestResult "Hidden path forbidden (good): $path" "ACCESS" "PASS" }
            404 { Write-TestResult "Hidden path not found (expected): $path" "ACCESS" "PASS" }
            default { Write-TestResult "Hidden path response $($result.StatusCode): $path" "ACCESS" "INFO" }
        }
        Start-Sleep 1
    }
    
    # Test 2: HTTP method bypass
    Write-TestResult "Testing HTTP method bypass..." "ACCESS" "TESTING"
    
    $protectedEndpoint = "/api/v1/admin/metrics"
    $methods = @("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")
    
    foreach ($method in $methods) {
        $result = Test-EndpointAccess -Endpoint $protectedEndpoint -Method $method
        
        switch ($result.StatusCode) {
            200 { Write-TestResult "POTENTIAL: Admin endpoint accessible via $method" "ACCESS" "WARN" }
            405 { Write-TestResult "Method $method not allowed (expected)" "ACCESS" "PASS" }
            401 { Write-TestResult "Authentication required for $method (good)" "ACCESS" "PASS" }
            default { Write-TestResult "Method $method response: $($result.StatusCode)" "ACCESS" "INFO" }
        }
        Start-Sleep 1
    }
}

function Generate-Report {
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
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
        
        if ($status -eq "VULN" -or $status -eq "WARN") {
            $vulnerabilities += $result
        }
    }
    
    $accessTests = $results | Where-Object { $_.test -eq "ACCESS" }
    $totalTests = $accessTests.Count
    $vulnCount = ($accessTests | Where-Object { $_.status -eq "VULN" }).Count
    $warnCount = ($accessTests | Where-Object { $_.status -eq "WARN" }).Count
    $passCount = ($accessTests | Where-Object { $_.status -eq "PASS" }).Count
    
    Write-Host ""
    Write-Host ("="*80)
    Write-Host "A01 BROKEN ACCESS CONTROL PENETRATION TESTING REPORT" -ForegroundColor Cyan
    Write-Host ("="*80)
    
    Write-Host "Test Summary:" -ForegroundColor Yellow
    Write-Host "   Total Tests: $totalTests"
    Write-Host "   Duration: $([math]::Round($duration, 2)) seconds"
    Write-Host "   Critical Vulnerabilities: $vulnCount"
    Write-Host "   Warnings: $warnCount"
    Write-Host "   Passed Controls: $passCount"
    
    if ($vulnCount -gt 0) {
        Write-Host ""
        Write-Host "CRITICAL ACCESS CONTROL VULNERABILITIES:" -ForegroundColor Red
        $criticalVulns = $vulnerabilities | Where-Object { $_.status -eq "VULN" }
        foreach ($vuln in $criticalVulns) {
            Write-Host "   - $($vuln.message)" -ForegroundColor Red
        }
    }
    
    if ($warnCount -gt 0) {
        Write-Host ""
        Write-Host "ACCESS CONTROL WARNINGS:" -ForegroundColor Yellow
        $warnings = $vulnerabilities | Where-Object { $_.status -eq "WARN" }
        foreach ($warn in $warnings) {
            Write-Host "   - $($warn.message)" -ForegroundColor Yellow
        }
    }
    
    if ($vulnCount -eq 0) {
        Write-Host ""
        Write-Host "NO CRITICAL ACCESS CONTROL VULNERABILITIES DETECTED" -ForegroundColor Green
        Write-Host "   Application demonstrates good access control implementation" -ForegroundColor Green
    }
    
    # Overall assessment
    $assessment = if ($vulnCount -eq 0 -and $warnCount -le 2) {
        "EXCELLENT ACCESS CONTROL"
    } elseif ($vulnCount -eq 0 -and $warnCount -le 5) {
        "GOOD ACCESS CONTROL"
    } elseif ($vulnCount -le 2) {
        "MODERATE ACCESS CONTROL ISSUES"
    } else {
        "SIGNIFICANT ACCESS CONTROL VULNERABILITIES"
    }
    
    Write-Host ""
    Write-Host "Overall Assessment: $assessment" -ForegroundColor Cyan
    Write-Host "Next: Run A02 Cryptographic Failures testing" -ForegroundColor Cyan
    Write-Host "Results logged for security audit documentation" -ForegroundColor Cyan
}

# Main execution
Write-Host "PHASE 4: A01 BROKEN ACCESS CONTROL PENETRATION TESTING" -ForegroundColor Cyan
Write-Host "Target: memeit.pro production environment" -ForegroundColor Cyan
Write-Host "Testing OWASP A01:2021 - Broken Access Control" -ForegroundColor Cyan
Write-Host ("="*80)

# Add System.Web for URL encoding
Add-Type -AssemblyName System.Web

# Run all test categories
Test-HorizontalPrivilegeEscalation
Test-VerticalPrivilegeEscalation  
Test-DirectObjectReference
Test-AdministrativeFunctionAccess
Test-ForceBrowsing

# Generate final report
Generate-Report 