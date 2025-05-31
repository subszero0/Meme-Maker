# Build Plan – Meme Maker 
*A practical, step-by-step checklist (no timeline estimates)*  

---

## 0. Prep & housekeeping
- [ ] **Create Git monorepo** (`clip-downloader/`) with `frontend`, `backend`, `worker`, `infra` sub-dirs.  
- [ ] Add MIT LICENSE and a `CODE_OF_CONDUCT.md`.  
- [ ] Configure **Pre-Commit** hooks (black, isort, flake8, prettier).  
- [ ] Enable GitHub Actions → run lint & unit-tests on every push.  

---

## 1. Core dependencies
- [ ] Pin **Python 3.12** in `pyproject.toml`; add **FastAPI**, **uvicorn**, **pydantic**, **redis-rq**.  
- [ ] Add **yt-dlp** & **ffmpeg-static** to `worker/requirements.txt`.  
- [ ] Initialise **Next.js 14** app in `frontend/` with TypeScript, Tailwind, Headless UI.  

---

## 2. Infrastructure scaffolding
- [ ] Write **Dockerfile.backend** (FastAPI) & **Dockerfile.worker** (yt-dlp + ffmpeg).  
- [ ] Compose local stack with **docker-compose**:  
  - api (FastAPI)  
  - redis (cache + queue)  
  - worker (RQ)  
- [x] Provision **AWS**: S3 bucket (`clip-files-dev`), an IAM role with presign permissions.  
- [x] Terraform (or CloudFormation) files in `infra/` for S3, ECS Cluster, CloudWatch log group.  

---

## 3. Back-end API (FastAPI)
- [ ] Endpoint `POST /jobs` → validate URL, duration cap, rights checkbox.  
- [ ] Yt-dlp metadata probe to fetch total duration + title.  
- [ ] Write RQ job (`clip_video`) signature:  
  ```python
  clip_video(url, in_ts, out_ts, job_id)
  ```
- [ ] Endpoint `GET /jobs/{id}` → JSON status (queued|working|done|error) & presigned URL if done.  
- [ ] Prometheus metrics (`/metrics`): queue depth, job_duration_seconds, failures_total.  

---

## 4. Worker logic
- [ ] Auto-update yt-dlp on container start (`yt-dlp -U`).  
- [ ] Download source to ephemeral `/tmp`.  
- [ ] Determine if in_ts hits key-frame (ffprobe); branch:  
  - if yes → `ffmpeg -ss {in} -to {out} -c copy`  
  - if no → `ffmpeg -ss {in} -to {out} -c:v libx264 -preset veryfast -crf 18 -c:a copy` for first GOP, then `-c copy`  
- [ ] Upload result to S3 with `Content-Disposition: attachment`.  
- [ ] Generate single-use presigned URL (expiry 60 s).  
- [ ] Delete both the source and clipped file locally; push status "done".  

---

## 5. Front-end (Next.js)
- [ ] Landing page with URL input + "Start" button.  
- [ ] Fetch metadata → show video preview (react-player) + dual-handle slider (Headless UI).  
- [ ] Live timecode inputs sync with slider.  
- [ ] POST job; poll `/jobs/{id}` every 2 s or via WebSocket.  
- [ ] On "done" → trigger download, show toast "File will self-destruct after this download."  
- [ ] Error banners for >3 min trim, private link, queue-full.  
- [ ] Fully responsive breakpoints; mobile drag handles ≥ 44 px touch-target.  

---

## 6. Observability & operations
- [ ] Deploy Grafana + Prometheus via Grafana Cloud or docker-compose-monitoring.  
- [ ] Dashboards: API p95 latency, worker job duration, error rate, queue depth.  
- [ ] Alert rules → email / Slack when error rate > 5 % or queue > 20 jobs for > 2 min.  

---

