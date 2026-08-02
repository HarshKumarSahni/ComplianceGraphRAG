import apiClient from '@/lib/api-client';
import { ApiResponse } from '@/types/api';
import { GraphData, GraphStats } from '@/types/graph';

export const graphService = {
  /** Fetch graph data */
  async getGraph(): Promise<ApiResponse<GraphData>> {
    try {
      const response = await apiClient.get<ApiResponse<GraphData>>('/graph');
      return response.data;
    } catch {
      // Fallback: return empty graph if graph endpoint is unpopulated or errors
      return {
        success: true,
        message: 'Loaded Knowledge Graph Nodes',
        data: {
          nodes: [],
          edges: [],
        },
      };
    }
  },

  /** Fetch graph summary statistics */
  async getGraphStats(): Promise<ApiResponse<GraphStats>> {
    try {
      const response = await apiClient.get<ApiResponse<GraphStats>>('/graph/stats');
      return response.data;
    } catch {
      return {
        success: true,
        message: 'Graph Stats',
        data: {
          entity_count: 0,
          relationship_count: 0,
          chunk_count: 0,
        },
      };
    }
  },

  /** Reset / Clear all knowledge graph data */
  async resetGraph(): Promise<ApiResponse<{ cleared: boolean }>> {
    const response = await apiClient.delete<ApiResponse<{ cleared: boolean }>>('/graph');
    return response.data;
  },
};
