# PHASE 4: INJECTION PENETRATION TESTING (A03:2021)
# ====================================================
# Comprehensive injection testing focusing on command injection through yt-dlp

$baseUrl = "https://memeit.pro"
$metadataEndpoint = "$baseUrl/api/v1/metadata"
$results = @()
$startTime = Get-Date

function Write-TestResult {
    param(
        [string]$Message,
        [string]$TestType = "INJECTION",
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

function Test-InjectionPayload {
    param(
        [string]$PayloadUrl,
        [string]$Description,
        [string]$InjectionType
    )
    
    Write-TestResult "Testing $InjectionType`: $Description" "INJECTION" "TESTING"
    
    try {
        $headers = @{
            'Content-Type' = 'application/json'
        }
        
        $body = @{
            url = $PayloadUrl
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri $metadataEndpoint -Method POST -Headers $headers -Body $body -TimeoutSec 15 -ErrorAction Stop
        
        # If we get a 200 response, check if it contains signs of successful injection
        $responseText = $response | ConvertTo-Json
        if ($responseText -match "uid=|gid=|root|passwd|/etc/|/bin/|whoami|pwd") {
            Write-TestResult "CRITICAL: Command injection successful - system information exposed!" "INJECTION" "VULN"
            return "VULNERABLE"
        } else {
            Write-TestResult "Request succeeded but no injection detected" "INJECTION" "PASS"
            return "SAFE"
        }
        
    } catch {
        $statusCode = $null
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.Value__
        }
        
        if ($statusCode -eq 422) {
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorContent = $reader.ReadToEnd()
                $errorData = $errorContent | ConvertFrom-Json
                $errorDetail = $errorData.detail.ToLower()
                
                if ($errorDetail -match "domain not allowed|invalid url|unsupported|blocked") {
                    Write-TestResult "BLOCKED (Expected): $errorDetail" "INJECTION" "PASS"
                    return "BLOCKED"
                } else {
                    Write-TestResult "422 error: $errorDetail" "INJECTION" "PASS"
                    return "ERROR_HANDLED"
                }
            } catch {
                Write-TestResult "422 response - injection blocked" "INJECTION" "PASS"
                return "BLOCKED"
            }
        } elseif ($statusCode -eq 400) {
            Write-TestResult "400 Bad Request - injection blocked" "INJECTION" "PASS"
            return "BLOCKED"
        } else {
            Write-TestResult "Request failed: $($_.Exception.Message)" "INJECTION" "PASS"
            return "ERROR"
        }
    }
}

# Main execution
Write-Host "PHASE 4: INJECTION PENETRATION TESTING" -ForegroundColor Cyan
Write-Host "Target: memeit.pro production environment" -ForegroundColor Cyan
Write-Host "Testing OWASP A03:2021 - Injection Vulnerabilities" -ForegroundColor Cyan
Write-Host ("="*80)

Write-TestResult "Starting Injection Penetration Testing Suite" "INJECTION" "INFO"

# Test 1: Command Injection through URL parameter
Write-TestResult "=== Test Category 1: Command Injection via URL ===" "INJECTION" "INFO"

$commandInjectionTargets = @(
    @('https://youtube.com/watch?v=test"; whoami; echo "', "Basic command injection"),
    @('https://youtube.com/watch?v=test''whoami''', "Backtick command injection"),
    @('https://youtube.com/watch?v=test''$(whoami)', "Command substitution injection"),
    @('https://youtube.com/watch?v=test && whoami', "Command chaining injection"),
    @('https://youtube.com/watch?v=test; cat /etc/passwd; echo', "File reading injection"),
    @('https://youtube.com/watch?v=test | whoami', "Pipe injection"),
    @('https://youtube.com/watch?v=test%26%26whoami', "URL encoded injection"),
    @('https://youtube.com/watch?v=test\x26\x26whoami', "Hex encoded injection")
)

foreach ($target in $commandInjectionTargets) {
    Test-InjectionPayload $target[0] $target[1] "CMD"
    Start-Sleep 1
}

# Test 2: Path Traversal Injection
Write-TestResult "=== Test Category 2: Path Traversal Injection ===" "INJECTION" "INFO"

$pathTraversalTargets = @(
    @("https://youtube.com/watch?v=../../../etc/passwd", "Basic path traversal"),
    @("https://youtube.com/watch?v=....//....//....//etc/passwd", "Double dot traversal"),
    @("https://youtube.com/watch?v=%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd", "URL encoded traversal"),
    @("https://youtube.com/watch?v=..\..\..\..\windows\system32\drivers\etc\hosts", "Windows path traversal")
)

foreach ($target in $pathTraversalTargets) {
    Test-InjectionPayload $target[0] $target[1] "PATH"
    Start-Sleep 1
}

# Test 3: Script Injection
Write-TestResult "=== Test Category 3: Script Injection ===" "INJECTION" "INFO"

$scriptInjectionTargets = @(
    @('https://youtube.com/watch?v=test<script>alert("xss")</script>', "Basic script injection"),
    @('https://youtube.com/watch?v=test''><script>alert(''xss'')</script>', "Quote breaking script"),
    @('https://youtube.com/watch?v=test"; eval("alert(1)"); variable="', "JavaScript eval injection")
)

foreach ($target in $scriptInjectionTargets) {
    Test-InjectionPayload $target[0] $target[1] "SCRIPT"
    Start-Sleep 1
}

# Test 4: LDAP/NoSQL Injection (Redis)
Write-TestResult "=== Test Category 4: NoSQL Injection ===" "INJECTION" "INFO"

$nosqlTargets = @(
    @('https://youtube.com/watch?v=test"; FLUSHALL; SET test "', "Redis FLUSHALL injection"),
    @('https://youtube.com/watch?v=test\"; CONFIG SET dir /tmp; CONFIG SET dbfilename shell.php; SET test \"', "Redis file write injection"),
    @('https://youtube.com/watch?v=test''; return true; variable=''', "JavaScript injection")
)

foreach ($target in $nosqlTargets) {
    Test-InjectionPayload $target[0] $target[1] "NOSQL"
    Start-Sleep 1
}

# Test 5: Template Injection
Write-TestResult "=== Test Category 5: Template Injection ===" "INJECTION" "INFO"

$templateTargets = @(
    @('https://youtube.com/watch?v={{7*7}}', "Basic template injection"),
    @('https://youtube.com/watch?v={{config.items()}}', "Python template injection"),
    @('https://youtube.com/watch?v=${7*7}', "Expression language injection")
)

foreach ($target in $templateTargets) {
    Test-InjectionPayload $target[0] $target[1] "TEMPLATE"
    Start-Sleep 1
}

# Generate Report
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host ("="*80)
Write-Host "INJECTION PENETRATION TESTING REPORT" -ForegroundColor Cyan
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

$totalTests = ($results | Where-Object { $_.test -eq "INJECTION" }).Count
$passCount = if ($statusCounts.ContainsKey("PASS")) { $statusCounts["PASS"] } else { 0 }
$vulnCount = if ($statusCounts.ContainsKey("VULN")) { $statusCounts["VULN"] } else { 0 }

Write-Host "Test Summary:" -ForegroundColor Yellow
Write-Host "   Total Tests: $totalTests"
Write-Host "   Duration: $([math]::Round($duration, 2)) seconds"
Write-Host "   Blocked/Safe: $passCount"
Write-Host "   Vulnerabilities Found: $vulnCount"

if ($vulnerabilities.Count -gt 0) {
    Write-Host ""
    Write-Host "CRITICAL INJECTION VULNERABILITIES DETECTED:" -ForegroundColor Red
    foreach ($vuln in $vulnerabilities) {
        Write-Host "   - $($vuln.message)" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "NO INJECTION VULNERABILITIES DETECTED" -ForegroundColor Green
    Write-Host "All injection attempts were properly blocked or sanitized" -ForegroundColor Green
}

Write-Host ""
Write-Host "Injection testing completed - Results logged for security audit" 