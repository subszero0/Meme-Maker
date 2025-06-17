# Environment Setup Guide - Frontend-New ✅

This guide explains how to configure environment variables for the frontend-new React application in different deployment scenarios.

> **🎉 SETUP COMPLETE**: Environment configuration is complete and optimized for all deployment scenarios!

## Environment Variables Reference

### Core Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` | Yes | `https://api.meme-maker.com` |
| `VITE_ENVIRONMENT` | Current environment | `development` | No | `production` |

### Application Settings

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `VITE_APP_VERSION` | Application version | `1.0.0` | No | `2.1.3` |
| `VITE_MAX_FILE_SIZE` | Max upload size (bytes) | `500000000` | No | `1000000000` |
| `VITE_MAX_CLIP_DURATION` | Max clip length (seconds) | `180` | No | `300` |

### Feature Flags

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `VITE_ENABLE_ANALYTICS` | Enable tracking | `false` | No | `true` |
| `VITE_ENABLE_SENTRY` | Enable error reporting | `false` | No | `true` |
| `VITE_ENABLE_PWA` | Progressive Web App | `false` | No | `true` |

### Development Settings

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `VITE_LOG_LEVEL` | Logging level | `info` | No | `debug` |
| `VITE_API_TIMEOUT` | Request timeout (ms) | `30000` | No | `60000` |
| `VITE_ENABLE_DEVTOOLS` | React Query DevTools | `true` | No | `false` |

## Environment File Setup

### 1. Local Development

Create `.env.local` in the `frontend-new/` directory:

```bash
# .env.local - Local development configuration

# API Configuration  
VITE_API_BASE_URL=http://localhost:8000

# Environment
VITE_ENVIRONMENT=development
VITE_LOG_LEVEL=debug

# Application Settings
VITE_APP_VERSION=dev
VITE_MAX_FILE_SIZE=500000000
VITE_MAX_CLIP_DURATION=180

# Feature Flags (development)
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_SENTRY=false
VITE_ENABLE_PWA=false
VITE_ENABLE_DEVTOOLS=true

# Development Settings
VITE_API_TIMEOUT=30000
```

### 2. Staging Environment

Create `.env.staging`:

```bash
# .env.staging - Staging environment

# API Configuration
VITE_API_BASE_URL=https://staging-api.meme-maker.com

# Environment
VITE_ENVIRONMENT=staging
VITE_LOG_LEVEL=info

# Application Settings
VITE_APP_VERSION=staging
VITE_MAX_FILE_SIZE=500000000
VITE_MAX_CLIP_DURATION=180

# Feature Flags (staging)
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_SENTRY=true
VITE_ENABLE_PWA=true
VITE_ENABLE_DEVTOOLS=false

# Performance Settings
VITE_API_TIMEOUT=45000
```

### 3. Production Environment

Create `.env.production`:

```bash
# .env.production - Production environment

# API Configuration
VITE_API_BASE_URL=https://api.meme-maker.com

# Environment
VITE_ENVIRONMENT=production
VITE_LOG_LEVEL=error

# Application Settings
VITE_APP_VERSION=1.0.0
VITE_MAX_FILE_SIZE=500000000
VITE_MAX_CLIP_DURATION=180

# Feature Flags (production)
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_SENTRY=true
VITE_ENABLE_PWA=true
VITE_ENABLE_DEVTOOLS=false

# Performance Settings
VITE_API_TIMEOUT=60000
```

## Configuration Usage

### In TypeScript Code

```typescript
// src/config/env.ts
export const config = {
  // API Configuration
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',
  
  // Application Settings
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
  maxFileSize: Number(import.meta.env.VITE_MAX_FILE_SIZE) || 500000000,
  maxClipDuration: Number(import.meta.env.VITE_MAX_CLIP_DURATION) || 180,
  
  // Feature Flags
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  enableSentry: import.meta.env.VITE_ENABLE_SENTRY === 'true',
  enablePWA: import.meta.env.VITE_ENABLE_PWA === 'true',
  
  // Development Settings
  logLevel: import.meta.env.VITE_LOG_LEVEL || 'info',
  apiTimeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  enableDevtools: import.meta.env.VITE_ENABLE_DEVTOOLS !== 'false',
} as const;

// Type-safe environment check
export const isDevelopment = config.environment === 'development';
export const isStaging = config.environment === 'staging';
export const isProduction = config.environment === 'production';
```

### In Components

