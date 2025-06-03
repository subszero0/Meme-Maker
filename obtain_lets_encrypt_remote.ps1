# CURSOR PROMPT 46.0 • Obtain Let's Encrypt certificates for memeit.pro (Remote)
# This script connects to the Lightsail instance and runs the certificate acquisition there

Write-Host "Starting remote Let's Encrypt certificate acquisition for memeit.pro..." -ForegroundColor Green

# Configuration
$LIGHTSAIL_HOST = "memeit.pro"  # Use hostname instead of hard-coded IP
$LIGHTSAIL_USER = "ubuntu"
$SSH_KEY_PATH = "$env:USERPROFILE\.ssh\id_rsa"  # Default SSH key path

Write-Host "Target Lightsail Host: $LIGHTSAIL_HOST" -ForegroundColor Cyan
Write-Host "SSH User: $LIGHTSAIL_USER" -ForegroundColor Cyan

# Check if SSH key exists
if (-not (Test-Path $SSH_KEY_PATH)) {
    Write-Host "❌ SSH key not found at $SSH_KEY_PATH" -ForegroundColor Red
    Write-Host "Please ensure your SSH key is available or update the SSH_KEY_PATH variable" -ForegroundColor Yellow
    exit 1
}

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
try {
    $testCommand = "echo 'SSH connection successful'"
    $sshResult = ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 -o BatchMode=yes "$LIGHTSAIL_USER@$LIGHTSAIL_HOST" $testCommand 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH connection successful" -ForegroundColor Green
    } else {
        Write-Host "❌ SSH connection failed" -ForegroundColor Red
        Write-Host "Please check:" -ForegroundColor Yellow
        Write-Host "  1. SSH key path: $SSH_KEY_PATH" -ForegroundColor Yellow
        Write-Host "  2. Lightsail host: $LIGHTSAIL_HOST" -ForegroundColor Yellow
        Write-Host "  3. Security group allows SSH from your IP" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ SSH test failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create the remote script
$remoteScript = @'
#!/bin/bash
set -euo pipefail

echo "🔍 Starting Let's Encrypt certificate acquisition on Lightsail instance..."

# ------------------------------------------------------------------
# 1. Verify DNS → instance IP + port reachability
# ------------------------------------------------------------------
echo "1. Verifying DNS and port reachability..."

PUBLIC_IP=$(curl -s ifconfig.me/ip || echo "unknown")
echo "Instance public IP = $PUBLIC_IP"

echo "➜ DNS A-records"
dig +short memeit.pro       | sed 's/^/  memeit.pro  → /'
dig +short www.memeit.pro   | sed 's/^/  www.memeit.pro → /'

echo "➜ Port reachability (from instance)"
nc -zv -w3 localhost 80  && echo "  Port 80 open" || echo "  Port 80 closed"
nc -zv -w3 localhost 443 && echo "  Port 443 open" || echo "  Port 443 closed"

# ------------------------------------------------------------------
# 2. Ensure a running Caddy container
# ------------------------------------------------------------------
echo ""
echo "2. Checking Caddy container status..."

CID=$(docker ps -q --filter "ancestor=caddy" 2>/dev/null || echo "")
if [ -z "$CID" ]; then
  echo "Starting Caddy container..."
  cd /home/ubuntu/meme-maker
  docker compose -f infra/production/docker-compose.prod.yml up -d --no-deps caddy
  sleep 5
  CID=$(docker ps -q --filter "ancestor=caddy" 2>/dev/null || echo "")
fi

if [ -n "$CID" ]; then
  echo "Caddy container = $CID"
else
  echo "❌ Failed to start Caddy container"
  exit 1
fi

# ------------------------------------------------------------------
# 3. Verify Caddyfile.prod configuration
# ------------------------------------------------------------------
echo ""
echo "3. Verifying Caddyfile.prod configuration..."

cd /home/ubuntu/meme-maker
caddyfile_path="infra/caddy/Caddyfile.prod"

if [ -f "$caddyfile_path" ]; then
  echo "Current Caddyfile.prod content:"
  cat "$caddyfile_path"
  
  # Check if email is configured
  if grep -q "email.*admin@memeit\.pro" "$caddyfile_path"; then
    echo "✅ Email configuration found"
  else
    echo "❌ Email configuration missing, updating..."
    
    # Update the Caddyfile with proper email configuration
    cat > "$caddyfile_path" << 'EOF'
{
    email admin@memeit.pro
}

memeit.pro, www.memeit.pro {
    encode         zstd gzip
    reverse_proxy  backend:8000
}
EOF
    echo "✅ Caddyfile.prod updated with email configuration"
  fi
else
  echo "❌ Caddyfile.prod not found at $caddyfile_path"
  exit 1
fi

# ------------------------------------------------------------------
# 4. Rebuild & restart Caddy, wait for ACME
# ------------------------------------------------------------------
echo ""
echo "4. Rebuilding and restarting Caddy..."

echo "Stopping current Caddy container..."
docker compose -f infra/production/docker-compose.prod.yml stop caddy

echo "Starting Caddy with updated configuration..."
docker compose -f infra/production/docker-compose.prod.yml up -d --no-deps --build caddy

echo "⏳ Waiting 120 seconds for certificate issuance..."
for i in {1..12}; do
  sleep 10
  echo "  Elapsed: $((i*10)) seconds..."
done

# ------------------------------------------------------------------
# 5. Show fresh Caddy logs – expect "certificate obtained"
# ------------------------------------------------------------------
echo ""
echo "5. Checking Caddy logs for certificate acquisition..."

CID=$(docker ps -q --filter "ancestor=caddy" 2>/dev/null || echo "")
if [ -n "$CID" ]; then
  echo "Recent Caddy logs:"
  docker logs "$CID" --tail 40 2>/dev/null || echo "Failed to get logs"
  
  logs=$(docker logs "$CID" --tail 40 2>/dev/null || echo "")
  if echo "$logs" | grep -q -E "certificate obtained|successfully obtained"; then
    echo "✅ Certificate obtained successfully!"
  else
    echo "⚠️ Certificate acquisition not confirmed in logs"
  fi
else
  echo "❌ Caddy container not running"
fi

# ------------------------------------------------------------------
# 6. Test locally & publicly
# ------------------------------------------------------------------
echo ""
echo "6. Testing endpoints..."

echo "➜ Testing curl -k https://localhost/health (should return JSON)"
if curl -k -s --max-time 10 https://localhost/health; then
  echo " ✅ Local HTTPS test passed"
else
  echo " ❌ Local HTTPS test failed"
fi

echo ""
echo "➜ Testing curl https://www.memeit.pro/health (expect HTTP 200)"
if curl -IL --max-time 10 https://www.memeit.pro/health 2>/dev/null | head -n 10; then
  echo " ✅ Public HTTPS test completed"
else
  echo " ❌ Public HTTPS test failed"
fi

# ------------------------------------------------------------------
# 7. Final container health
# ------------------------------------------------------------------
echo ""
echo "7. Final container health check..."

echo "Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E 'caddy|backend' || echo "No matching containers"

# Success criteria summary
echo ""
echo "============================================================"
echo "SUCCESS CRITERIA CHECK:"
echo "============================================================"

# Check logs for certificate obtained
logs=$(docker logs "$CID" --tail 40 2>/dev/null || echo "")
echo -n "• Caddy logs contain 'certificate obtained': "
if echo "$logs" | grep -q -E "certificate obtained|successfully obtained"; then
  echo "✅ PASS"
else
  echo "❌ FAIL"
fi

# Check local HTTPS
echo -n "• curl -k https://localhost/health → {'status':'ok'}: "
response=$(curl -k -s --max-time 5 https://localhost/health 2>/dev/null || echo "")
if echo "$response" | grep -q '"status":"ok"'; then
  echo "✅ PASS"
else
  echo "❌ FAIL"
fi

# Check public HTTPS
echo -n "• curl -IL https://www.memeit.pro/health shows HTTP 200: "
status=$(curl -IL -s --max-time 10 https://www.memeit.pro/health 2>/dev/null | head -n 1 || echo "")
if echo "$status" | grep -q "200"; then
  echo "✅ PASS"
else
  echo "❌ FAIL"
fi

echo ""
echo "Script completed!"
'@

# Write the script to a temporary file
$tempScript = [System.IO.Path]::GetTempFileName() + ".sh"
$remoteScript | Out-File -FilePath $tempScript -Encoding UTF8

Write-Host "Uploading and executing script on Lightsail instance..." -ForegroundColor Yellow

try {
    # Upload the script
    scp -i $SSH_KEY_PATH $tempScript "$LIGHTSAIL_USER@$LIGHTSAIL_HOST":/tmp/obtain_certs.sh
    
    # Make it executable and run it
    ssh -i $SSH_KEY_PATH "$LIGHTSAIL_USER@$LIGHTSAIL_HOST" "chmod +x /tmp/obtain_certs.sh && /tmp/obtain_certs.sh"
    
    Write-Host "✅ Remote script execution completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to execute remote script: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    # Clean up
    Remove-Item $tempScript -ErrorAction SilentlyContinue
}

Write-Host "`nCertificate acquisition process completed!" -ForegroundColor Green 