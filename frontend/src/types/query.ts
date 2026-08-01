// GraphRAG Query Types

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_name: string;
  snippet: string;
  confidence_score: number;
  page_number?: number;
  section_title?: string;
}

export interface SubGraphPath {
  nodes: Record<string, any>[];
  edges: Record<string, any>[];
}

export interface RetrievalStats {
  node_count: number;
  chunk_count: number;
  relationship_count: number;
  retrieval_time_ms: number;
  llm_time_ms: number;
  total_time_ms: number;
}

export interface QueryRequest {
  question: string;
  top_k?: number;
  filters?: Record<string, any>;
}

export interface QueryResponse {
  question: string;
  answer: string;
  confidence: number;
  citations: Citation[];
  sources: string[];
  subgraph: SubGraphPath;
  retrieval_stats: RetrievalStats;
}
