# GraphGuard AI — Frontend Foundation

Modern Next.js 15 (App Router) enterprise UI for the **GraphGuard AI** Multi-Modal Knowledge Graph Synthesis and GraphRAG platform.

---

## 🏗️ Architecture Overview

The frontend is built with clean architecture, strict TypeScript types, and high-performance React client/server components.

- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS v4 + Blue & Slate Curated Theme
- **State Management**: TanStack Query (React Query v5) for server state caching & automatic background polling
- **API Client**: Centralized Axios client with environment base URL resolution & unified error handling
- **Icons**: Lucide React
- **Animations**: Framer Motion & CSS transition micro-animations
- **Theme**: Light & Dark mode support with `ThemeProvider` & local storage persistence

---

## 📁 Directory Structure

```text
frontend/
├── src/
│   ├── app/                      # Next.js App Router pages & layouts
│   │   ├── (routes)/
│   │   │   ├── page.tsx          # / (Dashboard)
│   │   │   ├── upload/page.tsx   # /upload (Upload Documents)
│   │   │   ├── chat/page.tsx     # /chat (Compliance Assistant)
│   │   │   ├── graph/page.tsx    # /graph (Knowledge Graph)
│   │   │   ├── documents/page.tsx# /documents (Uploaded Documents)
│   │   │   └── settings/page.tsx # /settings (Project Settings)
│   │   ├── layout.tsx            # Root layout & providers
│   │   ├── globals.css           # Blue + Slate theme tokens & custom scrollbars
│   │   ├── loading.tsx           # Full-page loader
│   │   ├── not-found.tsx         # 404 Error page
│   │   └── error.tsx             # React Error Boundary
│   ├── components/
│   │   ├── layout/               # Shell layout components
│   │   │   ├── Sidebar.tsx       # Navigation sidebar with active page indicator
│   │   │   ├── TopNavbar.tsx     # System status indicator, Neo4j status & theme toggle
│   │   │   └── DashboardLayout.tsx # Integrated layout wrapper
│   │   └── ui/                   # Reusable atomic UI components
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Table.tsx
│   │       ├── Badge.tsx
│   │       ├── Loader.tsx
│   │       ├── EmptyState.tsx
│   │       ├── ErrorState.tsx
│   │       ├── PageHeader.tsx
│   │       ├── SectionCard.tsx
│   │       ├── StatusBadge.tsx
│   │       ├── SearchBar.tsx
│   │       └── ConfirmationDialog.tsx
│   ├── hooks/                    # Custom hooks
│   │   ├── useTheme.ts           # Theme mode state & toggling
│   │   ├── useToast.ts           # Toast notifications trigger
│   │   └── useHealth.ts          # Backend health polling hook
│   ├── lib/                      # Base utilities & client instances
│   │   ├── api-client.ts         # Axios client instance & interceptors
│   │   └── utils.ts              # `cn`, date & byte formatting helpers
│   ├── providers/                # React Context Providers
│   │   ├── QueryProvider.tsx     # TanStack React Query Provider
│   │   ├── ThemeProvider.tsx     # Theme Provider (Light/Dark)
│   │   └── ToastProvider.tsx     # Notification Toast Provider
│   ├── services/                 # Modular API services
│   │   ├── health.service.ts     # Health status endpoint
│   │   ├── upload.service.ts     # Upload documents service
│   │   ├── documents.service.ts  # Document catalog service
│   │   ├── graph.service.ts      # Graph data service
│   │   └── query.service.ts      # GraphRAG query service
│   └── types/                    # TypeScript interfaces & models
│       ├── api.ts                # API Response & Error models
│       ├── document.ts           # Document metadata models
│       ├── graph.ts              # Knowledge Graph node & edge models
│       ├── query.ts              # GraphRAG request, answer & citation models
│       └── health.ts             # Health check models
```

---

## 🚦 Navigation Routes

| Route | Page Title | Description |
|-------|------------|-------------|
| `/` | Dashboard | System metrics, quick actions, & architecture overview |
| `/upload` | Upload Documents | Drag-and-drop file ingestion interface |
| `/chat` | Compliance Assistant | Natural language GraphRAG query & citation interface |
| `/graph` | Knowledge Graph | Interactive visualizer for Neo4j node/edge networks |
| `/documents` | Uploaded Documents | Document catalog with status & metadata table |
| `/settings` | Project Settings | API parameters, Neo4j Aura inputs, & AI model settings |

---

## ⚙️ Environment Configuration

Copy or create `.env.local` in `frontend/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 🚀 Running Locally

```bash
# Install dependencies
npm install

# Start local dev server
npm run dev
```

The application will be running at `http://localhost:3000`.
