# Streamlit Deployment Plan

This document outlines the strategy to pivot from a separated FastAPI/React architecture into a unified Python app on **Streamlit Community Cloud**.

Since Streamlit Community Cloud is optimized for pure Python applications, we will bypass the FastAPI and React layers entirely. Instead, we will build a new Streamlit UI (`app.py`) that imports our existing backend AI engines (RAG, Clustering, Ingestion) directly as Python modules.

---

## 1. Architecture Shift

**Current Architecture (Railway)**
- React Frontend -> FastAPI Backend -> Backend Services (SQLite, ChromaDB)

**New Architecture (Streamlit)**
- Streamlit UI (`app.py`) -> Backend Services (SQLite, ChromaDB)
*Note: We completely skip the API overhead! The Streamlit UI talks directly to the database and Groq.*

---

## 2. Implementation Steps

### Step 1: Create the Streamlit Entrypoint
Create a new file named `app.py` at the root of the repository. This file will:
1. Define the web interface using `import streamlit as st`.
2. Import `query_engine`, `vector_store`, and `clusterer` from the `backend.services` modules.
3. Provide interactive widgets for Ask AI, Problem Explorer, and the Dashboard.

### Step 2: Update Dependencies
Ensure the root `requirements.txt` contains Streamlit.
Add `streamlit>=1.32.0` to `requirements.txt`.

### Step 3: Handle State & Data Persistence
Streamlit Community Cloud resets its local storage when the app goes to sleep.
- **Temporary Persistence**: SQLite and ChromaDB will live on the container's ephemeral disk. The data will reset when the app sleeps.
- **To fix this**: We will add a "Re-Initialize Data" button in the Streamlit sidebar that runs the `ingest` scripts to fetch 100 app reviews and re-build the RAG vectors instantly when needed.

---

## 3. Deployment on Streamlit Cloud

1. Commit and push the new `app.py` and updated `requirements.txt` to the `main` branch of your GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **New app**.
4. Fill in the details:
   - **Repository**: `rparvathysuresh/google-photos-review`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click **Advanced settings** (before deploying!) and add your secret:
   - In the Secrets box, paste:
     ```toml
     GROQ_API_KEY = "your-groq-api-key"
     ```
6. Click **Deploy!**

---

## 4. Next Actions
- [ ] Create `app.py` (Streamlit UI).
- [ ] Add `streamlit` to `requirements.txt`.
- [ ] Push to GitHub.
- [ ] Deploy via Streamlit Community Cloud.
