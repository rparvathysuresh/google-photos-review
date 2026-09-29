# AI-Powered Photo Retrieval Discovery Engine

> A research tool that ingests multi-source user feedback about photo retrieval, extracts structured retrieval episodes using LLM, and provides RAG-based research Q&A to surface evidence-backed opportunity areas.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Groq API key](https://console.groq.com/)

### Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cd ..
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start the backend
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.
API docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Environment configuration
│   ├── db/
│   │   └── database.py      # SQLAlchemy engine & session
│   ├── models/
│   │   ├── feedback.py      # FeedbackItem model
│   │   ├── episode.py       # RetrievalEpisode model
│   │   └── cluster.py       # ProblemCluster model
│   ├── routers/             # API route handlers
│   └── services/            # Business logic
├── frontend/                # React + Vite UI
├── data/
│   └── sample/              # Sample test data
├── docs/                    # Architecture & planning docs
├── .env.example             # Environment template
└── README.md
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| Frontend | React + Vite |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Vector Store | ChromaDB |
| LLM | Groq (Llama 3 / Mixtral) |
| Embeddings | BGE `bge-large-en-v1.5` (local) |

## Documentation

- [Problem Statement](docs/problemstatement.txt)
- [Project Context](docs/context.md)
- [Architecture](docs/architecture.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Edge Cases](docs/edge-cases.md)
- [Evaluation Criteria](docs/eval.md)
