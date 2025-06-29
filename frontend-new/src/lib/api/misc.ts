import { AxiosResponse } from "axios";
import { apiClient, handleApiError } from "../apiClient";
import { HealthResponse } from "../../types/common";
import { config } from "../../config/environment";

export const clipsApi = {
  getDownloadUrl(filename: string): string {
    return `${config.API_BASE_URL}/clips/${filename}`;
  },

  async deleteClip(jobId: string): Promise<{ message: string }> {
    try {
      const response: AxiosResponse<{ message: string }> =
        await apiClient.delete(`api/v1/clips/${jobId}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

export const healthApi = {
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response: AxiosResponse<HealthResponse> =
        await apiClient.get("/health");
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};