## 7. Security & compliance
- [ ] Enforce HTTPS (Cloudflare flexible TLS).  
- [ ] Add CSP & CORS headers (allow only frontend origin).  
- [ ] Log user IP & URL to support DMCA takedown audits.  
- [ ] Add mandatory checkbox text:  
  *"I confirm I own or am licensed to download this video. I accept the Terms of Use."*  
- [ ] Generate and publish Terms of Use + Privacy pages.  

---

## 8. QA & release
- [ ] Unit-tests: URL validation, duration validation, presign link generator.  
- [ ] Integration test: end-to-end job (public YouTube 30 s clip) inside CI.  
- [ ] Lighthouse audit → performance ≥ 90 mobile.  
- [ ] "Smoke" checklist before every deploy:  
  - Upload & clip 15 s YouTube link (key-frame start).  
  - Upload & clip 15 s YouTube link at non-key-frame start.  
  - Confirm single download then 404 on second attempt.  

---

## 9. Deployment
- [ ] Push images to AWS ECR.  
- [ ] Create ECS service (Fargate) for api + worker with min 1 / max 5 tasks.  
- [ ] Application Load Balancer → api service (path `/`).  
- [ ] Cloudflare DNS → ALB CNAME.  
- [ ] Configure autoscaling:  
  - api: CPU > 60 %  
  - worker: Redis queue depth > 15  
- [ ] Tag release v0.1.  

---

## 10. Post-launch housekeeping
- [ ] Weekly cron job to rebuild worker image (gets latest yt-dlp).  
- [ ] Rotate S3 bucket keys quarterly.  
- [ ] Add cron Lambda → purge S3 objects older than 1 h as fallback to instant delete.  
- [ ] Collect anonymised metrics (clip durations, sources) for future capacity planning.

---

## ✅ Done
- [x] **Fix circular import in metrics package** – Moved Prometheus metrics definitions to separate module to eliminate circular dependencies.
- [x] **Set up deploy script** – Created one-command VPS deployment script with SSH automation and health checks.
- [x] **Serve Frontend via Caddy + FastAPI** – Updated deployment to properly serve the frontend UI built in Next.js as a static SPA alongside the FastAPI backend.
- [x] **End-to-End Smoke Tests** – Created comprehensive E2E test suite that verifies the complete user flow: metadata fetch → job creation → job completion → clip download. Includes automated test script and CI/CD integration.
- [x] **Line Counting Script** – Created `scripts/line_counts.sh` with cloc/wc fallback, component analysis, and cross-platform support. Shows ~3,883 total lines across backend (2,113), frontend (~800), and other components.
- [x] **DRY Deployment Infrastructure (IaC)** – Created comprehensive Infrastructure-as-Code using Terraform v1.5+ for core AWS resources (S3 bucket with lifecycle policies, IAM role with S3 permissions, optional Route53 DNS). Includes validation scripts for both Linux/macOS and Windows, comprehensive documentation, and example configurations for dev/staging/prod environments.
- [x] **S3 Cost & Usage Guardrails** – Implemented comprehensive Prometheus-based monitoring for S3 storage and egress with Alertmanager rules that fire when monthly thresholds are exceeded. Created S3 metrics exporter (`infra/monitoring/s3_metrics_exporter.py`) that fetches CloudWatch metrics and exposes `S3_STORAGE_BYTES` and `S3_EGRESS_BYTES` gauges. Added cost-guardrails alert group with `S3StorageTooHigh` (>200 GB for 12h) and `S3EgressTooHigh` (>50 GB/hour) alerts routed to Slack. Includes verification script (`infra/monitoring/test_s3_metrics.sh`) and comprehensive runbooks in monitoring documentation.

### Follow-ups
- [ ] Add pytest regression test that imports app.metrics to catch future circular-import regressions.
- [ ] Ensure deploy/memeit.service stays in sync with docker compose ports & environment.
- [ ] **CI/CD via GitHub Actions** – Automate testing and deployment pipeline.
- [ ] **Cron job for automated testing** – Set up scheduled health checks and smoke tests. 