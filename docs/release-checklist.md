# Production Release Checklist

This checklist ensures safe and reliable production deployments for Meme Maker.

## Pre-Flight Checklist ✅

Before creating a release tag, verify all items below:

### 🔍 **Staging Verification**
- [ ] ✅ Staging environment is green and healthy
- [ ] ✅ All staging smoke tests pass
- [ ] ✅ Latest changes deployed to staging for at least 24h
- [ ] ✅ No critical issues reported in staging
- [ ] ✅ Performance metrics within acceptable ranges

### 🔒 **Security & Compliance**
- [ ] ✅ SSL Labs A+ rating for staging domain
- [ ] ✅ Security scan results reviewed (no critical vulnerabilities)
- [ ] ✅ Dependencies updated (no known CVEs)
- [ ] ✅ Access logs reviewed for suspicious activity

### 📊 **Monitoring & Alerting**
- [ ] ✅ Error logs < 1% in last 24h
- [ ] ✅ All monitoring endpoints responsive
- [ ] ✅ Prometheus alerts configured and tested
- [ ] ✅ Alertmanager routing to Slack verified
- [ ] ✅ Grafana dashboards updated and functional

### 🧪 **Testing**
- [ ] ✅ All unit tests passing
- [ ] ✅ Integration tests passing
- [ ] ✅ E2E tests passing on staging
- [ ] ✅ Load testing completed (if applicable)
- [ ] ✅ Critical user journeys verified manually

### 🏗️ **Infrastructure**
- [ ] ✅ Production server has sufficient resources
- [ ] ✅ Database backups recent and verified
- [ ] ✅ DNS configurations reviewed
- [ ] ✅ Blue-green deployment scripts tested
- [ ] ✅ Rollback procedures documented and tested

---

## Release Process 🚀

### Step 1: Create Release Tag

```bash
# Ensure you're on main branch with latest changes
git checkout main
git pull origin main

# Create annotated tag with semantic versioning
git tag -a v1.0.0 -m "Release v1.0.0: Go-Live Production Release

Features:
- Complete video clipping functionality
- Blue-green deployment
- Comprehensive monitoring
- Automated scaling

Bug Fixes:
- Fixed worker queue handling
- Resolved memory leaks
- Improved error handling

Security:
- Updated dependencies
- Enhanced input validation
- Added rate limiting"

# Push the tag to trigger deployment
git push origin v1.0.0
```

### Step 2: Monitor Deployment Pipeline

1. **Navigate to GitHub Actions**: [Production Release Workflow](../.github/workflows/prod-release.yml)
2. **Monitor progress**:
   - [ ] ✅ Validation and security scanning (2-3 min)
   - [ ] ✅ Build and push images (5-8 min)
   - [ ] ✅ Test suite completion (8-12 min)
   - [ ] ✅ Promote to production (1-2 min)
   - [ ] ✅ Blue-green deployment (3-5 min)
   - [ ] ✅ Post-deploy E2E tests (3-5 min)

**Expected Total Time**: ≤ 15 minutes

### Step 3: Verify Deployment

#### Automated Checks (handled by pipeline)
- [ ] Health endpoints responding
- [ ] SSL certificate valid
- [ ] Response times < 2s
- [ ] Cypress E2E tests pass

#### Manual Verification
- [ ] Navigate to [https://app.memeit.pro](https://app.memeit.pro)
- [ ] Verify homepage loads correctly
- [ ] Test video URL submission
- [ ] Verify job creation and processing
- [ ] Test file download
- [ ] Check monitoring dashboards

### Step 4: Post-Deploy Monitoring

Monitor the following for 2 hours post-deployment:

- [ ] **Error Rate**: < 1% (5xx responses)
- [ ] **Response Time**: 95th percentile < 2s
- [ ] **Queue Depth**: < 10 jobs
- [ ] **Resource Usage**: CPU < 70%, Memory < 80%
- [ ] **User Traffic**: Normal patterns, no drop-offs

---

## Emergency Rollback 🔄

### Automated Rollback

If post-deploy E2E tests fail, the pipeline automatically executes rollback.

### Manual Rollback

If issues are discovered post-deployment:

```bash
# SSH to production server
ssh production-user@production-server

# Navigate to application directory
cd /opt/meme-maker

# Execute auto-generated rollback script
./rollback_prod.sh

# OR manually specify previous version
./scripts/promote_to_prod.sh v0.9.3 rollback
```

### Rollback Verification

After rollback:
- [ ] Verify application functionality
- [ ] Check error rates return to normal
- [ ] Confirm all services healthy
- [ ] Monitor for 30 minutes

### Post-Rollback Actions

1. **Investigate root cause**
2. **Create hotfix branch** (if needed)
3. **Update staging with fix**
4. **Re-run full testing cycle**
5. **Document lessons learned**

---

## Communication Plan 📢

### Before Release
- [ ] Notify team in #deployments channel
- [ ] Schedule release window (business hours recommended)
- [ ] Prepare status page update (if applicable)

### During Release
- [ ] Share GitHub Actions workflow link
- [ ] Provide real-time updates on progress
- [ ] Monitor Slack alerts

### After Release
- [ ] Announce successful deployment
- [ ] Share performance metrics
- [ ] Update release notes

### If Issues Occur
- [ ] Immediately notify in #incidents channel
- [ ] Escalate to on-call engineer if needed
- [ ] Document timeline and resolution

---

## Release Freeze Policy 🚫

**24-hour launch freeze** after v1.0.0 go-live:

- ✅ **Allowed**: Hotfixes for critical security/stability issues
- ❌ **Forbidden**: Feature additions, non-critical changes, dependency updates

This ensures production stability during the critical post-launch period.

---

## Quick Reference Commands

```bash
# Check deployment status
curl -f https://app.memeit.pro/health

# View recent deployments
tail -n 20 /opt/meme-maker/logs/deployments/production.log

# Check active containers
docker ps --filter "name=meme-prod"

# View container logs
docker logs meme-prod-backend -f --tail=50

# Check Prometheus metrics
curl https://app.memeit.pro/prometheus/api/v1/query?query=up

# Execute rollback
cd /opt/meme-maker && ./rollback_prod.sh
```

---

## Troubleshooting

### Common Issues

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| 5xx error spike | Application error | Check logs, consider rollback |
| Slow response times | Resource constraint | Check CPU/memory, scale if needed |
| SSL certificate warning | Cert renewal failed | Check Caddy logs, renew manually |
| Queue backup | Worker issues | Restart worker containers |
| Health check fails | Service dependency | Check Redis/MinIO connectivity |

### Emergency Contacts

- **Primary On-Call**: [Engineer Name] - [Phone] - [Slack]
- **Secondary On-Call**: [Engineer Name] - [Phone] - [Slack]
- **DevOps Lead**: [Lead Name] - [Phone] - [Slack]

---

## Post-Release Tasks

Within 24 hours of v1.0.0 release:

- [ ] Review deployment metrics and performance
- [ ] Analyze user feedback and error reports
- [ ] Update documentation based on lessons learned
- [ ] Schedule retrospective meeting
- [ ] Plan next release cycle

---

*Last Updated: [Current Date]*  
*Next Review: [Next Review Date]* 