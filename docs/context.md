# Project Context: AI-Powered Photo Retrieval Discovery Engine

## 1. Project Vision

Build an **evidence-driven AI discovery engine** that analyzes publicly available user feedback to understand how people retrieve old photos, videos, screenshots, and documents from large personal libraries — specifically when their memories are **incomplete** (e.g., they remember the trip but not the date, the person but not the album).

The system transforms raw, unstructured user conversations into actionable insights via the pipeline:

> **User Feedback → Retrieval Episodes → Patterns → Problem Areas → Opportunity Insights**

This is a **research tool**, not a product recommendation engine. Its purpose is to surface evidence-backed opportunity areas so product teams can decide what to build next.

---

## 2. Target Audience

| Role | How They Use the Engine |
|---|---|
| Product Managers | Research photo-retrieval pain points backed by real user evidence |
| UX Researchers | Conduct qualitative discovery and pattern analysis |
| Product/Design Teams | Explore opportunity areas in photo organization & retrieval |

---

## 3. Core Problem Being Studied

Photo retrieval breaks down when users have **incomplete memories**. The engine studies:

- **What users try to find** — photos, screenshots, documents, videos, images of people/objects.
- **What users remember** — person, location, event/trip, object, approximate time, activity, visual appearance, text/content, context.
- **What users forget** — exact date, exact location, album, filename, person/object name, exact search terms.
- **How users attempt retrieval** — keyword search, timeline browsing, albums, scrolling, face/person search, visual scanning, workarounds.
- **Why retrieval fails** — can't formulate the right query, too many results, forgotten date/location, context doesn't translate to keywords, difficulty describing a visual memory, uncertainty between similar results.

---

## 4. Architecture & Pipeline

### 4.1 Data Collection

Ingest publicly available user feedback from:

- Reddit discussions
- YouTube comments
- Google Photos Community / support discussions
- Google Play / App Store reviews (publicly accessible)
- Other relevant forums and public discussions
- **CSV/JSON uploads** of pre-collected public data

### 4.2 AI Discovery Pipeline

For each relevant feedback item, the AI extracts structured fields:

1. **Target** — what the user is trying to find.
2. **Remembered clues** — information the user still has.
3. **Forgotten information** — information the user has lost.
4. **Retrieval method** — how the user attempted to find it.
5. **Failure reason** — why the attempt failed.

### 4.3 Retrieval Episodes (Structured Output)

Each piece of relevant feedback is converted into a **Retrieval Episode** with:

| Field | Description |
|---|---|
| User Goal | What the user was trying to find |
| Remembered Clues | Information the user still has |
| Forgotten Information | Information the user has lost |
| Retrieval Attempt | How the user tried to find it |
| Failure Reason | Why the attempt failed |
| Memory Type | Category of the visual memory |
| Desired Outcome | What the user wished had happened |
| Original Source & URL | Attribution back to the raw feedback |
| Supporting Evidence | Excerpt from the original feedback |

### 4.4 RAG (Retrieval-Augmented Generation)

- Store raw feedback **and** structured episodes in a searchable / vector database.
- Support evidence-grounded Q&A such as:
  - "What kinds of old photos do users struggle to retrieve?"
  - "What information do users remember most often?"
  - "What retrieval workarounds do users use?"
  - "Show examples of users remembering an event but not the date."
- Every insight must be **traceable** to its underlying user evidence.

### 4.5 Problem & Opportunity Clustering

Automatically group retrieval episodes into recurring problem areas, e.g.:

- Event/trip-based retrieval
- People/context retrieval
- Visual-object retrieval
- Screenshot/document retrieval
- Location-based retrieval
- Approximate-time retrieval
- Text-inside-image retrieval

For each problem area, surface:

- Number of relevant retrieval episodes
- Common remembered clues
- Common forgotten information
- Current retrieval behaviour
- Common failure patterns
- Representative user evidence
- Sources in which the pattern appears

---

## 5. User Interface

### 5.1 Discovery Dashboard

High-level metrics:

- Total feedback analyzed
- Relevant feedback count
- Retrieval episodes generated
- Problem clusters identified
- Source breakdown

### 5.2 Ask the Research Engine

Conversational interface for asking research questions against the collected evidence (powered by RAG).

### 5.3 Problem Explorer

Browse and drill into individual problem areas — inspect patterns and supporting user evidence.

### 5.4 Evidence Cards

Each insight card shows:

- Source
- Short excerpt
- Date
- Retrieval pattern
- Original source link

---

## 6. Constraints

### Data & Evidence

- Use **only publicly available** user feedback.
- Preserve original source and URL for every data point.
- **Never fabricate** user quotes, statistics, or evidence.
- Clearly separate **direct evidence** from AI-generated interpretation.
- Do not present findings as representative of all Google Photos users.

### AI / RAG

- Use RAG for evidence retrieval; answers must be grounded in the dataset.
- Explicitly state when sufficient evidence is unavailable.
- Avoid generic sentiment analysis as the primary output.

### Privacy

- Do not intentionally collect or expose PII.
- Store only information necessary for research and source attribution.

---

## 7. Deliverables

### 7.1 Working AI Discovery Engine

- Data ingestion pipeline
- AI extraction of structured fields
- Retrieval Episode generation
- Embeddings / vector search
- RAG-powered Q&A
- Problem clustering
- Opportunity analysis

### 7.2 Minimal Research UI

- Dashboard
- Chat / research interface
- Problem explorer
- Evidence cards

### 7.3 README

- Setup instructions
- Architecture overview
- Data sources
- RAG approach
- AI extraction schema
- Known limitations

---

## 8. Success Criteria

The system should:

1. Reliably identify relevant photo-retrieval feedback from noisy sources.
2. Distinguish what users **remember** from what they **forget**.
3. Identify **recurring retrieval failure patterns**.
4. Compare different retrieval problem areas using evidence.
5. Answer research questions with **source-backed** responses.
6. Allow every major finding to be **traced back** to real user feedback.
7. Surface meaningful **opportunity areas** rather than merely summarizing reviews.

---

## 9. Key Design Decisions (To Be Made)

| Decision | Status | Choice |
|---|---|---|
| Vector DB | Decided | ChromaDB (dev) → Qdrant (prod) |
| LLM for extraction & RAG | ✅ Decided | **Groq** (Llama 3 / Mixtral) — ultra-fast inference via Groq API |
| Embedding model | ✅ Decided | **BGE `bge-large-en-v1.5`** — local inference, 1024-dim, fine-tunable |
| Backend framework | Decided | Python + FastAPI |
| Frontend framework | Decided | React + Vite |
| Data scraping strategy | Decided | API-based + CSV/JSON upload |
| Hosting / deployment | To Be Made | Local-first, cloud, or hybrid |

---

*This document is derived from [problemstatement.txt](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/problemstatement.txt) and serves as the living project context. Update it as architectural and design decisions are finalized.*
