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

// Default configuration
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

// Environment-specific overrides
const environmentConfigs: Record<string, Partial<EnvironmentConfig>> = {
  development: {
    API_BASE_URL: 'http://localhost:8000',
    WS_BASE_URL: 'ws://localhost:8000',
    ENABLE_LOGGING: true,
    ENABLE_ANALYTICS: false,
    ENABLE_DEVTOOLS: true,
    ENVIRONMENT: 'development',
  },
  staging: {
    API_BASE_URL: 'https://staging-api.meme-maker.com',
    WS_BASE_URL: 'wss://staging-api.meme-maker.com',
    ENABLE_LOGGING: true,
    ENABLE_ANALYTICS: true,
    ENABLE_DEVTOOLS: false,
    ENVIRONMENT: 'staging',
  },
  production: {
    API_BASE_URL: 'https://api.meme-maker.com',
    WS_BASE_URL: 'wss://api.meme-maker.com',
    ENABLE_LOGGING: false,
    ENABLE_ANALYTICS: true,
    ENABLE_DEVTOOLS: false,
    ENVIRONMENT: 'production',
  },
};

// Merge default config with environment-specific config
const currentMode = import.meta.env.MODE || 'development';
const envConfig = environmentConfigs[currentMode] || {};

export const config: EnvironmentConfig = {
  ...defaultConfig,
  ...envConfig,
  // Allow environment variables to override config
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || envConfig.API_BASE_URL || defaultConfig.API_BASE_URL,
  WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL || envConfig.WS_BASE_URL || defaultConfig.WS_BASE_URL,
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