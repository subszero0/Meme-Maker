import { AxiosResponse } from "axios";
import { apiClient, handleApiError } from "../apiClient";
import { JobCreate, JobResponse } from "../../types/job";

export const jobsApi = {
  async createJob(jobData: JobCreate): Promise<JobResponse> {
    try {
      const response: AxiosResponse<JobResponse> = await apiClient.post(
        "api/v1/jobs",
        jobData,
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  async getJob(jobId: string): Promise<JobResponse> {
    try {
      const response: AxiosResponse<JobResponse> = await apiClient.get(
        `api/v1/jobs/${jobId}`,
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};
