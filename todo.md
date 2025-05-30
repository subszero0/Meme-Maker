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
- [ ] Provision **AWS**: S3 bucket (`clip-files-dev`), an IAM role with presign permissions.  
- [ ] Terraform (or CloudFormation) files in `infra/` for S3, ECS Cluster, CloudWatch log group.  

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

### Follow-ups
- [ ] Add pytest regression test that imports app.metrics to catch future circular-import regressions.
- [ ] Ensure deploy/memeit.service stays in sync with docker compose ports & environment. 