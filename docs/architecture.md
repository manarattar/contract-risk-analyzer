# Architecture

## Data Flow

```
User uploads file
       ↓
FastAPI /upload endpoint
       ↓
Background task starts
       ↓
┌─────────────────────────────────────────────┐
│ 1. document_parser  → extract raw text       │
│ 2. clause_splitter  → split into chunks      │
│ 3. risk_analyzer    → LLM per-clause + summary│
│ 4. vector_store     → embed chunks → ChromaDB│
│ 5. SQLite           → store analysis JSON    │
└─────────────────────────────────────────────┘
       ↓
Frontend polls /status every 2s
       ↓
Status = "complete" → fetch /analysis
       ↓
Results rendered in React
```

## Components

### Backend

- **FastAPI** — REST API, CORS, background tasks
- **SQLite** — stores document metadata and full analysis JSON
- **ChromaDB** — vector store for semantic Q&A over contract chunks
- **LLM (OpenAI-compatible)** — clause-level risk analysis + overall summary
- **ReportLab** — PDF report generation with risk color coding

### Frontend

- **React + Vite** — SPA, state machine (idle → uploading → analyzing → results)
- **Tailwind CSS** — utility-first styling
- **react-dropzone** — file upload UX
- **Axios** — HTTP client

## Key Design Decisions

- **Background tasks**: analysis runs async; frontend polls `/status` to avoid HTTP timeout on large docs
- **Mock mode**: triggered when no API key is present; returns realistic hardcoded data so the app is always demeable
- **Clause splitting**: tries regex-based header detection first (numbered sections, ALL CAPS headers), falls back to paragraph splitting
- **Vector store per document**: each document gets its own ChromaDB collection, making Q&A fast and isolated
- **OpenAI-compatible**: works with OpenAI, Groq, Ollama, Azure OpenAI — just change `OPENAI_BASE_URL`
