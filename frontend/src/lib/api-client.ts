import axios, { AxiosError, AxiosInstance } from 'axios';
import { ApiResponse, ErrorResponse } from '@/types/api';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000, // 45 seconds for processing / LLM extraction
  headers: {
    'Content-Type': 'application/json',
  },
});

// Retry configuration for transient errors
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const config = error.config as any;

    // Retry logic for 502/503/504 or network timeout errors
    if (
      config &&
      !config._retry &&
      (error.response?.status === 502 ||
        error.response?.status === 503 ||
        error.response?.status === 504 ||
        error.code === 'ECONNABORTED' ||
        !error.response)
    ) {
      config._retryCount = config._retryCount || 0;

      if (config._retryCount < MAX_RETRIES) {
        config._retryCount += 1;
        await new Promise((resolve) =>
          setTimeout(resolve, RETRY_DELAY_MS * config._retryCount)
        );
        return apiClient(config);
      }
    }

    const errorData = error.response?.data;
    const message =
      errorData?.message ||
      (error.code === 'ECONNABORTED'
        ? 'Request timed out. Please try again.'
        : !error.response
        ? 'Backend API server unreachable (http://localhost:8000).'
        : 'An unexpected error occurred.');

    return Promise.reject({
      message,
      status: error.response?.status || 500,
      code: errorData?.error_code || 'API_ERROR',
      details: errorData?.details || {},
    });
  }
);

export default apiClient;
