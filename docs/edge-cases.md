# Edge Cases & Corner Scenarios

> Comprehensive catalog of edge cases across every layer of the system, derived from the [architecture](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/architecture.md) and [implementation plan](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/implementation-plan.md).

---

## 1. Data Ingestion & Collection

### 1.1 CSV/JSON Upload

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 1 | Empty CSV file (headers only, no rows) | Return error: "File contains no data rows." No items created. | Medium |
| 2 | CSV with no header row | Attempt auto-detection; if columns can't be mapped, reject with clear error listing required columns. | Medium |
| 3 | CSV with extra/unknown columns | Ignore unknown columns; only map recognized fields. Log warning listing ignored columns. | Low |
| 4 | CSV missing required `text` column | Reject entire file with error: "Required column 'text' not found." | High |
| 5 | Row with empty/whitespace-only `text` field | Skip the row; increment `skipped_count` in response. | Medium |
| 6 | Row with extremely long text (>50,000 chars) | Truncate to max length (configurable, default: 10,000 chars). Log warning. Store truncated text. | Medium |
| 7 | Row with malformed `date` field | Set `date` to `null`; log warning. Do not reject the row. | Low |
| 8 | Row with invalid `source_url` (not a URL) | Store the value as-is but flag `source_url_valid = false`. | Low |
| 9 | JSON file with nested/non-flat structure | Reject if top-level is not an array of objects. Return error with expected schema. | Medium |
| 10 | File exceeds upload size limit (e.g., >100MB) | Reject at API layer before processing. Return 413 with max size info. | High |
| 11 | Non-UTF-8 encoded file | Attempt auto-detect encoding (chardet); fallback to latin-1. If decoding fails, reject with encoding error. | Medium |
| 12 | Upload while previous ingestion is still running | Queue the upload or return 409 conflict. Do not allow concurrent writes that could cause dedup races. | High |
| 13 | CSV with duplicate rows within the same file | Dedup within the file before DB insert. Report count in response. | Medium |
| 14 | Mixed CSV and JSON content (wrong file extension) | Detect format by content inspection, not extension. Try CSV first, then JSON. | Low |
| 15 | Upload with 100,000+ rows | Process in streaming/chunked batches (e.g., 1000 rows at a time). Return progress-aware response or job ID. | High |

### 1.2 Reddit Adapter

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 16 | Reddit API credentials invalid or expired | Fail fast with clear error. Do not proceed to scrape. Log auth failure. | High |
| 17 | Subreddit does not exist or is private | Skip that subreddit; log warning; continue with remaining subreddits. | Medium |
| 18 | Post has been deleted or removed | Skip deleted posts; handle `[deleted]` / `[removed]` body text gracefully. | Medium |
| 19 | Post/comment contains only images/links, no text | Skip if text body is empty after stripping markdown/URLs. | Low |
| 20 | Reddit API rate limit hit (429) | Implement backoff; pause and retry after `Retry-After` header. | High |
| 21 | Post body contains excessive markdown/formatting | Strip markdown formatting before storing; preserve plain text only. | Low |
| 22 | Unicode/emoji-heavy comments | Handle Unicode correctly; do not strip emojis (they may contain context). | Low |
| 23 | Very long thread with 1000+ comments | Paginate comment fetching; cap at configurable max (e.g., 500 comments per post). | Medium |
| 24 | Cross-posted content (same post in multiple subreddits) | Dedup by content fingerprint; store first occurrence only. | Medium |

### 1.3 YouTube Adapter

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 25 | YouTube API quota exhausted | Stop scraping; log remaining quota. Return partial results with warning. | High |
| 26 | Video has comments disabled | Skip video; log that comments were disabled. | Medium |
| 27 | Comment in non-English language | Store as-is; mark `language` in platform_metadata if detectable. Extraction may produce lower quality. | Medium |
| 28 | Comment is a reply to a reply (deeply nested) | Flatten to 2 levels max (comment → reply). Set `parent_id` correctly. | Low |
| 29 | Video has been deleted since search was performed | Handle 404 gracefully; skip and continue. | Medium |
| 30 | API key invalid | Fail fast with auth error. Do not retry. | High |

