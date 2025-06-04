import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import URLInputPanel from "../URLInputPanel";

const mockOnSubmit = jest.fn();

describe("URLInputPanel", () => {
  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it("renders input field and button", () => {
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    expect(screen.getByTestId("url-input")).toBeInTheDocument();
    expect(screen.getByTestId("start-button")).toBeInTheDocument();
    expect(screen.getByLabelText("Video URL")).toBeInTheDocument();
  });

  it("shows error when input is empty and form is submitted", async () => {
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const startButton = screen.getByTestId("start-button");
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByTestId("url-error")).toHaveTextContent(
        "Please enter a video URL",
      );
    });
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows error for invalid URLs after debounce", async () => {
    const user = userEvent.setup();
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const input = screen.getByTestId("url-input");
    await user.type(input, "invalid-url");

    await waitFor(
      () => {
        expect(screen.getByTestId("url-error")).toHaveTextContent(
          "Please enter a valid video URL",
        );
      },
      { timeout: 500 },
    );
  });

  it("detects YouTube platform and shows correct icon", async () => {
    const user = userEvent.setup();
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const input = screen.getByTestId("url-input");
    await user.type(input, "https://youtube.com/watch?v=test");

    await waitFor(() => {
      expect(screen.getByText("🎬")).toBeInTheDocument();
    });
  });

  it("detects Instagram platform and shows correct icon", async () => {
    const user = userEvent.setup();
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const input = screen.getByTestId("url-input");
    await user.type(input, "https://instagram.com/p/test");

    await waitFor(() => {
      expect(screen.getByText("📷")).toBeInTheDocument();
    });
  });

  it("calls onSubmit with valid YouTube URL", async () => {
    const user = userEvent.setup();
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const input = screen.getByTestId("url-input");
    const validUrl = "https://youtube.com/watch?v=test123";

    await user.type(input, validUrl);

    // Wait for debounce to complete
    await waitFor(() => {
      expect(screen.queryByTestId("url-error")).not.toBeInTheDocument();
    });

    const startButton = screen.getByTestId("start-button");
    fireEvent.click(startButton);

    expect(mockOnSubmit).toHaveBeenCalledWith(validUrl);
  });

  it("disables button when URL has error", async () => {
    const user = userEvent.setup();
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const input = screen.getByTestId("url-input");
    await user.type(input, "invalid-url");

    await waitFor(() => {
      expect(screen.getByTestId("start-button")).toBeDisabled();
    });
  });

  it("has proper accessibility attributes", () => {
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const input = screen.getByTestId("url-input");
    const label = screen.getByText("Video URL");

    expect(label).toHaveAttribute("for", "video-url");
    expect(input).toHaveAttribute("id", "video-url");
    expect(input).toHaveAttribute("type", "url");
  });

  it("trims whitespace from URL before submission", async () => {
    const user = userEvent.setup();
    render(<URLInputPanel onSubmit={mockOnSubmit} />);

    const input = screen.getByTestId("url-input");
    const urlWithSpaces = "  https://youtube.com/watch?v=test  ";

    await user.type(input, urlWithSpaces);

    await waitFor(() => {
      expect(screen.queryByTestId("url-error")).not.toBeInTheDocument();
    });

    const startButton = screen.getByTestId("start-button");
    fireEvent.click(startButton);

    expect(mockOnSubmit).toHaveBeenCalledWith(
      "https://youtube.com/watch?v=test",
    );
  });
});
