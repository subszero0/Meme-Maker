# Test job creation
$jobBody = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    start = "00:00:10"
    end = "00:00:30"
} | ConvertTo-Json

Write-Host "Creating job..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/jobs" -Method POST -Body $jobBody -ContentType "application/json"
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Response: $($response.Content)"
    
    # Parse job ID from response
    $jobData = $response.Content | ConvertFrom-Json
    $jobId = $jobData.job_id
    
    Write-Host "Job ID: $jobId"
    
    # Check job status
    Write-Host "Checking job status..."
    $statusResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/jobs/$jobId" -Method GET
    Write-Host "Status Response: $($statusResponse.Content)"
}
catch {
    Write-Host "Error: $_"
    Write-Host "Response: $($_.Exception.Response.GetResponseStream())"
} 