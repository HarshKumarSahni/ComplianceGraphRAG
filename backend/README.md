# GraphGuard AI - FastAPI Backend Foundation

Production-ready FastAPI backend foundation for GraphGuard AI (Multi-Modal Knowledge Graph Synthesis for Enterprise Compliance).

## Setup & Local Development

### 1. Create Virtual Environment
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and adjust settings:
```bash
cp .env.example .env
```

### 4. Run Server
```bash
uvicorn app.main:app --reload --port 8000
```

Access API Documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Multi-Modal Upload Pipeline

The upload pipeline supports simultaneous multi-file uploads for enterprise compliance evidence.

### Supported Modalities & File Extensions
- **PDF Documents** (`.pdf`) - Policies, regulatory guidelines, compliance specs.
- **CSV Data Dumps** (`.csv`) - Infrastructure inventories, asset registers, user roles.
- **Audio Recordings** (`.mp3`) - Security audit recordings, compliance sync calls.

### Upload API Usage (`POST /api/v1/documents/upload`)
Upload multiple files simultaneously via `multipart/form-data`:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@GDPR_Policy.pdf" \
  -F "files=@Asset_Inventory.csv" \
  -F "files=@Audit_Meeting.mp3"
```

### Response Payload Structure
```json
{
  "success": true,
  "message": "Uploaded 3/3 files successfully",
  "data": {
    "total_files": 3,
    "successful_uploads": 3,
    "failed_uploads": 0,
    "files": [
      {
        "filename": "GDPR_Policy.pdf",
        "success": true,
        "metadata": {
          "document_id": "c7a6e11b-3d44-48b0-a5fb-39b06f8510a2",
          "original_filename": "GDPR_Policy.pdf",
          "cloudinary_url": "https://res.cloudinary.com/...",
          "public_id": "graphguard/c7a6e11b-3d44-48b0-a5fb-39b06f8510a2_GDPR_Policy.pdf",
          "upload_timestamp": "2026-08-01T13:14:00Z",
          "file_size_bytes": 1048576,
          "file_type": "pdf",
          "mime_type": "application/pdf",
          "status": "UPLOADED"
        }
## Multi-Modal Document Processing & Semantic Chunking Pipeline

Convert uploaded multi-modal evidence (PDF, CSV, Audio) into unified structured representation (`UnifiedDocument`) and generate context-aware semantic chunks.

### Pipeline Stages
1. **Parser Engine Selection**:
   - `PDFParser`: PyMuPDF layout-aware text block & page extraction.
   - `CSVParser`: Pandas-driven structured row-to-natural language conversion.
   - `AudioParser`: timestamped transcription via `faster-whisper`.
2. **Text Normalization (`DocumentNormalizer`)**:
   - Unicode NFKC normalization, control character removal, hyphenated line break merging, and whitespace sanitization.
3. **Sentence-Aware Semantic Chunking (`SemanticChunker`)**:
   - Sentence boundary-aware chunking preserving contextual overlap across sentences.
4. **Target Status Flow**:
   `UPLOADED` -> `PARSING` -> `NORMALIZING` -> `CHUNKING` -> `READY_FOR_ENTITY_EXTRACTION`

### Processing API Usage (`POST /api/v1/documents/process/{document_id}`)
Trigger parsing and semantic chunking for an uploaded document ID:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/process/c7a6e11b-3d44-48b0-a5fb-39b06f8510a2" \
  -H "accept: application/json"
```

### Processing Result Payload
```json
{
  "success": true,
  "message": "Document processed successfully. Status: READY_FOR_ENTITY_EXTRACTION",
  "data": {
    "document_id": "c7a6e11b-3d44-48b0-a5fb-39b06f8510a2",
    "status": "READY_FOR_ENTITY_EXTRACTION",
    "page_count": 1,
    "chunk_count": 3,
    "character_count": 1250,
    "estimated_tokens": 210,
    "chunks": [
      {
        "chunk_id": "c7a6e11b-3d44-48b0-a5fb-39b06f8510a2-chunk-0",
        "document_id": "c7a6e11b-3d44-48b0-a5fb-39b06f8510a2",
        "chunk_index": 0,
        "text": "First sentence for testing chunking...",
        "page_number": 1,
        "section_title": "Chunk 1",
        "metadata": {
          "source_file": "GDPR_Policy.pdf",
          "file_type": "pdf"
        },
## AI Knowledge Extraction Pipeline

Extracts validated entity nodes, relationship edges, and source-anchored `KnowledgeObject` structures from semantic document chunks using OpenRouter LLMs.

### Extraction Pipeline Architecture
1. **Prompt Engineering (`PromptBuilder`)**:
   - Strictly enforces JSON output schema, preventing hallucination by anchoring entities and relations to chunk text.
2. **LLM Extraction Engine (`OpenRouterClient`)**:
   - Communicates with OpenRouter API (`OPENROUTER_MODEL`, default `openai/gpt-4o-mini`) using JSON mode, exponential retries, and timeout controls. Includes deterministic fallback execution if API key is unconfigured.
3. **Strict Validation (`JSONValidator`)**:
   - Validates JSON output against Pydantic models (`ExtractionLLMOutput`). Rejects malformed structures gracefully.
4. **Entity Resolution (`EntityResolver`)**:
   - Normalizes case, removes whitespace, merges aliases, and deduplicates entity nodes across chunks.
5. **Target Status Flow**:
   `READY_FOR_ENTITY_EXTRACTION` -> `ENTITY_EXTRACTION` -> `RELATIONSHIP_EXTRACTION` -> `VALIDATION` -> `READY_FOR_GRAPH_BUILDING`

### Extraction API Usage (`POST /api/v1/documents/extract/{document_id}`)
Trigger AI knowledge extraction for a processed document ID:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/extract/c7a6e11b-3d44-48b0-a5fb-39b06f8510a2" \
  -H "accept: application/json"
```

### Extraction Result Payload (`ExtractionPipelineResult`)
```json
{
  "success": true,
  "message": "Knowledge extraction completed. Extracted 2 entities, 1 relationships.",
  "data": {
    "document_id": "c7a6e11b-3d44-48b0-a5fb-39b06f8510a2",
    "status": "READY_FOR_GRAPH_BUILDING",
    "chunk_count": 1,
    "entity_count": 2,
    "relationship_count": 1,
    "validation_errors": 0,
    "average_confidence": 0.96,
    "processing_time_seconds": 1.45,
    "knowledge_objects": [
      {
        "document_id": "c7a6e11b-3d44-48b0-a5fb-39b06f8510a2",
        "chunk_id": "c7a6e11b-3d44-48b0-a5fb-39b06f8510a2-chunk-0",
        "page_number": 1,
        "chunk_text": "GDPR Article 32 requires technical security for Customer Data Bucket.",
        "entities": [
          {
            "name": "GDPR Article 32",
            "type": "Regulation",
            "description": "Requires technical security.",
            "aliases": ["GDPR Art 32"],
            "confidence": 0.98
          },
          {
            "name": "Customer Data Bucket",
            "type": "Storage",
            "description": "AWS S3 Bucket.",
            "aliases": ["s3-customer-pii"],
            "confidence": 0.95
          }
        ],
        "relationships": [
          {
            "source_entity": "GDPR Article 32",
            "relationship_type": "GOVERNS",
            "target_entity": "Customer Data Bucket",
            "confidence": 0.94,
            "evidence": "GDPR Article 32 requires technical security for Customer Data Bucket."
          }
        ],
        "confidence_score": 0.965,
        "source_metadata": {
          "source_file": "GDPR_Policy.pdf"
        },
        "processing_timestamp": "2026-08-01T13:22:00Z"
      }
    ]
  }
}
```
