export interface VideoFormat {
  format_id: string;
  ext: string;
  resolution: string;
  url: string;
  filesize?: number;
  filesize_approx?: number;
  fps?: number;
  vcodec: string;
  acodec: string;
  format_note: string;
  view_count: number;
  formats: VideoFormat[];
  manifest_url?: string;
}

export interface MetadataRequest {
  url: string;
}

export interface MetadataResponse {
  title: string;
  duration: number;
  thumbnail_url?: string;
  resolutions: string[];
}

export interface VideoMetadata {
  title: string;
  duration: number;
  thumbnail: string;
  uploader: string;
  upload_date: string;
  view_count: number;
  formats: VideoFormat[];
  resolutions: string[];
  manifest_url?: string;
}
