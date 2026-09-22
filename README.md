# Contract Risk Analyzer

An AI-powered full-stack application that analyzes legal contracts for risk. Upload a PDF, DOCX, or TXT contract and get a clause-by-clause risk breakdown, an interactive Q&A interface, and an exportable PDF report.

> **Disclaimer:** This tool provides AI-generated analysis for informational purposes only and does not constitute legal advice.

---

## Features

- Upload PDF, DOCX, or TXT contracts (up to 10 MB)
- Automatic clause extraction and categorization
- Per-clause risk scoring (0–100) and risk level (Low / Medium / High)
- Detection of missing standard clauses
- Interactive contract Q&A powered by vector search
- Exportable PDF report with full analysis
- **Mock mode** — works without any API key for demos

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite (SQLAlchemy) |
| Vector Search | ChromaDB |
| Document Parsing | PyMuPDF, python-docx |
| LLM | OpenAI-compatible API |
| PDF Export | ReportLab |
| Frontend | React, Vite, Tailwind CSS |
| Containers | Docker, docker-compose |

---

## Quick Start (Local)

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env — add your OPENAI_API_KEY, or leave empty for mock mode

# Start server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: http://localhost:5173

---

## Mock Mode (No API Key Needed)

Leave `OPENAI_API_KEY` empty in `.env` — the app automatically uses realistic mock data. Perfect for demos and testing.

You can also force mock mode regardless of API key:
```
MOCK_MODE=true
```

---

## Docker

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API key (or leave empty for mock mode)

# Build and start
docker-compose up --build
```

App available at: http://localhost:80

---

## Testing

Upload the included sample contract:
```
backend/sample_contract.txt
```

This is a realistic service agreement with intentional risk clauses covering liability, IP, payment, and termination.

---

## Project Structure

```
contract-risk-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   ├── database.py      # SQLite models
│   │   ├── schemas.py       # Pydantic models
│   │   ├── routers/         # API endpoints
│   │   └── services/        # Business logic
│   └── sample_contract.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
├── docs/
│   ├── architecture.md
│   └── demo-script.md
├── docker-compose.yml
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload` | Upload a contract |
| GET | `/api/status/{id}` | Check analysis status |
| GET | `/api/analysis/{id}` | Get full analysis |
| POST | `/api/qa` | Ask a question |
| GET | `/api/report/{id}` | Download PDF report |
| GET | `/api/health` | Health check |
