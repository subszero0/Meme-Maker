'use client';

import { useState } from 'react';
import FeedbackWidget from './FeedbackWidget';

export default function Footer() {
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);

  const handleFeedbackClick = () => {
    setIsFeedbackOpen(true);
  };

  const handleFeedbackClose = () => {
    setIsFeedbackOpen(false);
  };

  return (
    <>
      <footer className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
        <div className="text-center space-y-3">
          <div className="text-sm text-text-secondary dark:text-gray-300">
            <p>Maximum clip length: **30 minutes** · 20 jobs per hour · Files self-destruct after download</p>
            <p className="text-xs mt-1 text-text-tertiary dark:text-gray-400">
              Rate limits: 10 requests per minute · 20 job creations per hour
            </p>
          </div>
          
          <div className="flex justify-center space-x-6 text-sm">
            <a
              href="/terms"
              target="_blank"
              rel="noopener noreferrer"
              className="text-link-primary hover:text-link-hover dark:text-link-dark dark:hover:text-link-dark-hover transition-colors"
            >
              Terms of Use
            </a>
            <span className="text-gray-300 dark:text-gray-600">•</span>
            <a
              href="/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-link-primary hover:text-link-hover dark:text-link-dark dark:hover:text-link-dark-hover transition-colors"
            >
              Privacy Policy
            </a>
            <span className="text-gray-300 dark:text-gray-600">•</span>
            <button
              type="button"
              onClick={handleFeedbackClick}
              className="text-link-primary hover:text-link-hover dark:text-link-dark dark:hover:text-link-dark-hover transition-colors underline decoration-dotted underline-offset-2"
              data-cy="feedback-link"
            >
              Feedback
            </button>
          </div>
          
          <div className="text-xs text-text-secondary dark:text-gray-400">
            <p>© 2024 Meme Maker • Free video clipping tool</p>
          </div>
        </div>
      </footer>

      <FeedbackWidget 
        isOpen={isFeedbackOpen} 
        onClose={handleFeedbackClose} 
      />
    </>
  );
} 