import apiClient from '@/lib/api-client';
import { ApiResponse } from '@/types/api';
import { HealthStatus } from '@/types/health';

export const healthService = {
  async getHealthStatus(): Promise<ApiResponse<HealthStatus>> {
    const response = await apiClient.get<ApiResponse<HealthStatus>>('/health');
    return response.data;
  },
};
