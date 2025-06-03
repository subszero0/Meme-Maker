# 🧪 User Testing Checklist for Meme Maker

## Pre-Testing Setup
- [ ] Website is accessible at https://memeit.pro
- [ ] SSL certificate is working (green lock icon)
- [ ] All Docker containers are healthy
- [ ] Monitoring dashboards are accessible
- [ ] S3 bucket has proper permissions

## Functional Testing

### Basic Flow Testing
- [ ] **Homepage loads correctly**
  - [ ] UI displays properly on desktop
  - [ ] UI displays properly on mobile
  - [ ] All text is readable
  - [ ] Form elements are accessible

- [ ] **URL Input Testing**
  - [ ] Can paste YouTube URL
  - [ ] Can paste Instagram URL  
  - [ ] Can paste Facebook URL
  - [ ] Can paste Threads URL
  - [ ] Can paste Reddit URL
  - [ ] Error handling for invalid URLs
  - [ ] Error handling for private/blocked content

- [ ] **Video Trimming Interface**
  - [ ] Video preview loads
  - [ ] Dual-handle slider works
  - [ ] Timestamp input boxes work
  - [ ] Live preview updates while scrubbing
  - [ ] 3-minute limit is enforced
  - [ ] Terms acceptance checkbox works

- [ ] **Download Process**
  - [ ] Render process initiates
  - [ ] Progress indication works
  - [ ] Download link generation
  - [ ] File downloads successfully
  - [ ] File plays correctly
  - [ ] File is trimmed to correct duration

### Error Handling Testing
- [ ] **Rate Limiting**
  - [ ] Global rate limit (10 requests/minute) works
  - [ ] Job rate limit (3 jobs/hour) works
  - [ ] User-friendly error messages display

- [ ] **Content Restrictions**
  - [ ] Private video handling
  - [ ] Geo-blocked content handling
  - [ ] Copyright-protected content handling
  - [ ] Age-restricted content handling

- [ ] **Technical Errors**
  - [ ] Network timeout handling
  - [ ] Server overload handling
  - [ ] Invalid video format handling

## Performance Testing
- [ ] **Page Load Times**
  - [ ] Homepage loads in <3 seconds
  - [ ] Video metadata fetches in <5 seconds
  - [ ] Video preview loads in <10 seconds

- [ ] **Processing Times**
  - [ ] 30-second clip processes in <30 seconds
  - [ ] 3-minute clip processes in <60 seconds
  - [ ] Queue handling when multiple users active

## Cross-Platform Testing

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest) 
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile Devices
- [ ] iOS Safari
- [ ] Android Chrome
- [ ] Mobile responsiveness (360px width minimum)

### Accessibility Testing
- [ ] Keyboard navigation works
- [ ] Screen reader compatibility
- [ ] Color contrast compliance
- [ ] Focus indicators visible

## Security Testing
- [ ] **HTTPS Enforcement**
  - [ ] HTTP redirects to HTTPS
  - [ ] Security headers present
  - [ ] SSL/TLS configuration secure

- [ ] **Input Validation**
  - [ ] XSS protection
  - [ ] SQL injection protection
  - [ ] File upload security

## Test Scenarios

### Happy Path Scenarios
1. **YouTube Short Video (30 seconds)**
   - Paste URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
   - Trim: 0:10 to 0:40
   - Download and verify

2. **Instagram Reel (1 minute)**
   - Test Instagram reel URL
   - Trim: 0:15 to 1:00
   - Download and verify

3. **Long YouTube Video (10+ minutes)**
   - Paste long video URL
   - Trim: 2:00 to 5:00 (3 minutes max)
   - Verify 3-minute limit enforcement

### Edge Case Scenarios
1. **Maximum Length Clip**
   - Create exactly 3-minute clip
   - Verify processing and download

2. **Very Short Clip**
   - Create 5-second clip
   - Verify quality and playback

3. **High Resolution Video**
   - Test 4K YouTube video
   - Verify processing and file size

## Monitoring During Testing
- [ ] **Application Metrics**
  - [ ] Response times in Grafana
  - [ ] Error rates monitoring
  - [ ] Resource usage tracking

- [ ] **Infrastructure Health**
  - [ ] Docker container health
  - [ ] Redis queue monitoring
  - [ ] S3 storage usage
  - [ ] Server resource utilization

## User Feedback Collection
- [ ] **Usability Feedback**
  - [ ] Interface intuitiveness
  - [ ] Process clarity
  - [ ] Error message helpfulness
  - [ ] Overall user experience

- [ ] **Performance Feedback**
  - [ ] Loading speed perception
  - [ ] Processing time satisfaction
  - [ ] Download speed experience

## Post-Testing Checklist
- [ ] Collect and analyze logs
- [ ] Review performance metrics
- [ ] Document bugs and issues
- [ ] Prioritize fixes and improvements
- [ ] Plan next iteration

## Emergency Procedures
- [ ] **If site goes down:**
  - [ ] Check Docker containers: `docker ps`
  - [ ] Check Caddy status: `systemctl status caddy`
  - [ ] Check logs: `docker logs meme-prod-backend`
  - [ ] Restart services: `docker-compose restart`

- [ ] **If SSL fails:**
  - [ ] Check Caddy logs: `journalctl -u caddy`
  - [ ] Verify DNS configuration
  - [ ] Check Route 53 permissions

## Success Criteria
- [ ] **Availability:** 99.9% uptime during testing
- [ ] **Performance:** <3s page load, <60s processing
- [ ] **Functionality:** All core features working
- [ ] **User Experience:** Positive feedback from testers
- [ ] **Security:** No vulnerabilities found
- [ ] **Scalability:** Handles concurrent users 