import { AxiosResponse } from "axios";
import { apiClient, handleApiError } from "../apiClient";
import { MetadataResponse, VideoMetadata } from "../../types/metadata";

export const metadataApi = {
  async getBasicMetadata(url: string): Promise<MetadataResponse> {
    try {
      console.log("🔍 Fetching basic metadata for:", url);
      const response: AxiosResponse<MetadataResponse> = await apiClient.post(
        "api/v1/metadata/extract",
        {
          url,
        },
      );
      console.log("✅ Basic metadata received:", response.data);
      return response.data;
    } catch (error) {
      console.error("❌ Basic metadata failed:", error);
      handleApiError(error as any);
    }
  },

  async getDetailedMetadata(url: string): Promise<VideoMetadata> {
    try {
      console.log("🔍 Fetching detailed metadata for:", url);
      const response: AxiosResponse<VideoMetadata> = await apiClient.post(
        "api/v1/metadata/extract",
        {
          url,
        },
      );
      console.log(
        `✅ Detailed metadata received: ${response.data.formats.length} formats`,
      );
      return response.data;
    } catch (error) {
      console.error("❌ Detailed metadata failed:", error);
      handleApiError(error as any);
    }
  },
}; 