### 1.4 Google Play Store Adapter

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 31 | Reviews in non-English languages | Store with `language` metadata. Extraction quality may degrade for non-English. | Medium |
| 32 | Review text is just a rating (no text) | Skip reviews with empty text body. | Low |
| 33 | `google-play-scraper` rate-limited or blocked | Implement delays between batches; retry with exponential backoff. | High |
| 34 | App ID is incorrect or app not found | Return clear error with correct app ID suggestion. | Medium |
| 35 | Review contains developer reply | Store `reply_content` in platform_metadata. Do not treat reply as feedback. | Low |
| 36 | Review text contains only emojis/symbols | Store but flag as potentially low-value for extraction. | Low |

### 1.5 Community & App Store Adapters

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 37 | Google Photos Community page structure changes | HTML scraper breaks; detect parsing failures and alert. Use CSS selector versioning. | High |
| 38 | Thread has no replies (question only) | Store the question as a single `FeedbackItem`. | Low |
| 39 | Apple App Store region restrictions | Configure target country; handle 404s for unavailable regions. | Medium |
| 40 | Community thread marked as "resolved" | Still ingest; add `resolved: true` to platform_metadata. | Low |

### 1.6 Deduplication

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 41 | Same user posts nearly identical text on Reddit and YouTube | Fingerprint catches exact matches; semantic dedup (if enabled) catches paraphrased versions. | Medium |
| 42 | Same text but different `source_url` (re-posted content) | Fingerprint matches on text content; keep first, skip subsequent. | Medium |
| 43 | Text differs only in whitespace/capitalization | Normalize text before fingerprinting (strip, lowercase, collapse whitespace). | Medium |
| 44 | Legitimate similar feedback from different users | Should NOT be deduped — fingerprint includes `author_id`. Only identical author + text is deduped. | High |
| 45 | Author posted updated version of same review | Both versions stored (different text → different fingerprint). Not a dedup case. | Low |
| 46 | Fingerprint collision (different text, same hash) | Extremely unlikely with SHA-256 but handle gracefully; compare full text on collision. | Low |

---

## 2. AI Extraction Pipeline

### 2.1 Relevance Classification

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 47 | Feedback is ambiguous — partially about photo retrieval | Classify with `relevance_score` (e.g., 0.4-0.6). Store as relevant with low score. Allow filtering by threshold. | Medium |
| 48 | Feedback about a completely different app (false positive from scrape) | Relevance classifier marks as `is_relevant = false`. Do not extract episode. | Medium |
| 49 | Feedback discusses photo retrieval in a hypothetical context | Classify as relevant but with lower confidence. The LLM prompt should handle hypotheticals. | Low |
| 50 | Feedback is in a language Groq/Llama 3 handles poorly | Relevance score will be unreliable; mark `language_confidence: low` in metadata. | Medium |
| 51 | Groq API returns 429 (rate limit) during classification | Retry with exponential backoff. After max retries, mark item as `classification_pending`. | High |
| 52 | Groq API returns malformed response | Log error; mark item as `classification_failed`. Do not crash batch. | High |
| 53 | Feedback text is very short (<10 words) | Still attempt classification but expect lower accuracy. Flag as `short_text`. | Low |

### 2.2 Structured Extraction

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 54 | Feedback describes retrieval problem but with no specific details | Create episode with `user_goal` populated but most other fields as `null`/`unknown`. | Medium |
| 55 | Feedback contains multiple retrieval episodes in one text | Extract the **primary** episode. If clearly distinct, extract as separate episodes linked to same `FeedbackItem`. | High |
| 56 | LLM hallucinates details not present in text | Few-shot examples + grounding rules mitigate this. Validation step checks if `supporting_evidence` is actually a substring of original text. | Critical |
| 57 | LLM returns invalid JSON | Parse error → retry once with explicit "respond only with valid JSON" instruction. If still fails, mark as `extraction_failed`. | High |
| 58 | LLM returns JSON with unexpected/extra fields | Accept only known fields; silently drop extras. Log warning. | Medium |
| 59 | LLM returns JSON with missing required fields | Reject extraction; mark as `extraction_failed` with reason. | High |
| 60 | LLM uses vocabulary values not in the controlled list | Map to closest valid value or set to `other`. Log the unexpected value. | Medium |
| 61 | LLM response exceeds token limit / is truncated | Detect truncation (e.g., incomplete JSON). Retry with shorter input or simpler prompt. | High |
| 62 | `supporting_evidence` field contains fabricated quote | Post-extraction validation: check that the evidence string exists (fuzzy match) in the original text. Flag if not found. | Critical |
| 63 | Feedback text contains code snippets or structured data | LLM may misinterpret technical content. Extraction quality may degrade. | Low |
| 64 | Extraction prompt is updated but old episodes exist | Support re-extraction flag. Old episodes can be re-processed with new prompt. Track `prompt_version`. | Medium |
| 65 | Groq API timeout during extraction | Mark item as `extraction_pending` for retry. Continue with next item in batch. | High |
| 66 | Concurrent extraction requests for same item | Use optimistic locking on `extraction_status`. Second request should skip items already `processing`. | High |

