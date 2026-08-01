import apiClient from '@/lib/api-client';
import { ApiResponse } from '@/types/api';
import {
  DocumentListResponse,
  DocumentMetadata,
  MultiUploadResponse,
} from '@/types/document';

export const documentsService = {
  /** Fetch all uploaded compliance documents */
  async listDocuments(): Promise<ApiResponse<DocumentListResponse>> {
    const response = await apiClient.get<ApiResponse<DocumentListResponse>>(
      '/documents'
    );
    return response.data;
  },

  /** Upload multiple compliance documents (PDF, CSV, MP3) */
  async uploadDocuments(
    files: File[],
    onUploadProgress?: (progress: number) => void
  ): Promise<ApiResponse<MultiUploadResponse>> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const response = await apiClient.post<ApiResponse<MultiUploadResponse>>(
      '/documents/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onUploadProgress?.(percent);
          }
        },
      }
    );
    return response.data;
  },

  /** Process document into semantic chunks */
  async processDocument(documentId: string): Promise<ApiResponse<any>> {
    const response = await apiClient.post<ApiResponse<any>>(
      `/documents/process/${documentId}`
    );
    return response.data;
  },

  /** Run AI knowledge extraction on document chunks */
  async extractKnowledge(documentId: string): Promise<ApiResponse<any>> {
    const response = await apiClient.post<ApiResponse<any>>(
      `/documents/extract/${documentId}`
    );
    return response.data;
  },
};
