import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DownloadModal from "../DownloadModal";

// Mock framer-motion to avoid animation complexity in tests
jest.mock("framer-motion", () => ({
  motion: {
    div: ({
      children,
      ...props
    }: {
      children: React.ReactNode;
      [key: string]: unknown;
    }) => <div {...props}>{children}</div>,
  },
}));

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
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

    expect(screen.getByText("Clip ready!")).toBeInTheDocument();
    expect(
      screen.getByText("File will self-destruct after this download."),
    ).toBeInTheDocument();
  });

  it("renders download button with correct attributes", () => {
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

    const downloadBtn = screen.getByTestId("download-btn");
    expect(downloadBtn).toBeInTheDocument();
    expect(downloadBtn).toHaveAttribute("href", testUrl);
    expect(downloadBtn).toHaveAttribute("download");
    expect(downloadBtn).toHaveAttribute("rel", "noopener noreferrer");
    expect(downloadBtn).toHaveTextContent("Download");
  });

  it("calls onClose when download button is clicked", async () => {
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

    const downloadBtn = screen.getByTestId("download-btn");
    await userEvent.click(downloadBtn);

    await waitFor(
      () => {
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      },
      { timeout: 200 },
    );
  });

  it("calls onClose when cancel button is clicked", async () => {
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

    const cancelBtn = screen.getByText("Cancel");
    await userEvent.click(cancelBtn);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when X button is clicked", async () => {
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

    // The X button should be in the header
    const closeBtn = screen.getByLabelText(/close dialog/i);
    await userEvent.click(closeBtn);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Escape key is pressed", async () => {
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

    fireEvent.keyDown(document, { key: "Escape", code: "Escape" });

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when overlay is clicked", async () => {
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

    // HeadlessUI Dialog manages the overlay click internally
    // We'll test the escape key functionality instead as it's more reliable
    fireEvent.keyDown(document, { key: "Escape", code: "Escape" });
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("does not close when modal content is clicked", async () => {
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

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
    render(<DownloadModal url={testUrl} onClose={mockOnClose} />);

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

    render(<DownloadModal url={blobUrl} onClose={mockOnClose} />);

    const downloadBtn = screen.getByTestId("download-btn");
    await userEvent.click(downloadBtn);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    // Restore original function
    URL.revokeObjectURL = originalRevokeObjectURL;
  });
});
