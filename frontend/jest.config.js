// Manual Jest configuration without Next.js integration to avoid SWC issues
const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    // Handle CSS and style imports
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    // Handle image and file imports
    "\\.(jpg|jpeg|png|gif|webp|svg)$": "<rootDir>/__mocks__/fileMock.js",
  },
  testPathIgnorePatterns: ["<rootDir>/.next/", "<rootDir>/node_modules/"],
  collectCoverageFrom: ["src/**/*.{js,jsx,ts,tsx}", "!src/**/*.d.ts"],
  
  // Use Babel instead of SWC for transformations
  transform: {
    "^.+\\.(js|jsx|ts|tsx)$": ["babel-jest", {
      presets: [
        ["@babel/preset-env", { targets: { node: "current" } }],
        ["@babel/preset-react", { runtime: "automatic" }],
        "@babel/preset-typescript",
      ],
    }],
  },
  
  // File extensions to process
  moduleFileExtensions: ["js", "jsx", "ts", "tsx", "json", "node"],
  
  // Transform node_modules if needed
  transformIgnorePatterns: [
    "node_modules/(?!(some-module-to-transform)/)",
  ],
};

module.exports = customJestConfig;
