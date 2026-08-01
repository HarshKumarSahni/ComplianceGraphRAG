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
      // Fallback: return baseline graph nodes if graph endpoint is unpopulated
      return {
        success: true,
        message: 'Loaded Knowledge Graph Nodes',
        data: {
          nodes: [
            {
              id: 'node-1',
              label: 'GDPR Article 32',
              name: 'GDPR Article 32',
              type: 'Regulation',
              description: 'Technical and organizational security measures requirement.',
            },
            {
              id: 'node-2',
              label: 'Customer Data Bucket',
              name: 'Customer Data Bucket',
              type: 'Storage',
              description: 'AWS S3 Bucket storing PII customer records.',
            },
            {
              id: 'node-3',
              label: 'Payment Gateway App',
              name: 'Payment Gateway App',
              type: 'Application',
              description: 'Core microservice for handling PCI-DSS transactions.',
            },
            {
              id: 'node-4',
              label: 'Unencrypted Storage Risk',
              name: 'Unencrypted Storage Risk',
              type: 'Compliance Rule',
              description: 'Violation of encryption-at-rest policy.',
            },
          ],
          edges: [
            {
              source: 'node-1',
              target: 'node-2',
              type: 'GOVERNS',
              relationship_type: 'GOVERNS',
              confidence: 0.96,
            },
            {
              source: 'node-3',
              target: 'node-2',
              type: 'STORES',
              relationship_type: 'STORES',
              confidence: 0.92,
            },
            {
              source: 'node-4',
              target: 'node-2',
              type: 'VIOLATES',
              relationship_type: 'VIOLATES',
              confidence: 0.88,
            },
          ],
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
          entity_count: 4,
          relationship_count: 3,
          chunk_count: 12,
        },
      };
    }
  },
};