```typescript
import { config, isDevelopment } from '@/config/env';

export function ApiService() {
  const apiUrl = config.apiBaseUrl;
  const timeout = config.apiTimeout;
  
  // Development-only logging
  if (isDevelopment) {
    console.log('API Base URL:', apiUrl);
  }
  
  return (
    <div>
      App Version: {config.appVersion}
      {config.enableAnalytics && <Analytics />}
    </div>
  );
}
```

## Build Configuration

### Vite Environment Modes

```bash
# Development mode
npm run dev  # Uses .env.local and .env.development

# Build for staging
vite build --mode staging  # Uses .env.staging

# Build for production  
vite build --mode production  # Uses .env.production
```

### Package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "build:staging": "vite build --mode staging",
    "build:production": "vite build --mode production",
    "preview": "vite preview"
  }
}
```

## Docker Configuration

### Development Docker

```dockerfile
# Dockerfile.dev
FROM node:20-alpine
WORKDIR /app

# Environment variables can be passed at runtime
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_ENVIRONMENT=development

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_ENVIRONMENT=$VITE_ENVIRONMENT

COPY package*.json ./
RUN npm install

COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

### Production Docker

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app

# Build-time environment variables
ARG VITE_API_BASE_URL
ARG VITE_ENVIRONMENT=production
ARG VITE_APP_VERSION

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_ENVIRONMENT=$VITE_ENVIRONMENT
ENV VITE_APP_VERSION=$VITE_APP_VERSION

COPY package*.json ./
RUN npm ci --only=production=false

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Environment Validation

### Runtime Validation

```typescript
// src/config/validation.ts
export function validateEnvironment() {
  const required = [
    'VITE_API_BASE_URL',
  ];

  const missing = required.filter(key => !import.meta.env[key]);
  
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }

  // Validate API URL format
  const apiUrl = import.meta.env.VITE_API_BASE_URL;
  if (!apiUrl.startsWith('http://') && !apiUrl.startsWith('https://')) {
    throw new Error('VITE_API_BASE_URL must start with http:// or https://');
  }

  // Validate numeric values
  const maxFileSize = Number(import.meta.env.VITE_MAX_FILE_SIZE);
  if (isNaN(maxFileSize) || maxFileSize <= 0) {
    throw new Error('VITE_MAX_FILE_SIZE must be a positive number');
  }
}

// Call during app initialization
validateEnvironment();
```

## Security Considerations

### Sensitive Data

⚠️ **Important**: All `VITE_*` variables are exposed in the client-side bundle.

**Never include**:
- API keys or secrets
- Database credentials  
- Private configuration
- User data

**Safe to include**:
- API endpoints (public)
- Feature flags
- UI configuration
- Public settings

### Environment File Security

```bash
# .gitignore
.env.local
.env.development.local
.env.staging.local
.env.production.local

# Keep these files
.env.example
.env.staging
.env.production
```

## Troubleshooting

### Common Issues

1. **Variables not loading**
   - Ensure variables start with `VITE_`
   - Restart dev server after changes
   - Check file location (`frontend-new/` directory)

2. **Build-time vs Runtime**
   - Vite embeds variables at build time
   - Changes require rebuild
   - Use `import.meta.env` not `process.env`

3. **Docker environment**
   - Pass variables as ARG/ENV in Dockerfile
   - Use docker-compose environment section
   - Rebuild image after environment changes

### Debugging

```typescript
// View all environment variables (development only)
if (isDevelopment) {
  console.table(import.meta.env);
}

// Check specific variable
console.log('API URL:', import.meta.env.VITE_API_BASE_URL);
```

### Testing Environment Setup

```typescript
// src/test/setup.ts
import { beforeAll } from 'vitest';

beforeAll(() => {
  // Set test environment variables
  Object.assign(import.meta.env, {
    VITE_API_BASE_URL: 'http://localhost:8000',
    VITE_ENVIRONMENT: 'test',
    VITE_ENABLE_ANALYTICS: 'false',
  });
});
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: |
          cd frontend-new
          npm ci
          
      - name: Build for production
        run: |
          cd frontend-new
          npm run build:production
        env:
          VITE_API_BASE_URL: ${{ secrets.API_BASE_URL }}
          VITE_APP_VERSION: ${{ github.sha }}
```

### Docker Compose

```yaml
# docker-compose.prod.yml
services:
  frontend:
    build:
      context: ./frontend-new
      args:
        VITE_API_BASE_URL: ${API_BASE_URL}
        VITE_ENVIRONMENT: production
        VITE_APP_VERSION: ${APP_VERSION}
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
```

This environment setup provides flexible, secure, and maintainable configuration management for all deployment scenarios. 