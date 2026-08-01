import apiClient from '@/lib/api-client';
import { ApiResponse } from '@/types/api';
import { MultiUploadResponse } from '@/types/document';

export const uploadService = {
  async uploadDocuments(files: File[]): Promise<ApiResponse<MultiUploadResponse>> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const response = await apiClient.post<ApiResponse<MultiUploadResponse>>(
      '/documents/upload',
      formData
    );
    return response.data;
  },
};
