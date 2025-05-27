# Meme Maker Frontend Setup

This document contains the complete setup instructions for the Next.js 14 + TypeScript frontend.

## 1. Full Command Sequence

```bash
# Navigate to project root
cd "/c/Users/Vivek Subramanian/Desktop/Meme Maker"

# Create frontend directory
mkdir frontend
cd frontend

# Create Next.js 14 project with TypeScript and Tailwind
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --yes

# Install additional dependencies
npm install @headlessui/react @heroicons/react react-player

# Install development dependencies
npm install -D autoprefixer

# Create component directories
mkdir -p src/components/ui src/components/video src/lib

# Start development server
npm run dev
```

## 2. Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/
│   │   │   ├── url-input.tsx
│   │   │   └── time-range-slider.tsx
│   │   └── video/
│   │       └── video-preview.tsx
│   └── lib/
├── public/
├── .nvmrc
├── tailwind.config.ts
├── postcss.config.js
├── next.config.ts
├── tsconfig.json
└── package.json
```

## 3. Key Features Implemented

### Components
- **UrlInput**: Form component for pasting video URLs
- **VideoPreview**: React Player wrapper for video preview
- **TimeRangeSlider**: Dual-handle slider for video trimming
- **HomePage**: Main landing page with complete user flow

### Validation
- 3-minute clip duration limit
- Rights confirmation checkbox
- URL validation (client-side)
- Mobile-responsive design (44px+ touch targets)

### User Flow
1. Paste video URL (YouTube, Instagram, Facebook, Threads, Reddit)
2. Video metadata fetched and preview shown
3. Dual-handle slider for precise trimming
4. Live timecode display (hh:mm:ss.mmm format)
5. Rights confirmation required
6. Download button with validation

## 4. Technologies Used

- **Next.js 15.3.2** with App Router
- **React 19** with TypeScript
- **Tailwind CSS 4** with JIT mode
- **Headless UI** for accessible components
- **React Player** for video preview
- **Heroicons** for icons
- **Node 20 LTS** (specified in .nvmrc)

## 5. Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

## 6. Development Server

The app runs on `http://localhost:3000` by default with Turbopack enabled for faster development builds.

## 7. Next Steps

- [ ] Connect to FastAPI backend (localhost:8000)
- [ ] Implement API calls for video metadata
- [ ] Add job status polling
- [ ] Implement download functionality
- [ ] Add error handling and user feedback
- [ ] Add loading states and progress indicators 