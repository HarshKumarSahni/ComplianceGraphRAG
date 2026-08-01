// Document Types

export type FileType = 'pdf' | 'csv' | 'audio';

export type DocumentStatus =
  | 'UPLOADED'
  | 'PARSING'
  | 'NORMALIZING'
  | 'CHUNKING'
  | 'READY_FOR_ENTITY_EXTRACTION'
  | 'ENTITY_EXTRACTION'
  | 'RELATIONSHIP_EXTRACTION'
  | 'VALIDATION'
  | 'READY_FOR_GRAPH_BUILDING'
  | 'PARSED'
  | 'GRAPH_BUILT'
  | 'READY'
  | 'FAILED';

export interface DocumentMetadata {
  document_id: string;
  original_filename: string;
  cloudinary_url: string;
  public_id: string;
  upload_timestamp: string;
  file_size_bytes: number;
  file_type: FileType;
  mime_type: string;
  status: DocumentStatus;
  error_message?: string;
}

export interface FileUploadStatus {
  filename: string;
  success: boolean;
  metadata?: DocumentMetadata;
  error?: string;
}

export interface MultiUploadResponse {
  total_files: number;
  successful_uploads: number;
  failed_uploads: number;
  files: FileUploadStatus[];
}

export interface DocumentListResponse {
  documents: DocumentMetadata[];
  total: number;
}
