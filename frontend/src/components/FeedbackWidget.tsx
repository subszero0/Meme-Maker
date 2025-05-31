'use client';

import { Fragment, useEffect, useCallback } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface FeedbackWidgetProps {
  isOpen: boolean;
  onClose: () => void;
}

// Google Form URL for the feedback survey
// This form contains 5 questions: satisfaction rating, URL ease-of-use, slider intuitiveness, error encounters, and open feedback
const FEEDBACK_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSdV8JzQ2nR5K4WxY9Hg7TqPbN1uLmF3XvC9A6E0ZzRtOp8IkJ/viewform?embedded=true';

// Type for Google Analytics gtag function
interface GtagFunction {
  (command: string, action: string, parameters?: Record<string, unknown>): void;
}

/**
 * @ux @analytics 
 * Feedback widget with embedded Google Forms survey for collecting qualitative user feedback.
 * Tracks open/submit events via analytics and maintains ARIA compliance.
 */
export default function FeedbackWidget({ isOpen, onClose }: FeedbackWidgetProps) {
  
  // Track feedback modal open event
  useEffect(() => {
    if (isOpen) {
      // Analytics: Track feedback modal opened
      if (typeof window !== 'undefined' && 'gtag' in window) {
        (window.gtag as GtagFunction)('event', 'feedback_open', {
          event_category: 'engagement',
          event_label: 'feedback_modal'
        });
      }
      
      // Console tracking for development
      console.log('Analytics: feedback_open event fired');
    }
  }, [isOpen]);

  // Handle iframe load to track form submissions
  const handleIframeLoad = () => {
    // Note: Due to cross-origin restrictions, we can't directly detect form submission
    // This is a placeholder for when the iframe loads
    console.log('Feedback form loaded');
  };

  // Track when user closes modal (assumption: they may have submitted)
  const handleClose = useCallback(() => {
    // Analytics: Track potential feedback submission 
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window.gtag as GtagFunction)('event', 'feedback_submit', {
        event_category: 'engagement', 
        event_label: 'feedback_modal_closed'
      });
    }
    
    console.log('Analytics: feedback_submit event fired (modal closed)');
    onClose();
  }, [onClose]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, handleClose]);

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-50" />
        </Transition.Child>
        
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel 
                className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 text-left align-middle shadow-xl transition-all"
                role="dialog"
                aria-modal="true"
                aria-labelledby="feedback-title"
                aria-describedby="feedback-description"
                data-cy="feedback-modal"
              >
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                  <div>
                    <Dialog.Title 
                      id="feedback-title"
                      className="text-lg font-medium leading-6 text-gray-900 dark:text-white"
                    >
                      Share Your Feedback
                    </Dialog.Title>
                    <p 
                      id="feedback-description"
                      className="text-sm text-gray-600 dark:text-gray-400 mt-1"
                    >
                      Help us improve Meme Maker with your thoughts and suggestions
                    </p>
                  </div>
                  <button
                    type="button"
                    className="inline-flex items-center justify-center w-11 h-11 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 rounded-md transition-colors"
                    onClick={handleClose}
                    aria-label="Close feedback dialog"
                    data-cy="close-feedback-button"
                  >
                    <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                  </button>
                </div>
                
                <div className="p-0">
                  <iframe
                    src={FEEDBACK_FORM_URL}
                    width="100%"
                    height="600"
                    frameBorder="0"
                    marginHeight={0}
                    marginWidth={0}
                    title="Meme Maker Feedback Survey"
                    onLoad={handleIframeLoad}
                    allow="clipboard-read; clipboard-write"
                    className="border-0 rounded-b-2xl bg-white dark:bg-gray-100"
                    data-cy="feedback-iframe"
                  >
                    <p className="text-center p-6 text-gray-600 dark:text-gray-400">
                      Loading feedback form... 
                      <a 
                        href={FEEDBACK_FORM_URL}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline ml-1"
                      >
                        Open in new tab
                      </a>
                    </p>
                  </iframe>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
} 