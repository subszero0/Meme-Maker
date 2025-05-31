# Meme Maker Frontend

A Next.js-based web application for trimming and downloading video clips from social media platforms.

## Features

- 🎬 **URL Input**: Paste video URLs from YouTube, Instagram, Facebook, Threads, or Reddit
- ✂️ **Precision Trimming**: Dual-handle slider + timestamp inputs (max 3 minutes)
- 📱 **Mobile-First**: Responsive design works at 360px width with 44px touch targets
- 📋 **Auto-Copy**: Automatically copies download link to clipboard
- 🎯 **Real-Time Preview**: Live video preview with react-player
- ⚡ **Fast Polling**: 3-second status updates during processing

## Quick Start

### Development Mode

```bash
# Install dependencies
npm install

# Start development server (requires backend running on port 8000)
npm run dev

# Open http://localhost:3000
```

### Production Build

```bash
# Build static export
npm run build

# Output goes to ./out/ directory
```

## Environment Variables

Create `.env.local` for development:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Integration with Backend

The frontend is designed to be served by the FastAPI backend container in production:

1. **Static Export**: `npm run build` creates static files in `./out/`
2. **Backend Integration**: Backend Dockerfile copies these files to `/app/static`
3. **SPA Routing**: Backend serves `index.html` for all non-API routes
4. **API Proxying**: All `/api/v1/*` requests go to FastAPI

## Bundle Size

Current bundle size: **197kB** (well under 250kB gzipped requirement)

## Mobile Optimization

- **Touch Targets**: Slider handles are 44px × 44px for mobile
- **Responsive Design**: Works at 360px width minimum
- **Dark Mode**: Full dark mode support

## Testing

```bash
# Unit tests
npm test

# End-to-end tests
npm run cypress:run

# Coverage report
npm run test:coverage
```

## API Integration

The frontend integrates with the backend API:

- `POST /api/v1/metadata` - Fetch video metadata
- `POST /api/v1/jobs` - Create clip job
- `GET /api/v1/jobs/{id}` - Poll job status (every 3 seconds)

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js app router
│   │   └── page.tsx
│   ├── components/       # React components
│   │   ├── TrimPanel.tsx     # Dual-handle slider & preview
│   │   ├── URLInputPanel.tsx # URL input with validation
│   │   ├── DownloadModal.tsx # Auto-copy & download
│   │   └── ...
│   ├── hooks/            # Custom React hooks
│   │   └── useJobPoller.ts   # 3-second job polling
│   └── lib/              # Utilities
│       ├── api.ts            # Backend API integration
│       └── formatTime.ts     # Time formatting helpers
├── public/               # Static assets
└── out/                  # Static build output
```

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
