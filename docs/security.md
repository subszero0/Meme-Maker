# Security Guide - Meme Maker Production

This document outlines the security measures implemented for the Meme Maker production environment, including TLS hardening, SSL certificate management, and compliance with security best practices.

## 🔒 TLS Configuration & SSL Hardening

### SSL/TLS Implementation

Our production environment implements modern TLS security standards:

#### **Certificate Management**
- **Wildcard SSL Certificates**: `*.memeit.pro` via Let's Encrypt
- **DNS-01 Challenge**: Automated certificate issuance through Route 53
- **Auto-Renewal**: Caddy handles automatic certificate renewal
- **OCSP Stapling**: Enabled by default in Caddy (improves performance)

#### **TLS Protocol Support**
```
✅ TLS 1.3 (preferred)
✅ TLS 1.2 (fallback)
❌ TLS 1.1 (disabled)
❌ TLS 1.0 (disabled)
❌ SSL 3.0 (disabled)
❌ SSL 2.0 (disabled)
```

#### **Cipher Suites (Modern Only)**
```
TLS_AES_256_GCM_SHA384                    # TLS 1.3
TLS_CHACHA20_POLY1305_SHA256             # TLS 1.3
TLS_AES_128_GCM_SHA256                   # TLS 1.3
TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384  # TLS 1.2
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384    # TLS 1.2
TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305   # TLS 1.2
TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305     # TLS 1.2
TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256  # TLS 1.2
TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256    # TLS 1.2
```

#### **Elliptic Curves**
```
✅ secp384r1 (P-384)
✅ x25519
✅ secp256r1 (P-256)
```

### SSL Labs Grade Target: **A+**

#### **Required for A+ Rating**
- [x] **Perfect Forward Secrecy (PFS)**: All cipher suites provide PFS
- [x] **Strong Key Exchange**: 384-bit ECDH minimum
- [x] **Strong Cipher**: AES-256 or ChaCha20-Poly1305
- [x] **Strong Hash**: SHA-384 or SHA-256 minimum
- [x] **HSTS**: 1+ year max-age with includeSubDomains and preload
- [x] **Certificate Chain**: Valid, complete, and trusted
- [x] **Mixed Content**: No mixed content issues
- [x] **Protocol Support**: TLS 1.2+ only

#### **SSL Labs Testing**
```bash
# Test production SSL configuration
curl -s "https://api.ssllabs.com/api/v3/analyze?host=app.memeit.pro&startNew=on"

# Manual verification
echo | openssl s_client -servername app.memeit.pro -connect app.memeit.pro:443 -status
```

## 🛡️ Security Headers

### Comprehensive Header Policy

```http
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Content-Security-Policy: upgrade-insecure-requests; default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:; media-src 'self' blob: data: https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none';
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
X-XSS-Protection: 1; mode=block
Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()
```

### **HSTS Preload Configuration**

#### **Current Status**
- **Max-Age**: 63,072,000 seconds (2 years)
- **includeSubDomains**: Yes
- **preload**: Yes

#### **Preload Submission**
1. **Verify HSTS**: Ensure headers are properly set
2. **Test Subdomains**: Confirm all subdomains support HTTPS
3. **Submit to hstspreload.org**: Request inclusion in browser preload lists
4. **Monitor Status**: Track approval process

```bash
# Verify HSTS headers
curl -I https://app.memeit.pro | grep -i strict-transport-security

# Check preload eligibility
curl -s "https://hstspreload.org/api/v2/status?domain=memeit.pro"
```

## 🔐 Certificate Management

### **DNS-01 Challenge Process**

#### **Automatic Certificate Issuance**
1. Caddy detects need for certificate
2. Creates TXT record in Route 53: `_acme-challenge.memeit.pro`
3. Let's Encrypt validates DNS record
4. Certificate issued and stored in Caddy
5. DNS record cleaned up

#### **Certificate Monitoring**
```bash
# Check certificate expiry
echo | openssl s_client -servername app.memeit.pro -connect app.memeit.pro:443 2>/dev/null | openssl x509 -noout -dates

# View certificate details
echo | openssl s_client -servername app.memeit.pro -connect app.memeit.pro:443 2>/dev/null | openssl x509 -noout -text
```

#### **Renewal Process**
- **Frequency**: Automatic renewal 30 days before expiry
- **Method**: DNS-01 challenge via Route 53
- **Backup**: Manual renewal process documented
- **Monitoring**: Prometheus alerts for certificate expiry

