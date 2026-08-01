# GraphGuard AI — Multi-Modal Enterprise Compliance Knowledge Graph & GraphRAG Platform

> **GraphGuard AI** is a production-grade enterprise platform that synthesizes heterogeneous compliance documents—**PDF policies, CSV asset inventories, and MP3 audit recordings**—into a unified, queryable **Neo4j Knowledge Graph**. It enables grounded, natural language compliance query answering powered by **GraphRAG**.

---

## 🏛️ System Architecture

```text
                               MULTI-MODAL INGESTION PIPELINE
 ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
 │  PDF Regulatory Doc  │    │  CSV System Inventory│    │   MP3 Meeting Audio  │
 └──────────┬───────────┘    └──────────┬───────────┘    └──────────┬───────────┘
            │                           │                           │
            ▼                           ▼                           ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                             Cloudinary CDN Storage                           │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                    Parsing Engine (PyMuPDF / pandas / Whisper)               │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                    Semantic Chunker (Section & Paragraph Boundaries)          │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │               AI Knowledge Extraction (OpenRouter LLM + Prompts)             │
 │               - Extract Entities (Policies, Assets, Risks, Rules)            │
 │               - Extract Relationships (GOVERNS, STORES, VIOLATES)            │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                    Neo4j Aura Knowledge Graph Database                       │
 │                    - Cypher Property Graph Nodes & Directional Edges         │
 │                    - BAAI/bge-small-en-v1.5 Dense Vector Indexes           │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                            GraphRAG Retrieval Engine                         │
 │        User Question ➔ Entity Extractor ➔ Subgraph Path Search ➔            │
 │        Chunk Retrieval ➔ Grounded LLM Prompt ➔ Verbatim Citations           │
 └──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

- **Multi-Modal Document Processing**: Ingests PDFs, CSVs, and MP3 audio files with automated text extraction and transcription.
- **Strict Grounded Extraction**: No hallucinated entities; every node and edge is linked back to verbatim document chunks.
- **Neo4j Knowledge Graph Storage**: Persists property graphs with directional edges (`GOVERNS`, `STORES`, `USES`, `VIOLATES`, `OWNS`).
- **Hybrid Vector + Graph Retrieval**: Combines `sentence-transformers` vector search with 1–2 hop Cypher subgraph expansion.
- **Natural Language GraphRAG**: Answers complex compliance questions with verbatim document snippet citations, confidence scores, and subgraph paths.
- **Modern Next.js 15 UI**: Dark/Light mode, live system status polling, React Flow interactive graph canvas, and real-time upload progress.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.14)
- **Database**: Neo4j Aura Cloud Graph Database (`neo4j` driver v5.20+)
- **LLM Integration**: OpenRouter API (`openai/gpt-4o-mini`)
- **Embeddings**: SentenceTransformers (`BAAI/bge-small-en-v1.5`)
- **Parsers**: PyMuPDF (`fitz`), pandas, faster-whisper
- **Cloud Storage**: Cloudinary SDK

### Frontend
- **Framework**: Next.js 15 (App Router, TypeScript)
- **Styling**: Tailwind CSS v4 (Blue + Slate Enterprise Theme)
- **State & Data Fetching**: TanStack React Query v5
- **Graph Visualization**: React Flow (`@xyflow/react`)
- **Icons & UI**: Lucide React, shadcn/ui aesthetics

---

## ⚙️ Environment Configuration

### Backend Environment Variables (`backend/.env`)

```env
PROJECT_NAME="GraphGuard AI"
ENVIRONMENT="development"
DEBUG=true
PORT=8000

# Neo4j Database
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# OpenRouter LLM
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini

# Cloudinary CDN
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

### Frontend Environment Variables (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 💻 Running Locally

### 1. Start FastAPI Backend
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API docs available at: `http://localhost:8000/docs`

### 2. Start Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend web dashboard available at: `http://localhost:3000`

---

## 🌐 Production Deployment Guide

### Deploying Backend to Render
1. Create a Web Service on [Render](https://render.com/).
2. Root directory: `backend`.
3. Build Command: `pip install -r requirements.txt`.
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Health Check Path: `/api/v1/health`.
6. Add environment variables: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `OPENROUTER_API_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.

### Deploying Frontend to Vercel
1. Import repository on [Vercel](https://vercel.com/).
2. Root directory: `frontend`.
3. Add Environment Variable:
   `NEXT_PUBLIC_API_URL` = `https://graphguard-backend.onrender.com/api/v1`

*For full deployment details and troubleshooting, reference [deployment_guide.md](file:///C:/Users/harsh/.gemini/antigravity-ide/brain/c13d2b9b-ff05-49d3-83ec-71c3c834275e/deployment_guide.md).*

---

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health status of API, Neo4j, Cloudinary, and OpenRouter |
| `/api/v1/documents` | GET | List all ingested documents and metadata |
| `/api/v1/documents/upload` | POST | Upload multi-modal documents (PDF, CSV, MP3) |
| `/api/v1/documents/process/{id}` | POST | Execute semantic chunking pipeline |
| `/api/v1/documents/extract/{id}` | POST | Run AI entity and relationship extraction |
| `/api/v1/query` | POST | Execute GraphRAG compliance query |
| `/api/v1/graph` | GET | Fetch knowledge graph nodes and edges |

---

## 🧪 Testing Instructions

### Run Backend Unit & Integration Tests
```bash
cd backend
python -m pytest tests/ -v
```
*Result: 29 tests passing covering parser, chunker, extraction, GraphRAG engine, and API routes.*

### Run Frontend Production Build Check
```bash
cd frontend
npm run build
```
*Result: Clean TypeScript compilation & static generation for all routes (`/`, `/upload`, `/chat`, `/graph`, `/documents`, `/settings`).*
