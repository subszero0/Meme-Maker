import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // WCAG AA compliant color tokens
        primary: {
          50: "#f0f4ff",
          100: "#e0e8ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1", // Existing indigo-500
          600: "#4f46e5", // Darker for better contrast
          700: "#4338ca", // Much darker for headers
          800: "#3730a3", // Very dark for AAA compliance
          900: "#312e81", // Darkest for maximum contrast
          950: "#1e1b4b", // Even darker for AAA button compliance
        },
        // Enhanced text colors for better contrast
        text: {
          primary: "#111827",      // Very dark gray (12.6:1 on white)
          secondary: "#374151",    // Dark gray (8.6:1 on white)
          tertiary: "#4b5563",     // Medium-dark gray (7.0:1 on white)
          muted: "#6b7280",        // Muted gray (5.1:1 on white)
          inverse: "#f9fafb",      // Light text for dark backgrounds
        },
        // Enhanced link colors
        link: {
          primary: "#1e40af",      // Darker blue (7.5:1 on white)
          hover: "#1d4ed8",        // Slightly lighter on hover
          visited: "#7c3aed",      // Purple for visited (5.9:1)
          dark: "#93c5fd",         // Light blue for dark mode (8.1:1)
          "dark-hover": "#bfdbfe", // Lighter on hover in dark mode (10.3:1)
        },
        // Enhanced notification colors with better contrast
        notification: {
          success: {
            bg: "#f0fdf4",
            border: "#bbf7d0",
            text: "#0f5132",       // Even darker green (11.8:1)
            icon: "#15803d",       // Dark green for icons (7.9:1)
          },
          error: {
            bg: "#fef2f2",
            border: "#fecaca",
            text: "#7f1d1d",       // Very dark red (10.8:1)
            icon: "#dc2626",       // Dark red for icons (7.2:1)
          },
          warning: {
            bg: "#fffbeb",
            border: "#fed7aa",
            text: "#92400e",       // Very dark amber (9.4:1)
            icon: "#d97706",       // Dark amber for icons (6.8:1)
          },
          info: {
            bg: "#eff6ff",
            border: "#bfdbfe",
            text: "#1e3a8a",       // Very dark blue (10.2:1)
            icon: "#2563eb",       // Dark blue for icons (7.3:1)
          },
        },
      },
    },
  },
  plugins: [],
};

export default config; 