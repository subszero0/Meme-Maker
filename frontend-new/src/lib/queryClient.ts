import { QueryClient } from '@tanstack/react-query';

// ===========================
// React Query Configuration
// ===========================

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: How long data is considered fresh (5 minutes)
      staleTime: 5 * 60 * 1000,
      
      // Cache time: How long to keep unused data in cache (10 minutes)  
      gcTime: 10 * 60 * 1000,
      
      // Retry configuration
      retry: (failureCount, error: unknown) => {
        // Don't retry on 4xx errors (client errors)
        const errorWithStatus = error as { status?: number };
        if (errorWithStatus?.status && errorWithStatus.status >= 400 && errorWithStatus.status < 500) {
          return false;
        }
        // Retry up to 3 times for other errors
        return failureCount < 3;
      },
      
      // Retry delay with exponential backoff
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      // Refetch configuration
      refetchOnWindowFocus: false, // Don't refetch when window gains focus
      refetchOnReconnect: true,    // Refetch when connection is restored
      refetchOnMount: true,        // Refetch when component mounts
    },
    mutations: {
      // Retry mutations once on failure
      retry: 1,
      
      // Retry delay for mutations
      retryDelay: 1000,
    },
  },
});

// ===========================
// Query Keys Factory
// ===========================

export const queryKeys = {
  // Health check
  health: ['health'] as const,
  
  // Metadata queries
  metadata: ['metadata'] as const,
  metadataByUrl: (url: string) => [...queryKeys.metadata, url] as const,
  detailedMetadata: (url: string) => [...queryKeys.metadata, 'detailed', url] as const,
  
  // Job queries
  jobs: ['jobs'] as const,
  job: (jobId: string) => [...queryKeys.jobs, jobId] as const,
} as const; 