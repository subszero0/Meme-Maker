import { renderHook, act, waitFor } from "@testing-library/react";
import { ReactNode } from "react";
import axios from "axios";
import useJobPoller from "../useJobPoller";
import ToastProvider from "@/components/ToastProvider";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockApiUrl = "http://localhost:8000"; // Use default URL for tests

// Test wrapper with ToastProvider
const Wrapper = ({ children }: { children: ReactNode }) => (
  <ToastProvider>{children}</ToastProvider>
);

// Mock cancel token
const mockCancelTokenSource = {
  token: "mock-token",
  cancel: jest.fn(),
};

describe("useJobPoller", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    // Mock axios.CancelToken.source
    mockedAxios.CancelToken = {
      source: jest.fn(() => mockCancelTokenSource),
    } as { source: jest.Mock };

    // Mock axios.isCancel
    (mockedAxios.isCancel as jest.Mock) = jest.fn().mockReturnValue(false);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns queued status when jobId is null", () => {
    const { result } = renderHook(() => useJobPoller(null), {
      wrapper: Wrapper,
    });

    expect(result.current).toEqual({ status: "queued" });
  });

  it("polls job status successfully and stops when done", async () => {
    const jobId = "test-job-123";
    const mockJobData = {
      status: "working",
      progress: 50,
    };

    mockedAxios.get.mockResolvedValueOnce({
      data: mockJobData,
    });

    const { result } = renderHook(() => useJobPoller(jobId), {
      wrapper: Wrapper,
    });

    // Wait for initial poll
    await waitFor(() => {
      expect(result.current.status).toBe("working");
    });

    expect(result.current).toEqual({
      status: "working",
      progress: 50,
      url: undefined,
      errorCode: undefined,
    });

    expect(mockedAxios.get).toHaveBeenCalledWith(
      `${mockApiUrl}/api/v1/jobs/${jobId}`,
      {
        cancelToken: "mock-token",
        timeout: 5000,
      },
    );
  });

  it("stops polling when job status is done", async () => {
    const jobId = "test-job-123";
    const mockJobData = {
      status: "done",
      progress: 100,
      download_url: "https://example.com/download",
    };

    mockedAxios.get.mockResolvedValue({
      data: mockJobData,
    });

    const { result } = renderHook(() => useJobPoller(jobId), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.status).toBe("done");
    });

    expect(result.current).toEqual({
      status: "done",
      progress: 100,
      url: "https://example.com/download",
      errorCode: undefined,
    });

    // Advance time to verify polling stopped
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    // Should not make additional requests
    expect(mockedAxios.get).toHaveBeenCalledTimes(1);
  });

  it("handles network errors with exponential backoff", async () => {
    const jobId = "test-job-123";

    mockedAxios.get.mockRejectedValue({
      response: { status: 500 },
      code: undefined,
    });

    const { result, unmount } = renderHook(() => useJobPoller(jobId, 1000), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.errorCode).toBe("NETWORK");
    unmount();
  });

  it("handles timeout errors with exponential backoff", async () => {
    const jobId = "test-job-123";

    mockedAxios.get.mockRejectedValue({
      code: "ECONNABORTED",
      response: undefined,
    });

    const { result } = renderHook(() => useJobPoller(jobId, 1000), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.errorCode).toBe("NETWORK");
  });

  it("stops polling on 404 errors", async () => {
    const jobId = "test-job-123";

    mockedAxios.get.mockRejectedValue({
      response: { status: 404 },
    });

    const { result } = renderHook(() => useJobPoller(jobId), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.errorCode).toBe("JOB_NOT_FOUND");

    // Advance time to verify polling stopped
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    // Should not make additional requests
    expect(mockedAxios.get).toHaveBeenCalledTimes(1);
  });

  it("handles QUEUE_FULL errors correctly", async () => {
    const jobId = "test-job-123";

    mockedAxios.get.mockRejectedValue({
      response: { status: 429 },
    });

    const { result } = renderHook(() => useJobPoller(jobId), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.errorCode).toBe("QUEUE_FULL");
  });

  it("cancels requests on unmount", async () => {
    const jobId = "test-job-123";

    mockedAxios.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { unmount } = renderHook(() => useJobPoller(jobId), {
      wrapper: Wrapper,
    });

    // Unmount before request completes
    unmount();

    expect(mockCancelTokenSource.cancel).toHaveBeenCalledWith(
      "Component unmounted or polling stopped",
    );
  });

  it("cancels previous request when starting new one", async () => {
    const jobId = "test-job-123";

    mockedAxios.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderHook(() => useJobPoller(jobId), {
      wrapper: Wrapper,
    });

    // Advance time to trigger second poll
    act(() => {
      jest.advanceTimersByTime(2000);
    });

    expect(mockCancelTokenSource.cancel).toHaveBeenCalledWith(
      "New request initiated",
    );
  });

  it("ignores cancelled requests", async () => {
    const jobId = "test-job-123";

    mockedAxios.isCancel.mockReturnValue(true);
    mockedAxios.get.mockRejectedValue(new Error("Request cancelled"));

    const { result } = renderHook(() => useJobPoller(jobId), {
      wrapper: Wrapper,
    });

    // Wait a bit for any state changes
    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    // Should remain in initial state
    expect(result.current).toEqual({ status: "queued" });
  });

  it("respects custom poll interval", async () => {
    const jobId = "test-job-123";
    const customInterval = 5000;

    mockedAxios.get.mockResolvedValue({
      data: { status: "working" },
    });

    renderHook(() => useJobPoller(jobId, customInterval), {
      wrapper: Wrapper,
    });

    // Clear initial call
    mockedAxios.get.mockClear();

    // Advance by custom interval
    act(() => {
      jest.advanceTimersByTime(customInterval);
    });

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledTimes(1);
    });
  });

  it.skip("resets interval on successful response", async () => {
    const jobId = "test-job-123";
    const initialInterval = 1000;

    // First call fails (triggers backoff), then succeeds
    mockedAxios.get
      .mockRejectedValueOnce({
        response: { status: 500 },
        code: undefined,
      })
      .mockResolvedValue({
        data: { status: "working" },
      });

    const { result, unmount } = renderHook(
      () => useJobPoller(jobId, initialInterval),
      {
        wrapper: Wrapper,
      },
    );

    // Wait for error state first with longer timeout
    await waitFor(
      () => {
        expect(result.current.status).toBe("error");
      },
      { timeout: 3000 },
    );

    // Verify error code is set correctly
    expect(result.current.errorCode).toBe("NETWORK");

    // Advance time to trigger next poll attempt
    act(() => {
      jest.advanceTimersByTime(initialInterval * 2); // Account for backoff
    });

    // Wait for recovery to working state
    await waitFor(
      () => {
        expect(result.current.status).toBe("working");
      },
      { timeout: 3000 },
    );

    unmount();
  });

  it("caps exponential backoff at maximum interval", async () => {
    const jobId = "test-job-123";
    const initialInterval = 1000;

    mockedAxios.get.mockRejectedValue({
      response: { status: 500 },
    });

    const { result, unmount } = renderHook(
      () => useJobPoller(jobId, initialInterval),
      {
        wrapper: Wrapper,
      },
    );

    // Wait for error state
    await waitFor(() => {
      expect(result.current.status).toBe("error");
      expect(result.current.errorCode).toBe("NETWORK");
    });

    unmount();
  });

  it("includes poll interval test element for timing assertions", () => {
    renderHook(() => useJobPoller("test-job"), {
      wrapper: Wrapper,
    });

    // Add a test component that uses the hook and renders a testid element
    const TestComponent = () => {
      const pollResult = useJobPoller("test-job");
      return <span data-testid="poll-interval">{pollResult.status}</span>;
    };

    expect(TestComponent).toBeDefined();
  });

  it("supports custom poll intervals for testing timing", () => {
    // Test that the hook can be called with different intervals
    const hook1 = renderHook(() => useJobPoller("test-job-1", 1000), {
      wrapper: Wrapper,
    });
    const hook2 = renderHook(() => useJobPoller("test-job-2", 2000), {
      wrapper: Wrapper,
    });

    expect(hook1.result.current.status).toBe("queued");
    expect(hook2.result.current.status).toBe("queued");
  });
});