### **Certificate Backup & Recovery**

#### **Backup Strategy**
```bash
# Backup Caddy certificate data
docker exec meme-prod-caddy tar -czf /tmp/caddy-certs.tar.gz /data/caddy/certificates
docker cp meme-prod-caddy:/tmp/caddy-certs.tar.gz ./caddy-certs-$(date +%Y%m%d).tar.gz
```

#### **Recovery Process**
```bash
# Restore certificates
docker cp caddy-certs-backup.tar.gz meme-prod-caddy:/tmp/
docker exec meme-prod-caddy tar -xzf /tmp/caddy-certs-backup.tar.gz -C /
docker restart meme-prod-caddy
```

## 🚨 Security Monitoring

### **Certificate Expiry Alerts**
```yaml
# prometheus/rules/ssl-monitoring.yml
groups:
  - name: ssl_certificates
    rules:
      - alert: SSLCertificateExpiringSoon
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring in {{ $value | humanizeDuration }}"
          
      - alert: SSLCertificateExpired
        expr: probe_ssl_earliest_cert_expiry - time() <= 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "SSL certificate has expired"
```

### **Security Scanning**
```bash
# Regular security scans (automated in CI/CD)
trivy fs --security-checks vuln,config .
docker run --rm -v "$PWD":/src -w /src securecodewarrior/docker-security-scanner

# SSL/TLS scanning
testssl.sh app.memeit.pro
sslscan app.memeit.pro
```

## 🛠️ Security Incident Response

### **Certificate Issues**

#### **Expired Certificate**
1. **Immediate**: Force manual renewal
   ```bash
   docker exec meme-prod-caddy caddy reload --config /etc/caddy/Caddyfile
   ```
2. **If fails**: Check DNS permissions and Route 53 access
3. **Escalation**: Manual certificate generation

#### **DNS Resolution Issues**
1. **Check**: Route 53 records and TTL
2. **Verify**: DNS propagation globally
3. **Fallback**: Temporary A record with longer TTL

#### **Security Header Issues**
1. **Verify**: Caddy configuration
2. **Test**: Security headers with securityheaders.com
3. **Update**: Caddyfile and reload

### **Emergency Contacts**
- **Platform Team**: [emergency-contact]
- **AWS Support**: [support-plan-details]
- **Let's Encrypt**: community.letsencrypt.org

## 📋 Compliance Checklist

### **Pre-Production Checklist**
- [ ] **SSL Labs Grade A+** achieved
- [ ] **HSTS Preload** submitted and approved
- [ ] **Certificate Renewal** tested and verified
- [ ] **Security Headers** all implemented
- [ ] **TLS 1.0/1.1** completely disabled
- [ ] **Weak Ciphers** removed
- [ ] **Perfect Forward Secrecy** enabled
- [ ] **OCSP Stapling** functioning
- [ ] **Certificate Transparency** logs monitored
- [ ] **DNS Security** (DNSSEC) enabled on domain

### **Post-Deployment Verification**
- [ ] **External SSL Test**: ssllabs.com/ssltest/
- [ ] **Security Headers**: securityheaders.com
- [ ] **Certificate Chain**: Valid and complete
- [ ] **Mixed Content**: None detected
- [ ] **HSTS Preload**: Status verified
- [ ] **Performance**: TLS handshake < 100ms
- [ ] **Monitoring**: All alerts configured
- [ ] **Documentation**: Updated and current

### **Monthly Security Review**
- [ ] **Certificate Expiry**: Check upcoming renewals
- [ ] **SSL Labs Score**: Maintain A+ rating
- [ ] **Security Advisories**: Review for Caddy/TLS updates
- [ ] **Cipher Suites**: Update if new recommendations
- [ ] **Performance Metrics**: TLS handshake times
- [ ] **Incident Response**: Review and update procedures

## 🔗 External Resources

### **Security Testing Tools**
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
- [HSTS Preload](https://hstspreload.org/)
- [Certificate Transparency](https://crt.sh/)

### **Documentation References**
- [Caddy TLS Documentation](https://caddyserver.com/docs/automatic-https)
- [Let's Encrypt DNS-01 Challenge](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge)
- [AWS Route 53 DNS](https://docs.aws.amazon.com/route53/)
- [OWASP TLS Security](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

**Last Updated**: $(date)
**Next Review**: $(date -d "+1 month")
**Maintained By**: Platform Team 