interface EnvironmentConfig {
  API_BASE_URL: string;
  WS_BASE_URL: string;
  ENABLE_LOGGING: boolean;
  ENABLE_ANALYTICS: boolean;
  ENABLE_DEVTOOLS: boolean;
  MAX_FILE_SIZE: number;
  SUPPORTED_FORMATS: string[];
  ENVIRONMENT: 'development' | 'staging' | 'production';
}

const isDevelopment = import.meta.env.MODE === 'development';
const isStaging = import.meta.env.MODE === 'staging';
const isProduction = import.meta.env.MODE === 'production';

// Default configuration provides a base for all environments.
const defaultConfig: EnvironmentConfig = {
  API_BASE_URL: 'http://localhost:8000',
  WS_BASE_URL: 'ws://localhost:8000',
  ENABLE_LOGGING: true,
  ENABLE_ANALYTICS: false,
  ENABLE_DEVTOOLS: true,
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  SUPPORTED_FORMATS: ['mp4', 'webm', 'avi', 'mov', 'mkv'],
  ENVIRONMENT: 'development',
};

// Environment-specific overrides. Only the properties that differ from the default need to be listed.
const environmentConfigs: Record<string, Partial<EnvironmentConfig>> = {
  development: {
    API_BASE_URL: 'http://localhost:8000',
    WS_BASE_URL: 'ws://localhost:8000',
    ENVIRONMENT: 'development',
  },
  staging: {
    API_BASE_URL: 'https://staging-api.meme-maker.com',
    WS_BASE_URL: 'wss://staging-api.meme-maker.com',
    ENABLE_ANALYTICS: true,
    ENABLE_DEVTOOLS: false,
    ENVIRONMENT: 'staging',
  },
  production: {
    API_BASE_URL: '', // Use relative paths for API calls in production.
    WS_BASE_URL: '', // This will be set dynamically at runtime.
    ENABLE_LOGGING: false,
    ENABLE_ANALYTICS: true,
    ENABLE_DEVTOOLS: false,
    ENVIRONMENT: 'production',
  },
};

// Determine the current operating mode.
const currentMode = import.meta.env.MODE || 'development';
const envConfig = environmentConfigs[currentMode] || {};

// Build the final configuration object by merging defaults with environment-specific settings.
const finalConfig: EnvironmentConfig = {
  ...defaultConfig,
  ...envConfig,
};

// For production, the WebSocket URL must be determined at runtime in the browser.
if (isProduction && typeof window !== 'undefined') {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  finalConfig.WS_BASE_URL = `${protocol}//${window.location.host}/ws`;
}

// Export the final, clean configuration.
// It can still be overridden by explicit environment variables (VITE_*) if they are present.
export const config: EnvironmentConfig = {
    ...finalConfig,
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL ?? finalConfig.API_BASE_URL,
    WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL ?? finalConfig.WS_BASE_URL,
};

// Environment detection utilities
export const environment = {
  isDevelopment,
  isStaging,
  isProduction,
  mode: currentMode,
  isDebug: isDevelopment || isStaging,
};

// Logging utility that respects environment config
export const logger = {
  log: (...args: unknown[]) => {
    if (config.ENABLE_LOGGING) {
      console.log(...args);
    }
  },
  warn: (...args: unknown[]) => {
    if (config.ENABLE_LOGGING) {
      console.warn(...args);
    }
  },
  error: (...args: unknown[]) => {
    if (config.ENABLE_LOGGING) {
      console.error(...args);
    }
  },
  debug: (...args: unknown[]) => {
    if (config.ENABLE_LOGGING && environment.isDebug) {
      console.debug(...args);
    }
  },
};

export default config; 