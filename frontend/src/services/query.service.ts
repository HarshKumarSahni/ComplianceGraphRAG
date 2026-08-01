import apiClient from '@/lib/api-client';
import { ApiResponse } from '@/types/api';
import { QueryRequest, QueryResponse } from '@/types/query';

export const queryService = {
  /** Execute GraphRAG compliance question query */
  async executeQuery(
    request: QueryRequest
  ): Promise<ApiResponse<QueryResponse>> {
    const response = await apiClient.post<ApiResponse<QueryResponse>>(
      '/query',
      {
        question: request.question,
        top_k: request.top_k || 5,
        filters: request.filters || {},
      }
    );
    return response.data;
  },
};
