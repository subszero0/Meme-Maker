# Meme Maker – Product Requirements Document (PRD)  
**Version 0.4 – frozen scope**

---

## 1 · Product summary  

> **Paste an Instagram, Facebook, Threads, Reddit or YouTube link → drag In/Out → download up to 3 min, loss-free, no signup, file self-destructs after download.**

---

## 2 · Scope (MVP)  

| Axis | Decision |
|------|----------|
| **Supported sources** | YouTube, Instagram, Facebook (public videos & Reels), Threads, Reddit |
| **Clip-length cap** | ≤ 3 minutes (enforced client & server side) |
| **Accounts / history** | 100 % anonymous; no login, no stored clip history |
| **Monetisation** | Free-only MVP (no ads, no paywall) |
| **Output** | Container-copy – keep original resolution / fps / codec / container; re-encode only the first GOP if required |
| **Retention** | Single-use presigned URL; rendered file deleted immediately after a successful download (HTTP 200) |
| **Concurrency budget** | 20 simultaneous jobs |
| **Mobile** | Responsive web app; Android wrapper deferred |
| **Legal stance** | "Tool vendor" – user must tick *"I have the right to download this content"* for every job |

---

## 3 · User flow  

### 3.1 Paste  
* User pastes a public video URL.  
* Back-end validates the link and fetches metadata (title, duration, resolutions).

### 3.2 Trim  
* Dual-handle timeline slider **and** exact `hh:mm:ss.mmm` input boxes.  
* Live muted preview updates while scrubbing.  
* Clip-length validator blocks selections over 3 min.

### 3.3 Render  
* Command: `ffmpeg -ss {in} -to {out} -c copy`.  
* If IN-point is not a key-frame, back-end re-encodes only the first GOP, then continues `-c copy`.

### 3.4 Download & cleanup  
* Browser polls (or uses WebSocket) for job status.  
* When ready, server returns a **single-use presigned S3 link**.  
* Object is deleted immediately after the first successful 200 response; job record removed.

---

## 4 · Error states & UX copy  

| Condition | User message |
|-----------|--------------|
| Selection > 3 min | "Trim to three minutes or less to proceed." |
| Private / geo-blocked video | "We can't access this URL – is the video public?" |
| Rights checkbox unticked | "Please confirm you have the right to download this video." |
| Worker queue full (> 20 jobs) | "Busy right now. Try again in a minute." |

---

## 5 · Non-functional requirements  

| Category | Target |
|----------|--------|
| **Latency** | ≤ 30 s wall-time for a 3 min 1080 p clip on a 50 Mbps connection |
| **Throughput** | 20 concurrent jobs without performance degradation; autoscale on CPU / queue length |
| **Security** | TLS everywhere; signed URLs; no PII stored |
| **Observability** | Prometheus metrics (queue depth, median render time, failure count); Grafana dashboard |
| **Cost guard-rail** | Transient storage ≤ 200 GB; egress ≤ 50 GB / month; infra budget < ₹10 k / month |

---

## 6 · Technical architecture  

```text
Browser → FastAPI (Python) → Redis queue → Worker (yt-dlp + FFmpeg) → S3
   ↑                                            │
   └────────────── single-use presigned URL ←───┘
```

**Front-end:** Next.js / React / TypeScript, Tailwind CSS, Headless-UI slider, react-player for preview.

**API / gateway:** FastAPI (Python 3.12) in Docker.

**Task queue:** Redis + RQ.

**Workers:** Alpine container bundling latest yt-dlp (auto-updated) and FFmpeg; residential proxy rotation for resilience.

**Storage:** AWS S3 with a fallback lifecycle rule "delete after 1 h".

**CDN & TLS:** Cloudflare free tier (egress minimal thanks to self-destructing files).

**Observability:** Prometheus exporter in FastAPI; Grafana dashboard.

---

## 7 · Key-frame fallback – why it exists

Video streams contain key-frames (full images) followed by many delta-frames (only changes).

Cutting on a delta-frame causes playback glitches because the initial reference frame is missing.

The worker therefore re-encodes only the first group-of-pictures (≈ 1–2 s) so the very first frame of the clip is a key-frame, then copies the rest loss-lessly.

Extra CPU cost ≈ 0.3 s per job; quality and file size remain virtually unchanged.

---

## 8 · Stack overview

| Layer | Technology |
|-------|------------|
| **Front-end** | Next.js (React), Tailwind CSS, Headless-UI slider |
| **Back-end** | FastAPI (Python) |
| **Download engine** | yt-dlp + FFmpeg |
| **Queue** | Redis + RQ |
| **Storage** | AWS S3 + presigned URLs |
| **CDN & TLS** | Cloudflare |
| **Observability** | Prometheus + Grafana | 