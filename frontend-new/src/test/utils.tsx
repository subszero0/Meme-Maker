import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { AppStateProvider } from "../hooks/useAppState";
import { Toaster } from "../components/ui/toaster";
import { vi } from "vitest";

// ===========================
// Test Providers Wrapper
// ===========================

interface TestProvidersProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
  initialRoute?: string;
}

const TestProviders: React.FC<TestProvidersProps> = ({
  children,
  queryClient,
  initialRoute = "/",
}) => {
  const testQueryClient =
    queryClient ||
    new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: Infinity,
        },
        mutations: {
          retry: false,
        },
      },
    });

  // Set initial route if needed
  if (initialRoute !== "/") {
    window.history.pushState({}, "Test page", initialRoute);
  }

  return (
    <QueryClientProvider client={testQueryClient}>
      <BrowserRouter>
        <AppStateProvider>
          {children}
          <Toaster />
        </AppStateProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// ===========================
// Custom Render Function
// ===========================

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  queryClient?: QueryClient;
  initialRoute?: string;
}

const customRender = (ui: ReactElement, options: CustomRenderOptions = {}) => {
  const { queryClient, initialRoute, ...renderOptions } = options;

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <TestProviders queryClient={queryClient} initialRoute={initialRoute}>
      {children}
    </TestProviders>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// ===========================
// Test Utilities
// ===========================

export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
        gcTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });

export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

export const createMockFile = (name = "test.mp4", size = 1000000) =>
  new File(["test content"], name, {
    type: "video/mp4",
    lastModified: Date.now(),
  });

export const createMockUrl = (
  type: "youtube" | "valid" | "invalid" = "youtube",
) => {
  switch (type) {
    case "youtube":
      return "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
    case "valid":
      return "https://example.com/video.mp4";
    case "invalid":
      return "https://invalid-url.com/invalid";
    default:
      return "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
  }
};

export const mockIntersectionObserver = () => {
  const observe = vi.fn();
  const disconnect = vi.fn();
  const unobserve = vi.fn();

  window.IntersectionObserver = vi.fn(() => ({
    observe,
    disconnect,
    unobserve,
  })) as any;

  return { observe, disconnect, unobserve };
};

export const mockResizeObserver = () => {
  const observe = vi.fn();
  const disconnect = vi.fn();
  const unobserve = vi.fn();

  window.ResizeObserver = vi.fn(() => ({
    observe,
    disconnect,
    unobserve,
  })) as any;

  return { observe, disconnect, unobserve };
};

// ===========================
// Event Utilities
// ===========================

export const createMockPointerEvent = (
  type: string,
  options: Partial<PointerEvent> = {},
) => {
  return new PointerEvent(type, {
    bubbles: true,
    cancelable: true,
    pointerId: 1,
    ...options,
  });
};

export const createMockKeyboardEvent = (
  key: string,
  options: Partial<KeyboardEvent> = {},
) => {
  return new KeyboardEvent("keydown", {
    key,
    bubbles: true,
    cancelable: true,
    ...options,
  });
};

// ===========================
// Async Test Helpers
// ===========================

export const flushPromises = () =>
  new Promise((resolve) => setImmediate(resolve));

export const waitFor = (
  callback: () => boolean | Promise<boolean>,
  timeout = 5000,
) => {
  return new Promise<void>((resolve, reject) => {
    const startTime = Date.now();

    const check = async () => {
      try {
        const result = await callback();
        if (result) {
          resolve();
          return;
        }
      } catch (error) {
        // Continue waiting
      }

      if (Date.now() - startTime > timeout) {
        reject(new Error(`waitFor timeout after ${timeout}ms`));
        return;
      }

      setTimeout(check, 10);
    };

    check();
  });
};

// ===========================
// Exports
// ===========================

export { customRender as render };
export { TestProviders };

// Re-export everything from testing-library
export * from "@testing-library/react";
export { userEvent } from "@testing-library/user-event";
