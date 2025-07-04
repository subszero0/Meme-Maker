# Meme Maker

A web application for creating and processing video clips from various platforms.

## Features

- Extract clips from video URLs
- Trim video segments
- Download processed clips
- Modern web interface
- Local storage for fast processing

## Quick Start

For deployment instructions, see:
- `DEPLOYMENT_QUICK_START.md` - Deploy in 10 minutes
- `live-deployment-lightsail.md` - Complete setup guide
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist

## Architecture

- **Frontend**: React/Vite application with nginx
- **Backend**: FastAPI with async processing
- **Storage**: Local filesystem (Lightsail instance)
- **Queue**: Redis for job management
- **Deployment**: Docker Compose on Amazon Lightsail

## Status

✅ **Production Ready** - Deployed on Lightsail with local storage

<!-- Deployment trigger: nginx routing fixed, workflows cleaned -->

< ! - -   T e s t   d e p l o y m e n t   0 6 / 2 4 / 2 0 2 5   0 0 : 2 9 : 5 3   - - > 
 
 < ! - -   R e - t r i g g e r i n g   d e p l o y m e n t   a f t e r   S S H   k e y   f i x   - - > 
 
 < ! - -   P i p e l i n e   t e s t   0 6 / 2 4 / 2 0 2 5   0 3 : 1 0 : 3 2   - - > 
 
 