---

## 3. Embeddings & Vector Store

### 3.1 Embedding Generation

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 67 | Text exceeds BGE model's max token length (512 tokens) | Truncate to 512 tokens. For long feedback, consider splitting into chunks. | High |
| 68 | Empty text after preprocessing | Skip embedding; log warning. Store null embedding reference. | Medium |
| 69 | Special characters / HTML entities in text | Clean text before embedding (strip HTML, decode entities). | Low |
| 70 | GPU out of memory during batch embedding | Reduce batch size dynamically; retry with smaller batches. Fallback to CPU if GPU fails. | High |
| 71 | BGE model file corrupted or missing on disk | Detect on startup; auto-download model via sentence-transformers. Clear error if download fails. | High |
| 72 | Embeddings generated with different model version than existing embeddings | Track `embedding_model_version` in metadata. Flag incompatible embeddings; offer re-indexing. | High |
| 73 | Episode has all null fields (no meaningful text to embed) | Generate a minimal embedding from `user_goal` alone. If that's also null, skip embedding. | Medium |

### 3.2 ChromaDB

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 74 | ChromaDB persistence directory doesn't exist | Auto-create directory on startup. | Low |
| 75 | ChromaDB data corruption (disk failure, interrupted write) | Detect on startup via health check. Log error; offer re-indexing from relational DB. | Critical |
| 76 | Collection doesn't exist on first query | Auto-create collection if it doesn't exist. Return empty results, not error. | Medium |
| 77 | Vector search returns 0 results | Return empty list; RAG layer handles low-evidence case. | Medium |
| 78 | Similarity scores are all below threshold | Return empty results; RAG layer triggers "insufficient evidence" message. | Medium |
| 79 | ChromaDB runs out of disk space | Detect write failures; alert user. Do not silently drop data. | Critical |
| 80 | Concurrent reads and writes to ChromaDB | ChromaDB handles this internally, but test under load. Use connection pooling if needed. | Medium |
| 81 | Metadata filter produces no matches but vector search has results | Return vector results without metadata filtering; log filter miss. | Low |
| 82 | Deleting a `FeedbackItem` that has embeddings in ChromaDB | Cascade delete: remove embedding from vector store when relational record is deleted. | Medium |

---

## 4. RAG Q&A Engine

### 4.1 Query Processing

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 83 | User asks a question unrelated to photo retrieval | Return: "This question doesn't appear to relate to photo retrieval. Please ask about how users find or search for photos." | Medium |
| 84 | User asks an extremely broad question ("Tell me everything") | Query rewriting narrows it down; or return top-level summary with suggested specific questions. | Medium |
| 85 | User asks a very specific question with no matching evidence | Return: "Limited evidence available (0 sources). The dataset does not contain sufficient evidence to answer this question." | Medium |
| 86 | User sends empty/whitespace-only question | Return 400 error: "Question cannot be empty." | Low |
| 87 | User sends extremely long question (>2000 chars) | Truncate or reject with max length error. | Low |
| 88 | User asks in a non-English language | Attempt to process; quality may degrade. Suggest asking in English. | Medium |
| 89 | User sends rapid-fire questions (potential abuse) | Rate limiting returns 429 after threshold (e.g., 10 questions/minute). | Medium |

### 4.2 Retrieval & Context Assembly

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 90 | Retrieved documents are all from the same source | Note in response: "Evidence is based on [source] only — other sources did not contain relevant data." | Medium |
| 91 | Context window exceeds `max_context_tokens` limit | Truncate lower-ranked documents until within limit. Prioritize diversity (different sources). | High |
| 92 | All retrieved documents are near the similarity threshold | Lower confidence rating in response. Prefix with "The following evidence is weakly related." | Medium |
| 93 | Retrieved feedback items have been deleted from relational DB | Handle orphaned vector entries gracefully; skip and log. Suggest re-indexing. | Medium |
| 94 | Multiple retrieved documents are from the same original thread | Deduplicate by `thread_id`; keep the most relevant post from each thread. | Medium |
| 95 | Query embedding fails (BGE model issue) | Return 503 with error. Do not fall back to random results. | High |

