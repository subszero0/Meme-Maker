# ToDo - Video Player Functionality

This document outlines the systematic plan to fix and enable the video player for all supported platforms, focusing on Facebook which is currently failing.

## Phase 1: Stabilize Application (Completed)

- [x] Fix critical frontend import error for `useJobPoller`.
- [x] Fix crash in `LoadingAnimation` component during clip creation.
- [x] Stabilize the download architecture by switching from `format_id` to `resolution`.

## Phase 2: Implement Video Player for Facebook

### Step 1: Establish Ground Truth

*   **Goal**: Understand the exact metadata structure returned by `yt-dlp` for Facebook videos.
*   **Action**: Add temporary diagnostic logging to `backend/app/api/metadata.py` to print the full, raw `info` dictionary.
*   **Dependency**: Requires user to re-run the request and provide the backend logs.

### Step 2: Implement Robust URL Extraction

*   **Goal**: Extract a reliable, playable stream URL from the metadata.
*   **Action**:
    1.  Analyze the logged metadata to find the correct key for a manifest URL (e.g., `.m3u8`, `.mpd`) or a direct video format URL.
    2.  Modify the `VideoMetadata` Pydantic model in `backend/app/api/metadata.py` to include a field for this playable URL (e.g., `playback_url`).
    3.  Implement logic to populate this field, prioritizing manifest URLs over direct format URLs.

### Step 3: Update Frontend Player

*   **Goal**: Use the new `playback_url` in the React video player.
*   **Action**:
    1.  Update the `VideoMetadata` TypeScript type in `frontend-new/src/types/metadata.ts` to include `playback_url`.
    2.  Modify the URL selection logic in `frontend-new/src/pages/Index.tsx` to use `playback_url` for the `<VideoPlayer />` component if it exists.
    3.  Ensure the original source URL is still used for the actual clipping job request. 