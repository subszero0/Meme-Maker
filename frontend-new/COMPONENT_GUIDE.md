# Component Guide - Frontend-New ✅

This guide documents the main components in the frontend-new React application and how they work together.

> **🎉 ALL COMPONENTS INTEGRATED**: All components are now fully integrated with the backend and production-ready!

## Architecture Overview

The frontend-new follows a modern React architecture with:
- **Functional Components** with React hooks
- **ShadCN UI** components for consistent design
- **TypeScript** for type safety
- **React Query** for server state management
- **Zustand** for client state management

## Component Hierarchy

```
App
├── ErrorBoundary
├── ToastProvider  
└── Index (Main Page)
    ├── UrlInput
    ├── VideoPlayer
    ├── Timeline
    ├── ResolutionSelector
    ├── LoadingAnimation
    └── SharingOptions
```

## Core Components

### 1. App Component
**Location**: `src/App.tsx`

Main application component that sets up providers and routing.

```typescript
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <ToastProvider>
          <div className="min-h-screen bg-background">
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </ToastProvider>
      </ErrorBoundary>
      {isDevelopment && <ReactQueryDevtools />}
    </QueryClientProvider>
  );
}
```

**Features**:
- React Query provider for API state management
- Error boundary for graceful error handling
- Toast notifications system
- Development tools in development mode

### 2. ErrorBoundary Component
**Location**: `src/components/ErrorBoundary.tsx`

Catches JavaScript errors in the component tree and displays fallback UI.

```typescript
interface Props {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
}

export function ErrorBoundary({ children, fallback: Fallback }: Props) {
  // Error boundary implementation
}
```

**Features**:
- Catches and logs unhandled errors
- Provides custom fallback UI
- Reset functionality to recover from errors
- Integrates with error reporting services

### 3. UrlInput Component
**Location**: `src/components/UrlInput.tsx`

Handles video URL input and validation.

```typescript
interface UrlInputProps {
  onSubmit: (url: string) => void;
  isLoading?: boolean;
  error?: string;
}

export function UrlInput({ onSubmit, isLoading, error }: UrlInputProps) {
  // URL input implementation
}
```

**Features**:
- URL validation (YouTube, Instagram, etc.)
- Loading states during metadata fetching
- Error message display
- Auto-focus and keyboard shortcuts
- Paste detection and cleanup

**Supported Platforms**:
- YouTube (youtube.com, youtu.be)
- Instagram (instagram.com)
- Facebook (facebook.com)
- Threads (threads.net)
- Reddit (reddit.com)

### 4. VideoPlayer Component
**Location**: `src/components/VideoPlayer.tsx`

Displays video preview with playback controls.

```typescript
interface VideoPlayerProps {
  url?: string;
  thumbnail?: string;
  title?: string;
  duration?: number;
  currentTime?: number;
  onTimeUpdate?: (time: number) => void;
}

export function VideoPlayer({ 
  url, 
  thumbnail, 
  title, 
  duration, 
  currentTime, 
  onTimeUpdate 
}: VideoPlayerProps) {
  // Video player implementation
}
```

**Features**:
- React Player integration for multiple platforms
- Thumbnail display before video loads
- Custom controls overlay
- Time synchronization with timeline
- Responsive design for mobile
- Keyboard controls (space, arrow keys)

### 5. Timeline Component
**Location**: `src/components/Timeline.tsx`

Interactive timeline for selecting video trim points.

```typescript
interface TimelineProps {
  duration: number;
  startTime: number;
  endTime: number;
  currentTime?: number;
  maxDuration?: number; // 180 seconds default
  onRangeChange: (start: number, end: number) => void;
  onCurrentTimeChange?: (time: number) => void;
}

export function Timeline({
  duration,
  startTime,
  endTime,
  currentTime,
  maxDuration = 180,
  onRangeChange,
  onCurrentTimeChange
}: TimelineProps) {
  // Timeline implementation
}
```

**Features**:
- Dual-handle range slider for start/end times
- Current playback position indicator
- Time format display (MM:SS)
- Maximum clip duration enforcement (3 minutes)
- Keyboard navigation
- Touch support for mobile
- Visual feedback for invalid ranges

### 6. ResolutionSelector Component
**Location**: `src/components/ResolutionSelector.tsx`

Allows users to select video quality/format.

```typescript
interface Format {
  format_id: string;
  height: number;
  fps?: number;
  vcodec: string;
  acodec: string;
  filesize?: number;
}

interface ResolutionSelectorProps {
  formats: Format[];
  selectedFormatId: string;
  onFormatChange: (formatId: string) => void;
}

export function ResolutionSelector({
  formats,
  selectedFormatId,
  onFormatChange
}: ResolutionSelectorProps) {
  // Resolution selector implementation
}
```

**Features**:
- Displays available video formats from metadata
- Quality badges (HD, 4K, etc.)
- File size estimates when available
- Codec information (H.264, VP9, etc.)
- Best quality auto-selection
- Responsive dropdown menu

### 7. LoadingAnimation Component
**Location**: `src/components/LoadingAnimation.tsx`

Shows processing progress during video processing.

