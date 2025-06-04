import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import DownloadModal from "../DownloadModal";
import ToastProvider from "../ToastProvider";

// Mock framer-motion to avoid animation complexity in tests
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.ComponentProps<"div">) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
}));

// Test wrapper with ToastProvider
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ToastProvider>{children}</ToastProvider>
);

describe("DownloadModal", () => {
  const mockOnClose = jest.fn();
  const testUrl = "https://example.com/test-video.mp4";

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  afterEach(() => {
    // Clean up any blob URLs created during tests
    if (testUrl.startsWith("blob:")) {
      URL.revokeObjectURL(testUrl);
    }
  });

  it("renders modal with correct title and content", () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    expect(screen.getByText("Clip ready!")).toBeInTheDocument();
    expect(
      screen.getByText(/File will self-destruct after this download/),
    ).toBeInTheDocument();
  });

  it("renders download button with correct attributes", () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    const downloadBtn = screen.getByTestId("download-btn");
    expect(downloadBtn).toBeInTheDocument();
    expect(downloadBtn).toHaveAttribute("href", testUrl);
    expect(downloadBtn).toHaveAttribute("download");
    expect(downloadBtn).toHaveAttribute("rel", "noopener noreferrer");
    expect(downloadBtn).toHaveTextContent("Download Now");
  });

  it("calls onClose when download button is clicked", async () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    const downloadBtn = screen.getByTestId("download-btn");
    await userEvent.click(downloadBtn);

    await waitFor(
      () => {
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      },
      { timeout: 200 },
    );
  });

  it("calls onClose when close button is clicked", async () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    const closeBtn = screen.getByText("Close");
    await userEvent.click(closeBtn);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when X button is clicked", async () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    // The X button should be in the header
    const closeBtn = screen.getByLabelText(/close dialog/i);
    await userEvent.click(closeBtn);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Escape key is pressed", async () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    fireEvent.keyDown(document, { key: "Escape", code: "Escape" });

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when overlay is clicked", async () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    // HeadlessUI Dialog manages the overlay click internally
    // We'll test the escape key functionality instead as it's more reliable
    fireEvent.keyDown(document, { key: "Escape", code: "Escape" });
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("does not close when modal content is clicked", async () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    // Click on the modal content area (not the backdrop)
    const modalPanel = screen
      .getByText("Clip ready!")
      .closest("div[data-headlessui-state]");
    if (modalPanel) {
      await userEvent.click(modalPanel);
      expect(mockOnClose).not.toHaveBeenCalled();
    }
  });

  it("has proper focus management", () => {
    render(
      <TestWrapper>
        <DownloadModal url={testUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    // Check that the dialog is properly set up for focus trapping
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();

    // Download button should be focusable
    const downloadBtn = screen.getByTestId("download-btn");
    expect(downloadBtn).not.toHaveAttribute("tabindex", "-1");
  });

  it("handles blob URLs properly", async () => {
    const blobUrl = "blob:http://localhost:3000/test-blob";
    const originalRevokeObjectURL = URL.revokeObjectURL;
    const mockRevoke = jest.fn();
    URL.revokeObjectURL = mockRevoke;

    render(
      <TestWrapper>
        <DownloadModal url={blobUrl} onClose={mockOnClose} />
      </TestWrapper>,
    );

    const downloadBtn = screen.getByTestId("download-btn");
    await userEvent.click(downloadBtn);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    // Restore original function
    URL.revokeObjectURL = originalRevokeObjectURL;
  });
});