### 4.3 Answer Generation

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 96 | Groq API is down / unreachable | Return 503: "The research engine is temporarily unavailable. Please try again later." | Critical |
| 97 | Groq returns answer that contradicts the evidence | Post-generation check: validate that cited sources support the claims. If mismatch detected, add warning. | High |
| 98 | Groq returns answer with citations to non-existent sources | Map citation indices to actual retrieved documents. Drop citations that don't match. | High |
| 99 | Groq response is cut off (token limit) | Detect incomplete response; retry with shorter context or add "Please provide a concise answer." | High |
| 100 | Answer contains PII from feedback text | Do not filter PII from answers (we only store public data), but ensure author names are hashed. | Medium |
| 101 | Follow-up suggestion generation fails | Silently omit suggestions from response; log error. Core answer still returned. | Low |

### 4.4 Hybrid Retrieval

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 102 | Keyword search returns results but vector search returns nothing | Rely on keyword results only; note lower confidence. | Medium |
| 103 | Vector search and keyword search return completely different results | Both sets are valid; merge with reciprocal rank fusion. Let reranker decide final order. | Medium |
| 104 | User applies filters that exclude all data | Return: "No evidence matches the selected filters. Try broadening your criteria." | Medium |
| 105 | Date range filter covers period with no data | Return empty results with helpful message. | Low |

---

## 5. Problem Clustering

### 5.1 UMAP + HDBSCAN

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 106 | Fewer than 10 episodes exist (insufficient for clustering) | Skip clustering; return message: "Insufficient data for clustering. Minimum: 10 episodes." | Medium |
| 107 | All episodes are very similar (single cluster) | HDBSCAN may produce 1 cluster + noise. Accept this; label the single cluster appropriately. | Medium |
| 108 | All episodes are very different (no natural clusters) | HDBSCAN assigns all to noise. Return "No clear problem clusters found" with individual episodes. | Medium |
| 109 | Very large number of episodes (10,000+) | UMAP and HDBSCAN can handle this but may be slow. Run asynchronously with progress tracking. | Medium |
| 110 | Re-clustering produces completely different clusters than before | Cluster IDs change. Update all `RetrievalEpisode.problem_cluster` references. Invalidate cached profiles. | High |
| 111 | UMAP/HDBSCAN library throws numerical error | Catch exceptions; log parameters. Retry with adjusted hyperparameters. If persists, report error. | High |
| 112 | Embeddings have NaN or Inf values | Validate embeddings before clustering. Remove or re-generate invalid entries. | High |
| 113 | Cluster sizes are extremely imbalanced (1 cluster has 90% of episodes) | Flag as warning in cluster profiles. May indicate poor embedding quality or genuinely dominant problem area. | Medium |

### 5.2 Cluster Labelling

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 114 | LLM generates a generic label (e.g., "Photo Problems") | Validation step checks label quality. Re-prompt with more representative episodes if label is too generic. | Medium |
| 115 | LLM generates a label that doesn't match the cluster content | Include representative evidence in the prompt to ground the labelling. | Medium |
| 116 | Cluster has only noise-point episodes (low quality) | Label as "Uncategorized / Mixed" with disclaimer. | Low |
| 117 | Groq API fails during labelling | Use seeded category labels as fallback. Retry labelling later. | Medium |

### 5.3 Analytics & Metrics

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 118 | Database is empty (no feedback ingested yet) | Dashboard shows all zeros. Display "Get started by uploading feedback data." | Low |
| 119 | Only irrelevant feedback exists (0 episodes) | Show feedback count but zero episodes, zero clusters. Suggest refining data collection. | Medium |
| 120 | Source distribution is 100% from one source | Display correctly; note single-source limitation. | Low |
| 121 | Metrics cache stale after new ingestion | Invalidate cache on ingestion events. If cache fails, compute on-the-fly. | Medium |
| 122 | Analytics query on very large dataset is slow | Implement query timeouts; use materialized views or pre-aggregated tables for common queries. | Medium |

---

## 6. Research UI