```typescript
interface LoadingAnimationProps {
  progress: number; // 0-100
  stage: string;
  isVisible: boolean;
}

export function LoadingAnimation({
  progress,
  stage,
  isVisible
}: LoadingAnimationProps) {
  // Loading animation implementation
}
```

**Features**:
- Animated progress bar
- Stage descriptions ("Downloading", "Processing", "Uploading")
- Estimated time remaining
- Cancel functionality
- Smooth animations and transitions
- Mobile-optimized design

**Processing Stages**:
1. "Initializing" - Job creation
2. "Downloading" - Video download from source
3. "Processing" - Video trimming and encoding
4. "Uploading" - File upload to storage
5. "Completed" - Ready for download

### 8. SharingOptions Component
**Location**: `src/components/SharingOptions.tsx`

Provides download and sharing functionality.

```typescript
interface SharingOptionsProps {
  downloadUrl: string;
  filename: string;
  filesize: number;
  expiresAt: string;
}

export function SharingOptions({
  downloadUrl,
  filename,
  filesize,
  expiresAt
}: SharingOptionsProps) {
  // Sharing options implementation
}
```

**Features**:
- Direct download button
- Copy link functionality
- File information display (size, expiration)
- Social sharing buttons
- QR code generation for mobile sharing
- Expiration countdown timer

## Utility Components

### UI Components (ShadCN)
**Location**: `src/components/ui/`

Reusable UI components built on Radix UI primitives:

- **Button**: `button.tsx` - Various button styles and sizes
- **Input**: `input.tsx` - Form input with validation states
- **Toast**: `toast.tsx` - Notification system
- **Progress**: `progress.tsx` - Progress bars and indicators
- **Dialog**: `dialog.tsx` - Modal dialogs
- **Select**: `select.tsx` - Dropdown selections
- **Slider**: `slider.tsx` - Range and value sliders
- **Alert**: `alert.tsx` - Alert messages

### Custom Hooks

#### useAppState
**Location**: `src/hooks/useAppState.ts`

Manages global application state.

```typescript
export type AppPhase = 
  | 'input'           // URL input
  | 'loading'         // Metadata loading
  | 'video-loaded'    // Video ready for trimming
  | 'processing'      // Job processing
  | 'completed'       // Download ready
  | 'error';          // Error state

export function useAppState() {
  const [phase, setPhase] = useState<AppPhase>('input');
  const [url, setUrl] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  // ... state management logic
}
```

#### useApi
**Location**: `src/hooks/useApi.ts`

Custom hooks for API integration (documented in API_INTEGRATION.md).

## State Management

### Application Flow

1. **URL Input Phase**
   - User enters video URL
   - URL validation occurs
   - Metadata fetching triggered

2. **Metadata Loading Phase**
   - Loading animation shown
   - API call to `/metadata` endpoint
   - Error handling for invalid URLs

3. **Video Loaded Phase**
   - Video player displays with thumbnail
   - Timeline shows full duration
   - Resolution selector populated
   - User can adjust trim points

4. **Processing Phase**
   - Job creation API call
   - Real-time progress updates
   - Cancel functionality available
   - Progress visualization

5. **Completed Phase**
   - Download link ready
   - Sharing options available
   - File information displayed
   - Option to start new clip

### Error States

Each phase can transition to error state:
- **Network errors**: Retry functionality
- **Invalid URLs**: Clear error messages
- **Processing failures**: Detailed error info
- **Timeout errors**: Automatic retry

## Styling and Theming

### Tailwind CSS Classes
The application uses Tailwind CSS with custom design tokens:

```css
/* Custom CSS variables */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96%;
  /* ... more variables */
}
```

### Responsive Design
All components are mobile-first responsive:

```typescript
// Example responsive classes
<div className="w-full max-w-md mx-auto px-4 sm:max-w-lg md:max-w-2xl lg:max-w-4xl">
  <Button className="w-full sm:w-auto">
    Process Video
  </Button>
</div>
```

### Dark Mode Support
Components support system preference dark mode:

```typescript
// Dark mode variants
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  Content
</div>
```

## Testing

### Component Testing
Each component includes comprehensive tests:

```typescript
// Example test structure
describe('UrlInput', () => {
  test('validates YouTube URLs correctly', () => {
    // Test implementation
  });

  test('shows error for invalid URLs', () => {
    // Test implementation
  });

  test('handles paste events', () => {
    // Test implementation
  });
});
```

### Integration Testing
Components are tested together in realistic user workflows:

```typescript
// Example integration test
test('complete video processing workflow', async () => {
  // 1. Enter URL
  // 2. Wait for metadata
  // 3. Adjust trim points
  // 4. Select quality
  // 5. Process video
  // 6. Download result
});
```

## Best Practices

### Component Organization
- Keep components small and focused
- Use TypeScript interfaces for props
- Include proper error boundaries
- Implement loading states
- Add accessibility features

### Performance
- Use React.memo for expensive components
- Implement proper key props for lists
- Lazy load non-critical components
- Optimize bundle size with code splitting

### Accessibility
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Color contrast compliance
- Focus management

This component architecture provides a maintainable, scalable, and user-friendly video processing application.
