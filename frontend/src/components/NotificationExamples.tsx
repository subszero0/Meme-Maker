'use client';

import { useState } from 'react';
import Notification, { 
  SuccessNotification, 
  ErrorNotification, 
  InfoNotification, 
  WarningNotification 
} from './Notification';

/**
 * Comprehensive examples of the unified Notification component
 * 
 * This file demonstrates all notification types, positions, and features
 * for documentation and development reference purposes.
 */
export default function NotificationExamples() {
  const [showToast, setShowToast] = useState(false);
  const [countdown, setCountdown] = useState(60);

  // Simulate countdown timer
  useState(() => {
    const interval = setInterval(() => {
      setCountdown(prev => prev > 0 ? prev - 1 : 60);
    }, 1000);
    return () => clearInterval(interval);
  });

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold mb-6">Notification Component Examples</h1>

      {/* Toast Notifications */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Toast Notifications</h2>
        <div className="space-y-4">
          <SuccessNotification 
            message="Your clip has been successfully created!" 
            position="toast"
          />
          <ErrorNotification 
            message="Failed to process video. Please try again." 
            position="toast"
          />
          <InfoNotification 
            message="Processing your video clip..." 
            position="toast"
          />
          <WarningNotification 
            message="Your clip duration exceeds 3 minutes." 
            position="toast"
          />
        </div>
      </section>

      {/* Banner Notifications */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Banner Notifications</h2>
        <div className="space-y-4">
          <Notification
            type="warning"
            title="Queue Full"
            message="The video processing queue is currently full. Please try again in a few minutes."
            position="banner"
            dismissible={true}
            onClose={() => console.log('Banner dismissed')}
          />

          <Notification
            type="error"
            title="Rate Limit Exceeded"
            message="Too many requests. Please wait before trying again."
            position="banner"
            countdown={{
              timeLeft: countdown,
              totalTime: 60,
              label: 'Retry in'
            }}
            showProgress={true}
            duration={0}
          />

          <Notification
            type="info"
            title="Processing Video"
            message="Your video is being processed. This may take a few moments."
            position="banner"
            showProgress={true}
            duration={0}
          />
        </div>
      </section>

      {/* Inline Notifications */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Inline Notifications</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Video URL</label>
            <input 
              type="url" 
              className="w-full px-3 py-2 border rounded-md" 
              placeholder="https://www.youtube.com/watch?v=..."
            />
            <ErrorNotification 
              message="Please enter a valid video URL" 
              position="inline"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Clip Duration</label>
            <input 
              type="range" 
              className="w-full" 
              min="0" 
              max="300"
            />
            <WarningNotification 
              message="Trim to three minutes or less to proceed." 
              position="inline"
            />
          </div>
        </div>
      </section>

      {/* Custom Content */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Custom Content</h2>
        <Notification
          type="success"
          message={
            <div>
              <p className="font-semibold">Clip ready!</p>
              <p className="mt-1">File will self-destruct after download.</p>
              <button className="mt-2 px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700">
                Download Now
              </button>
            </div>
          }
          position="toast"
          duration={0}
        />
      </section>

      {/* Interactive Example */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Interactive Example</h2>
        <div className="space-y-4">
          <button
            onClick={() => setShowToast(!showToast)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {showToast ? 'Hide' : 'Show'} Toast
          </button>

          {showToast && (
            <Notification
              type="info"
              message="This toast can be toggled on and off"
              position="toast"
              onClose={() => setShowToast(false)}
              data-cy="interactive-toast"
            />
          )}
        </div>
      </section>

      {/* Accessibility Features */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Accessibility Features</h2>
        <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
          <h3 className="font-medium">ARIA Roles & Live Regions</h3>
          <div className="space-y-2 text-sm">
            <p><code>success/info</code>: role="status" aria-live="polite"</p>
            <p><code>error/warning</code>: role="alert" aria-live="assertive"</p>
            <p><strong>Keyboard navigation</strong>: Dismiss buttons are focusable</p>
            <p><strong>Pause on hover/focus</strong>: Auto-dismiss pauses for screen readers</p>
            <p><strong>44×44px touch targets</strong>: All dismiss buttons meet accessibility requirements</p>
          </div>
        </div>
      </section>

      {/* Dark Mode Preview */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Dark Mode Support</h2>
        <div className="dark bg-gray-900 p-6 rounded-lg space-y-4">
          <SuccessNotification message="Success in dark mode" />
          <ErrorNotification message="Error in dark mode" />
          <InfoNotification message="Info in dark mode" />
          <WarningNotification message="Warning in dark mode" />
        </div>
      </section>

      {/* Code Examples */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Usage Examples</h2>
        <div className="bg-gray-100 p-4 rounded-lg">
          <pre className="text-sm overflow-x-auto">
{`// Basic usage
<Notification type="success" message="Operation completed!" />

// Toast notification
<SuccessNotification message="File uploaded!" position="toast" />

// Banner with countdown
<Notification
  type="error"
  title="Rate Limited"
  message="Please wait before retrying"
  position="banner"
  countdown={{ timeLeft: 30, totalTime: 60 }}
  showProgress={true}
/>

// Inline form validation
<ErrorNotification 
  message="Invalid email format" 
  position="inline" 
/>

// Custom content
<Notification
  type="info"
  message={<CustomComponent />}
  position="toast"
/>`}
          </pre>
        </div>
      </section>
    </div>
  );
} 