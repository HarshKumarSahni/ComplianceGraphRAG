# GraphGuard AI — Multi-Modal Enterprise Compliance Knowledge Graph & GraphRAG Platform

[![Next.js 16](https://img.shields.io/badge/Next.js-16.2-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Aura_DB-008CC1?logo=neo4j)](https://neo4j.com/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.0-06B6D4?logo=tailwindcss)](https://tailwindcss.com/)

> **GraphGuard AI** is a production-grade enterprise platform that synthesizes heterogeneous compliance documents—**PDF policies, CSV asset inventories, and MP3 audit recordings**—into a unified, queryable **Neo4j Knowledge Graph**. It enables grounded, natural language compliance query answering powered by **GraphRAG** with strict citation traceability and zero hallucination.
---

## 🌐 Website & Demo

- **🌍 Live Website:** [GraphGuard AI](https://compliance-graph-rag.vercel.app/)
- **🎥 Demo Video & Resources:** [Google Drive](https://drive.google.com/drive/folders/1LGP_0rx8xZLNk7KQHQNHfOCGmWib7Fd8)

---

## 🚀 Key Features

- **Multi-Modal Document Processing**: Ingests PDFs, CSVs, and MP3 audio files with automated text extraction and speech transcription.
- **Multi-Document Graph Merging**: Cross-document entity deduplication connects nodes across multiple uploaded files into one unified enterprise compliance graph.
- **Strict Grounded Extraction**: No hallucinated entities; every node and edge is linked back to verbatim document chunks.
- **Interactive 2D Graph Explorer**: Built with ReactFlow (`@xyflow/react`) featuring dynamic 2D grid spacing (prevents node overlap), live **Node Dropdown**, and **Relationship Dropdown** controls.
- **Natural Language GraphRAG**: Answers complex compliance questions with verbatim document snippet citations, confidence scores, and subgraph paths.
- **Strict Hallucination Containment**: Out-of-domain or unsupported queries trigger immediate refusal instead of making up answers.
- **Modern Next.js 16 UI**: Light / Dark mode toggle built with Tailwind CSS v4, live document management, and real-time query streaming.
- **Private Evaluation Suite**: Standalone automated evaluation scripts for calculating standard GraphRAG metrics against ground-truth datasets without LLM-as-judge overhead.
---

## 📊 Evaluation & Benchmark Performance

GraphGuard AI was evaluated using a private automated evaluation pipeline over a compliance knowledge base containing PDF policies and CSV audit logs. The system was tested using **Top-3 evidence retrieval (`top_k = 3`)** across **14 evaluation queries**, consisting of **10 answerable compliance questions** and **4 unsupported (out-of-domain) questions**. The benchmark measures retrieval quality, knowledge graph extraction accuracy, citation grounding, hallucination resistance, and end-to-end response quality. :contentReference[oaicite:0]{index=0}

### Official Performance Metrics

| Metric | Score |
|---------|:-----:|
| **Retrieval Precision@3** | **85.00%** |
| **Entity Extraction F1** | **92.86%** |
| **Hallucination Containment** | **100.00%** |
| **Citation Traceability** | **100.00%** |
| **Answer Match Rate** | **100.00%** |
| **Average Query Latency** | **10.84 sec** |

---

### Benchmark Highlights

- **Retrieval Precision@3:** Achieved **85.00%**, with highly relevant Top-3 evidence retrieved for answerable compliance queries. Most questions achieved perfect retrieval precision, with only a few partial matches reducing the overall average. :contentReference[oaicite:1]{index=1}
- **Entity Extraction:** Achieved an **F1 score of 92.86%**, with **100% Recall** and **86.67% Precision**, correctly extracting all expected entities while introducing only two false-positive entities. :contentReference[oaicite:2]{index=2}
- **Answer Accuracy:** All **10 answerable questions** produced responses containing every expected keyword and matched the ground-truth answers, resulting in a **100% Answer Match Rate**. :contentReference[oaicite:3]{index=3}
- **Hallucination Containment:** All **4 unsupported questions** were correctly refused with the response *"The available evidence does not contain sufficient information to answer this question."*, yielding **100% Hallucination Containment**. :contentReference[oaicite:4]{index=4}
- **Citation Traceability:** Every answerable response included citations that could be traced back to the original compliance documents, resulting in **100% Citation Traceability**. :contentReference[oaicite:5]{index=5}
- **System Performance:** The complete GraphRAG pipeline—including retrieval, knowledge graph traversal, and answer generation—achieved an average end-to-end latency of **10.84 seconds** across all evaluation queries. :contentReference[oaicite:6]{index=6}

---

### Evaluation Summary

The evaluation demonstrates that GraphGuard AI successfully delivers:

- 🎯 High-accuracy GraphRAG retrieval over heterogeneous compliance documents.
- 🕸️ Reliable entity and relationship extraction for Knowledge Graph construction.
- 📚 Fully grounded, citation-backed responses.
- 🛡️ Zero hallucinations on unsupported queries.
- ⚡ Consistent end-to-end response generation with an average latency of **10.84 seconds**.

These results validate GraphGuard AI as a trustworthy, explainable, and enterprise-ready compliance assistant capable of answering complex compliance queries while maintaining complete traceability to the original source documents.

### Evaluation Summary

The benchmark validates that GraphGuard AI successfully achieves the primary objectives of the challenge:

- 🔹 Accurate multi-document compliance retrieval using GraphRAG.
- 🔹 High-quality entity and relationship extraction into Neo4j.
- 🔹 Explainable, citation-backed responses grounded in source documents.
- 🔹 Zero hallucinations on unsupported queries.
- 🔹 Reliable and audit-ready compliance reasoning.

Overall, the evaluation demonstrates that GraphGuard AI provides **trustworthy, explainable, and enterprise-ready compliance assistance** by combining structured Knowledge Graph retrieval with LLM-powered reasoning over heterogeneous compliance documents.
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
  │                    - User-Scoped Multi-Tenant Isolation                     │
  └──────────────────────────────────────┬───────────────────────────────────────┘
                                         │
                                         ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                            GraphRAG Retrieval Engine                         │
  │        User Question ➔ Entity Extractor ➔ Subgraph Path Search ➔            │
  │        Top-3 Chunk Retrieval ➔ Grounded LLM Prompt ➔ Verbatim Citations     │
  └──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: Neo4j Aura Cloud Graph Database (`neo4j` driver v5.20+)
- **LLM Integration**: OpenRouter API (`anthropic/claude-3.5-sonnet` / `openai/gpt-4o-mini`)
- **Authentication**: JWT authentication (`pyjwt`, `passlib`, `bcrypt`) with user-isolated database scoping
- **Parsers**: PyMuPDF (`fitz`), pandas, faster-whisper
- **Cloud Storage**: Cloudinary SDK

### Frontend
- **Framework**: Next.js 16 (App Router, Turbopack, TypeScript)
- **Styling**: Tailwind CSS v4 (`@custom-variant dark`)
- **State & Data Fetching**: TanStack React Query v5
- **Graph Visualization**: React Flow (`@xyflow/react`)
- **Icons & UI**: Lucide React, Framer Motion

---

## 📂 Project Structure

```text
ComplianceGraphRAG/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── core/                   # Security, Config & Logger settings
│   │   ├── db/                     # Database engine & SQLite/Postgres setup
│   │   ├── dependencies/           # Auth & Client dependency injection
│   │   ├── models/                 # SQLAlchemy User Models
│   │   ├── repositories/           # Neo4j Graph & GraphReader Repositories
│   │   ├── routers/                # API Endpoints (auth, documents, graph, query)
│   │   ├── schemas/                # Pydantic schemas (RAG, auth, document)
│   │   └── services/               # Extraction pipeline, GraphRAG engine, Cloudinary
│   ├── tests/                      # Unit & integration test suite
│   ├── requirements.txt            # Python dependencies
│   └── uvicorn_runner.py           # Local uvicorn entrypoint
│
├── frontend/                       # Next.js 16 Frontend Dashboard
│   ├── src/
│   │   ├── app/                    # App Router pages (/, /login, /graph, /documents)
│   │   ├── components/             # Layout, Graph Explorer, UI components
│   │   ├── context/                # AuthContext & ThemeProvider
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── services/               # API clients (graph.service, documents.service)
│   │   └── types/                  # TypeScript interface definitions
│   ├── package.json
│   └── next.config.ts              # Next.js configuration
│
├── GraphGuard_Evaluation_Top3/     # Top-3 Evidence Evaluation Suite
│   ├── evaluate.py                 # Private evaluation runner
│   ├── evaluation_config.json      # Configuration (top_k=3)
│   ├── gold_entities.json          # Ground truth entities & aliases
│   ├── gold_relationships.json     # Ground truth relationships
│   └── questions.json              # Benchmark evaluation questions (Q1–Q14)
│
└── README.md                       # Project documentation
```

---

## ⚙️ Environment Configuration

### 1. Backend Configuration (`backend/.env`)

```env
PROJECT_NAME="GraphGuard AI"
ENVIRONMENT="development"
DEBUG=true
PORT=8000

# Security / Auth
SECRET_KEY="your-secret-key-change-this-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Neo4j Database
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# OpenRouter LLM
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_PRIMARY_MODEL=anthropic/claude-3.5-sonnet

# Cloudinary CDN
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 2. Frontend Configuration (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 💻 Running Locally

### 1. Start FastAPI Backend
```bash
cd backend
python3 -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```
- Interactive API documentation available at: `http://localhost:8000/docs`

### 2. Start Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
- Access the web interface at: `http://localhost:3000`

## 📂 Sample Dataset

To help you get started quickly, GraphGuard AI includes a small sample compliance dataset located in the `backend/data/` directory.

These files can be uploaded directly through the web interface to test the complete pipeline—from document ingestion and knowledge graph construction to GraphRAG-based question answering.

```text
backend/data/
├── sample3.pdf
├── sample_audit.csv
└── sample_policy.pdf
```

### Sample Files

- **`sample3.pdf`** – Sample Encryption Remediation Policy containing compliance rules, remediation procedures, and risk classifications.
- **`sample_audit.csv`** – Sample audit records with systems, controls, encryption status, and audit outcomes.
- **`sample_policy.pdf`** – Sample Data Protection Policy defining customer data handling requirements, encryption controls, and team responsibilities.

After uploading these files, GraphGuard AI will automatically:

- 📄 Parse and preprocess the documents
- 🧠 Extract entities and relationships
- 🕸️ Build the Neo4j Knowledge Graph
- 🤖 Enable GraphRAG-powered compliance question answering with source citations

These sample documents are the same dataset used for the benchmark evaluation included in this repository.

---

## 🧪 Running Private Evaluation Suite

The project includes an automated evaluation suite that benchmarks the deployed backend against ground-truth files without introducing LLM-as-judge bias or frontend overhead.

```bash
# Set target backend credentials
export EVAL_API_BASE_URL=https://your-backend.onrender.com
export EVAL_EMAIL=adi@gmail.com
export EVAL_PASSWORD=your_account_password

# Run the Top-3 Evaluation Benchmark
python3 GraphGuard_Evaluation_Top3/evaluate.py
```

### Generated Artifacts (`GraphGuard_Evaluation_Top3/`):
- `evaluation_results.json`: JSON output containing metrics, counts, and per-question breakdowns.
- `question_results.csv`: CSV summary of latency, citations, and source documents per question.
- `evidence_report.txt`: Human-readable text report showing verbatim response snippets and confidence scores.

---

## 📡 API Reference

| Endpoint | Method | Auth Required | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/auth/signup` | `POST` | No | Register new user account & return JWT token |
| `/api/v1/auth/login` | `POST` | No | Authenticate user & return JWT token |
| `/api/v1/auth/me` | `GET` | Yes | Get authenticated user profile |
| `/api/v1/health` | `GET` | No | System health check (API, Neo4j, Cloudinary, OpenRouter) |
| `/api/v1/documents` | `GET` | Yes | List user's ingested documents |
| `/api/v1/documents/upload` | `POST` | Yes | Upload multi-modal documents (PDF, CSV, MP3) |
| `/api/v1/documents/extract/{id}`| `POST` | Yes | Run AI entity & relationship extraction |
| `/api/v1/query` | `POST` | Yes | Execute GraphRAG compliance question query |
| `/api/v1/graph` | `GET` | Yes | Fetch user's Neo4j knowledge graph nodes & edges |
| `/api/v1/graph` | `DELETE` | Yes | Reset user's Knowledge Graph data |

---

