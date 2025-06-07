#!/bin/bash

echo "🔬 SSL & Backend Diagnostic Script"
echo "=================================="

# Test 1: Check Caddy configuration and status
echo "🧪 Test 1: Caddy Service Diagnosis"
echo "📋 Caddy service status:"
systemctl status caddy --no-pager -l || echo "❌ Could not get Caddy status"

echo ""
echo "📄 Caddy configuration file:"
cat /etc/caddy/Caddyfile || echo "❌ Could not read Caddyfile"

echo ""
echo "📊 Caddy logs (last 20 lines):"
journalctl -u caddy --no-pager -n 20 || echo "❌ Could not get Caddy logs"

# Test 2: Check backend container and internal connectivity 
echo ""
echo "🧪 Test 2: Backend Container Diagnosis"
echo "🐳 Backend container status:"
docker ps | grep backend || echo "❌ Backend container not found"

echo ""
echo "📋 Backend container logs (last 10 lines):"
docker logs meme-maker-backend --tail 10 || echo "❌ Could not get backend logs"

echo ""
echo "🔌 Testing internal backend connectivity:"
curl -s -m 5 http://localhost:8000/health || echo "❌ Backend not accessible on localhost:8000"

# Test 3: Check port bindings and network
echo ""
echo "🧪 Test 3: Network & Port Diagnosis"
echo "📡 Port listening status:"
ss -tlnp | grep ":8000\|:80\|:443" || echo "❌ Could not get port info"

echo ""
echo "🌐 Docker network inspection:"
docker network ls
docker network inspect meme-maker_default 2>/dev/null || echo "❌ Default network not found"

# Test 4: SSL Certificate diagnosis
echo ""
echo "🧪 Test 4: SSL Certificate Diagnosis"
echo "🔐 SSL certificate check:"
echo | openssl s_client -connect memeit.pro:443 -servername memeit.pro 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "❌ Could not check SSL certificate"

echo ""
echo "📁 Caddy data directory:"
ls -la /var/lib/caddy/ 2>/dev/null || echo "❌ Could not access Caddy data directory"

echo ""
echo "🔍 Let's Encrypt certificates:"
ls -la /var/lib/caddy/certificates/ 2>/dev/null || echo "❌ No certificates directory found"

# Test 5: Domain and DNS verification
echo ""
echo "🧪 Test 5: Domain Configuration Check"
echo "🌐 External domain resolution:"
nslookup memeit.pro 8.8.8.8 || echo "❌ External DNS lookup failed"

echo ""
echo "🔍 Testing domain accessibility from external perspective:"
curl -I -m 10 http://memeit.pro 2>/dev/null || echo "❌ HTTP not accessible"

echo ""
echo "✅ Diagnostic complete! Analyze results above to identify issues." 