// Knowledge Graph Types

export interface GraphNode {
  id: string;
  label: string;
  name: string;
  type: string;
  description?: string;
  properties?: Record<string, any>;
}

export interface GraphEdge {
  id?: string;
  source: string;
  target: string;
  type: string;
  relationship_type?: string;
  confidence?: number;
  evidence?: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphStats {
  entity_count: number;
  relationship_count: number;
  chunk_count: number;
}