### 6.1 Dashboard

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 123 | Dashboard loads with no data | Show empty state with onboarding guide: "Upload your first dataset to get started." | Medium |
| 124 | Dashboard stat cards show very large numbers (1,000,000+) | Format with abbreviations (e.g., 1.2M) or locale-specific formatting. | Low |
| 125 | Chart data has only 1 data point | Show single bar/point; don't display empty chart. | Low |
| 126 | Browser window resized to very small viewport | Responsive design collapses sidebar; charts resize. Minimum supported width: 768px. | Medium |
| 127 | User navigates to dashboard while data is being ingested | Show stale data with "Data ingestion in progress..." indicator. Auto-refresh when complete. | Medium |

### 6.2 Ask Engine

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 128 | User submits question and immediately navigates away | Abort the API request (AbortController). Don't display stale answers on return. | Medium |
| 129 | RAG response takes >30 seconds | Show timeout message after 30s. Offer "Try again" button. | High |
| 130 | Markdown in RAG response renders incorrectly | Sanitize markdown; handle edge cases (unclosed tags, nested formatting). | Medium |
| 131 | Citation card links to a deleted/moved source URL | Show the URL but indicate "Source may no longer be available." Link still clickable. | Low |
| 132 | User pastes extremely long text into the question input | Client-side max length enforcement (2000 chars). Show character counter. | Low |
| 133 | Suggested follow-up question returns no results | Handle gracefully — show "No evidence found" for the follow-up too. | Low |
| 134 | User asks the same question twice | Return fresh results (don't cache Q&A). Different evidence may be relevant each time. | Low |

### 6.3 Problem Explorer

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 135 | No clusters exist yet | Show empty state: "Clusters haven't been generated yet. Ensure you have at least 10 retrieval episodes." | Medium |
| 136 | Cluster has zero episodes after re-clustering | Remove the empty cluster from the UI. Don't show cards with "0 episodes." | Medium |
| 137 | User clicks a cluster deep link (URL) but cluster no longer exists | Show 404 page: "This problem cluster no longer exists. It may have been merged during re-clustering." | Medium |
| 138 | Cluster detail page with 500+ evidence cards | Paginate evidence cards (20 per page). Lazy-load on scroll. | Medium |

### 6.4 Evidence Cards

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 139 | Supporting evidence excerpt is very long (>500 chars) | Truncate to 300 chars with "..." and "Show more" button. | Low |
| 140 | Source URL is malformed or missing | Show "Source unavailable" instead of broken link. | Low |
| 141 | Evidence card has all `null` fields except text | Show the text and source badge only. Hide empty fields. | Low |
| 142 | Multiple evidence cards are from the same source/author | Display normally but consider showing a "Same source" indicator. | Low |

---

## 7. Authentication & Security

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 143 | API key is missing from request header | Return 401: "API key required." | High |
| 144 | API key is invalid / revoked | Return 403: "Invalid API key." | High |
| 145 | Rate limit exceeded on `/api/ask` | Return 429 with `Retry-After` header. | Medium |
| 146 | CORS request from unauthorized origin | Block request; return CORS error. | Medium |
| 147 | SQL injection attempt in filter parameters | Parameterized queries (SQLAlchemy ORM) prevent injection. Log the attempt. | Critical |
| 148 | XSS in feedback text rendered in UI | Sanitize all user-generated content before rendering. Use React's default escaping. | Critical |
| 149 | `.env` file committed to version control | `.gitignore` must include `.env`. Pre-commit hook to catch accidental commits. | Critical |
| 150 | PII leaks in feedback text (email, phone number) | Optional PII detection pass during ingestion; flag but don't auto-redact (may lose context). | Medium |

---

## 8. Infrastructure & Operations

### 8.1 Database

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 151 | SQLite file is locked by another process | Use WAL mode for concurrent read access. Show clear error if write lock fails. | High |
| 152 | SQLite database file grows beyond disk space | Monitor disk usage; alert when >80% full. | Critical |
| 153 | Migration fails midway (Alembic) | Alembic handles rollback on failure. Log the error with migration version. | High |
| 154 | PostgreSQL connection pool exhausted | Queue requests; return 503 after timeout. Increase pool size in config. | High |
| 155 | Database schema mismatch after code update | Auto-detect migration needed on startup; prompt to run migrations. | High |

### 8.2 Vector Database Migration

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 156 | ChromaDB → Qdrant migration loses metadata | Validate metadata completeness after migration. Compare counts and spot-check. | Critical |
| 157 | Embedding dimensions mismatch between old and new vector DB | Verify dimension config matches model output (1024 for BGE-large). | Critical |
| 158 | Migration interrupted midway | Support resumable migration (track last migrated ID). | High |

### 8.3 External APIs

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 159 | Groq API deprecates the model endpoint | Monitor for deprecation notices. Have fallback model config (e.g., switch Llama 3 → Mixtral). | High |
| 160 | Groq API pricing changes | Budget monitoring; alert on cost spikes. | Medium |
| 161 | Reddit API ToS changes restrict scraping | Adapter should be modular enough to disable. Fall back to CSV upload for Reddit data. | Medium |
| 162 | YouTube API quota reduction | Implement quota tracking per adapter. Alert before quota exhaustion. | Medium |
| 163 | BGE model is removed from HuggingFace Hub | Pin model version in config; maintain local cache of downloaded model. | Medium |

### 8.4 Performance

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 164 | Embedding generation for 10,000 items takes hours on CPU | Detect GPU availability; warn if running on CPU with large dataset. Suggest batch size reduction. | Medium |
| 165 | RAG query on large vector DB (>50k embeddings) is slow | Monitor query latency; optimize `top_k` and indexing. Consider switching to Qdrant. | Medium |
| 166 | Multiple users hit `/api/ask` simultaneously | Groq API handles concurrency; but queue requests if exceeding API rate limits. | Medium |
| 167 | Frontend loads with stale cached JavaScript | Use content hashing in build (Vite does this by default). | Low |
| 168 | Health check reports DB healthy but vector store is down | Health check must verify ALL services independently; report partial health. | Medium |

---

## 9. Data Quality & Integrity

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 169 | Feedback text contains mostly URLs and no natural language | Extraction produces poor episodes. Consider filtering out URL-only feedback at relevance stage. | Medium |
| 170 | All ingested feedback is from a single user (astroturfing) | Analytics should show author distribution. Flag if >50% from one author_id. | Medium |
| 171 | Feedback text is clearly spam/promotional | Relevance classifier should filter this out. If it passes, extraction will produce low-quality episodes. | Medium |
| 172 | Feedback contradicts itself within the same text | LLM extracts what's present. May result in conflicting `remembered_clues` and `forgotten_info`. | Low |
| 173 | Historical feedback references features that no longer exist | Still relevant for analysis — shows historical retrieval challenges. Add `date` context. | Low |
| 174 | Feedback is a feature request, not a retrieval problem | Relevance classifier should flag as borderline. May produce episodes with `failure_reason: "feature_missing"`. | Medium |
| 175 | RetrievalEpisode references a FeedbackItem that was deleted | Foreign key constraint prevents orphaned episodes. Cascade delete or block deletion. | High |
| 176 | Re-ingestion of same source after schema change | Track `schema_version` on episodes. Allow re-extraction with new schema without losing old data. | Medium |

---

## 10. Cross-Cutting Concerns

| # | Edge Case | Expected Behavior | Severity |
|---|---|---|---|
| 177 | Server crashes mid-extraction (power failure, OOM kill) | On restart, detect `processing` status items and reset to `pending` for retry. | High |
| 178 | Disk full during any write operation | Catch `OSError`; return 507 (Insufficient Storage). Log urgently. | Critical |
| 179 | System clock skew (wrong timestamps) | Use UTC everywhere. Warn if system clock appears significantly off. | Medium |
| 180 | Logging produces PII in log files | Sanitize log output; never log full feedback text or author identifiers. | High |
| 181 | Multiple environment files (.env.prod, .env.dev) | Config loader should accept `ENV` variable to select the right file. | Low |
| 182 | Python dependency conflicts between packages | Pin all versions in `requirements.txt`. Use virtual environments. | Medium |
| 183 | Frontend and backend on different ports in development | CORS configured to allow `localhost:5173` (Vite) → `localhost:8000` (FastAPI). | Low |
| 184 | Browser localStorage full (Q&A history, auth tokens) | Handle `QuotaExceededError`; clear oldest history entries. | Low |

---

## Summary by Severity

| Severity | Count | Action |
|---|---|---|
| **Critical** | 9 | Must handle before any deployment. System integrity at risk. |
| **High** | 42 | Must handle in the phase where the component is built. |
| **Medium** | 88 | Handle during integration testing or Phase 7 polish. |
| **Low** | 45 | Nice-to-have; handle if time permits or when discovered in usage. |

---

*This document covers edge cases for all components defined in the [architecture](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/architecture.md) and [implementation plan](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/implementation-plan.md). Review and update as new edge cases are discovered during development.*
