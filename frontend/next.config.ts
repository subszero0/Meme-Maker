import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  eslint: {
    ignoreDuringBuilds: true
  },
  // Bundle optimization settings
  experimental: {
    optimizePackageImports: ['react-range', 'framer-motion', '@headlessui/react'],
  },
  // Webpack configuration for better tree shaking
  webpack: (config, { dev, isServer }) => {
    // Optimize for production builds
    if (!dev && !isServer) {
      config.optimization = {
        ...config.optimization,
        usedExports: true,
        sideEffects: false,
      };
    }
    
    // Alias react-player to lazy version by default
    config.resolve.alias = {
      ...config.resolve.alias,
      'react-player$': 'react-player/lazy',
    };

    return config;
  },
  // Enable compression
  compress: true,
};

export default nextConfig;
