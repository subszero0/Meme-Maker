export const en = {
  urlInputPanel: {
    placeholder: "Paste video URL (YouTube, Instagram, Facebook, Threads, Reddit)",
    startButton: "Start",
    errors: {
      required: "Please enter a video URL",
      invalid: "Please enter a valid video URL",
      unsupported: "This platform is not supported yet"
    },
    labels: {
      videoUrl: "Video URL"
    }
  }
} as const;

export type Translations = typeof en; 