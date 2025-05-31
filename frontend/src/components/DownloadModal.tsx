'use client';

import { Fragment, useEffect, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { motion } from 'framer-motion';
import { XMarkIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';
import { useToast } from './ToastProvider';

interface DownloadModalProps {
  url: string;
  onClose: () => void;
}

export default function DownloadModal({ url, onClose }: DownloadModalProps) {
  const { pushToast } = useToast();

  // Auto-copy URL to clipboard when modal opens
  useEffect(() => {
    const copyToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(url);
        pushToast({
          type: 'success',
          message: 'Download link copied to clipboard!'
        });
      } catch (error) {
        console.warn('Failed to copy to clipboard:', error);
      }
    };

    copyToClipboard();
  }, [url, pushToast]);

  const handleDownload = () => setTimeout(onClose, 100);

  const handleCopyAgain = async () => {
    try {
      await navigator.clipboard.writeText(url);
      pushToast({
        type: 'success',
        message: 'Link copied again!'
      });
    } catch (error) {
      pushToast({
        type: 'error',
        message: 'Failed to copy link'
      });
    }
  };

  return (
    <Transition show as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
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
                as={motion.div}
                className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 text-left align-middle shadow-xl transition-all"
              >
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
                    Clip ready!
                  </Dialog.Title>
                  <button
                    type="button"
                    className="inline-flex items-center justify-center w-11 h-11 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 rounded-md transition-colors"
                    onClick={onClose}
                    aria-label="Close dialog"
                    data-cy="close-button"
                  >
                    <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                  </button>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                  File will self-destruct after this download. Link copied to clipboard automatically.
                </p>
                <div className="flex space-x-3">
                  <a
                    href={url} download rel="noopener noreferrer"
                    onClick={handleDownload} data-testid="download-btn"
                    data-cy="download-button"
                    className="flex-1 inline-flex justify-center items-center min-h-[44px] px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500 transition-colors"
                  >
                    Download Now
                  </a>
                  <button
                    type="button" 
                    onClick={handleCopyAgain}
                    data-cy="copy-button"
                    className="inline-flex justify-center items-center min-w-[44px] min-h-[44px] px-3 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500 transition-colors"
                    title="Copy link again"
                  >
                    <ClipboardDocumentIcon className="h-4 w-4" />
                  </button>
                  <button
                    type="button" onClick={onClose}
                    data-cy="close-modal-button"
                    className="inline-flex justify-center items-center min-h-[44px] px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
} 