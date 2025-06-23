import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import type { FC, PropsWithChildren } from "react";
import ToastProvider from "@/components/ToastProvider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Clip Downloader - Video Trimming Tool",
  description:
    "Trim and download video clips from social media platforms instantly",
};

const AppShell: FC<PropsWithChildren> = ({ children }) => {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Suppress common browser extension errors
              window.addEventListener('error', function(e) {
                // Suppress RegisterClientLocalizationsError from browser extensions
                if (e.error && e.error.name === 'RegisterClientLocalizationsError') {
                  e.preventDefault();
                  return false;
                }
                // Suppress connection errors from browser extensions
                if (e.error && e.error.message && e.error.message.includes('Could not establish connection')) {
                  e.preventDefault();
                  return false;
                }
              });
              
              // Suppress unhandled promise rejections from browser extensions
              window.addEventListener('unhandledrejection', function(e) {
                if (e.reason && e.reason.name === 'RegisterClientLocalizationsError') {
                  e.preventDefault();
                  return false;
                }
                if (e.reason && e.reason.message && e.reason.message.includes('Could not establish connection')) {
                  e.preventDefault();
                  return false;
                }
              });
            `,
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {/* Fixed Header */}
        <header className="fixed top-0 left-0 right-0 z-50 bg-indigo-500 text-white shadow-lg">
          <div className="container mx-auto px-4 py-3">
            <div className="flex items-center justify-center">
              <span className="text-xl font-semibold">Clip Downloader</span>
            </div>
          </div>
          <h1 className="sr-only">Clip Downloader</h1>
        </header>

        {/* Hidden Progress Bar */}
        <div
          className="fixed top-16 left-0 right-0 z-40 h-1 bg-gray-200"
          aria-hidden="true"
        >
          <div className="h-full w-0 bg-indigo-400 transition-all duration-300 ease-out" />
        </div>

        {/* Main Content */}
        <main className="pt-20">
          <ToastProvider>{children}</ToastProvider>
        </main>
      </body>
    </html>
  );
};

export default AppShell;
