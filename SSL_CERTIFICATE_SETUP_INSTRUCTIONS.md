# Let's Encrypt SSL Certificate Setup for memeit.pro

## Overview
This guide helps you obtain Let's Encrypt SSL certificates for `memeit.pro` and `www.memeit.pro` to resolve the `ERR_SSL_PROTOCOL_ERROR` and ensure both domains serve the backend health JSON (`{"status":"ok"}`) over HTTPS.

## Prerequisites
- Access to your AWS Lightsail instance (reachable via `memeit.pro`)
- SSH access to the instance
- Docker and docker-compose installed on the instance
- The Meme Maker application deployed and running
- DNS records pointing to your Lightsail instance

## Current Status
Based on our analysis:
- ✅ DNS records are correctly pointing to your Lightsail instance
- ✅ Backend service is running and healthy
- ❌ SSL certificate acquisition is failing due to ACME challenge validation issues

## Option 1: Run Script on Lightsail Instance (Recommended)

### Step 1: Connect to Your Lightsail Instance
```bash
ssh ubuntu@memeit.pro
```

### Step 2: Navigate to Your Project Directory
```bash
cd /home/ubuntu/meme-maker
```

### Step 3: Create and Run the Certificate Script
Create a file called `obtain_certs.sh`:

```bash
nano obtain_certs.sh
```

Copy the contents from `obtain_lets_encrypt_certs.sh` (provided in this repository), then:

```bash
chmod +x obtain_certs.sh
./obtain_certs.sh
```

## Option 2: Upload Script from Local Machine

If you have SSH access configured on your local machine:

### Step 1: Upload the Script
```powershell
# From your local Meme Maker directory
scp obtain_lets_encrypt_certs.sh ubuntu@memeit.pro:/tmp/obtain_certs.sh
```

### Step 2: Connect and Run
```powershell
ssh ubuntu@memeit.pro "chmod +x /tmp/obtain_certs.sh && cd /home/ubuntu/meme-maker && /tmp/obtain_certs.sh"
```

## What the Script Does

1. **Verifies DNS and Network**
   - Checks that DNS records point to the correct IP
   - Verifies port 80 and 443 are accessible

2. **Ensures Caddy is Running**
   - Checks for existing Caddy container
   - Starts it if not running

3. **Updates Caddyfile Configuration**
   - Ensures proper email configuration for ACME
   - Sets up the correct domain routing

4. **Restarts Caddy with New Configuration**
   - Stops current container
   - Rebuilds and starts with updated config
   - Waits for certificate acquisition

5. **Validates Certificate Acquisition**
   - Checks Caddy logs for success messages
   - Tests local and public HTTPS endpoints

## Success Criteria

The script checks for these success criteria:

✅ **Caddy logs contain 'certificate obtained'**
- Indicates Let's Encrypt successfully issued certificates

✅ **Local HTTPS endpoint responds with `{"status":"ok"}`**
- `curl -k https://localhost/health` returns the health JSON

✅ **Public HTTPS endpoint returns HTTP 200**
- `curl -IL https://www.memeit.pro/health` shows successful response

## Troubleshooting

### If Certificate Acquisition Fails

1. **Check Firewall Rules**
   ```bash
   # Ensure ports 80 and 443 are open
   sudo ufw status
   ```

2. **Verify DNS Propagation**
   ```bash
   dig memeit.pro
   dig www.memeit.pro
   ```

3. **Check Caddy Logs for Specific Errors**
   ```bash
   docker logs $(docker ps -q --filter "ancestor=caddy") --tail 100
   ```

4. **Common Issues:**
   - **502 Bad Gateway**: Backend service not responding
   - **Firewall blocking**: Ports 80/443 not accessible from internet
   - **DNS issues**: Domain not pointing to correct IP
   - **Rate limiting**: Too many certificate requests (wait 1 hour)

### If Backend is Not Responding

1. **Check Backend Health**
   ```bash
   docker ps
   docker logs meme-prod-backend
   ```

2. **Restart Backend Service**
   ```bash
   cd /home/ubuntu/meme-maker
   docker compose -f infra/production/docker-compose.prod.yml restart backend
   ```

### Manual Certificate Check

To manually verify certificates after the script runs:

```bash
# Check certificate details
echo | openssl s_client -servername memeit.pro -connect memeit.pro:443 2>/dev/null | openssl x509 -noout -dates

# Test endpoints
curl -I https://memeit.pro/health
curl -I https://www.memeit.pro/health
```

## Security Notes

- The script uses `admin@memeit.pro` as the ACME email contact
- Certificates are automatically renewed by Caddy
- Make sure your Lightsail instance security group allows HTTP (80) and HTTPS (443) traffic

## Next Steps After Success

Once certificates are obtained:

1. **Verify the website loads properly**
   - Visit `https://memeit.pro` in a browser
   - Check for valid SSL certificate (green lock icon)

2. **Test the API endpoints**
   - `https://memeit.pro/health` should return `{"status":"ok"}`
   - `https://memeit.pro/docs` should show API documentation

3. **Monitor certificate renewal**
   - Caddy automatically renews certificates
   - Check logs periodically for renewal success

## Support

If you continue to experience issues:

1. Share the complete output of the certificate script
2. Provide the Caddy container logs
3. Confirm your DNS settings and firewall configuration
4. Check if Let's Encrypt rate limits are affecting your domain 