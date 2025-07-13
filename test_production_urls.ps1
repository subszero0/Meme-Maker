$headers = @{
    'Content-Type' = 'application/json'
}

function Test-ProductionURL($url, $label) {
    Write-Host ""
    Write-Host "=" * 60
    Write-Host "🔍 Testing $label against PRODUCTION"
    Write-Host "URL: $url"
    Write-Host "=" * 60
    
    $body = @{
        url = $url
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri 'https://memeit.pro/api/v1/metadata/extract' -Method POST -Headers $headers -Body $body -ErrorAction Stop
        Write-Host "✅ SUCCESS for $label!"
        Write-Host "Title: $($response.title)"
        Write-Host "Duration: $($response.duration) seconds"
        Write-Host "Uploader: $($response.uploader)"
        Write-Host "Formats: $($response.formats.Count)"
        return $true
    } catch {
        Write-Host "❌ FAILURE for $label!"
        Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)"
        Write-Host "Status Description: $($_.Exception.Response.StatusDescription)"
        
        # Try to get response content
        try {
            $streamReader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $responseContent = $streamReader.ReadToEnd()
            Write-Host "Response Content: $responseContent"
        } catch {
            Write-Host "Could not read response content"
        }
        return $false
    }
}

Write-Host "🧪 Production Instagram URL Comparison Test"
Write-Host "Testing both URLs against the live production endpoint"

# Test working URL
$workingUrl = "https://www.instagram.com/reel/DLjuZlDTrq3/?igsh=MXIxNGNrenp4bGF5aw=="
$workingResult = Test-ProductionURL $workingUrl "WORKING URL"

# Test failing URL  
$failingUrl = "https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw=="
$failingResult = Test-ProductionURL $failingUrl "FAILING URL"

# Summary
Write-Host ""
Write-Host "=" * 60
Write-Host "📊 PRODUCTION COMPARISON SUMMARY"
Write-Host "=" * 60
Write-Host "Working URL Result: $(if($workingResult) {'✅ SUCCESS'} else {'❌ FAILED'})"
Write-Host "Failing URL Result: $(if($failingResult) {'✅ SUCCESS'} else {'❌ FAILED'})"

if ($workingResult -and -not $failingResult) {
    Write-Host ""
    Write-Host "🔍 DIAGNOSIS: Content-specific production issue"
    Write-Host "   - One URL works, other fails in production only"
    Write-Host "   - Both work locally - suggests environment difference"
    Write-Host "   - Could be caching, IP restrictions, or specific content blocking"
} elseif (-not $workingResult -and -not $failingResult) {
    Write-Host ""
    Write-Host "🔍 DIAGNOSIS: General production Instagram extraction failure"
    Write-Host "   - Neither URL works in production"
    Write-Host "   - Both work locally - confirms environment issue"
} elseif ($workingResult -and $failingResult) {
    Write-Host ""
    Write-Host "🔍 DIAGNOSIS: Production issue resolved!"
    Write-Host "   - Both URLs now work in production"
    Write-Host "   - Recent deployment may have fixed the issue"
} 