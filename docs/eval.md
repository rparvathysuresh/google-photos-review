# Evaluation Criteria: AI-Powered Photo Retrieval Discovery Engine

> Phase-wise evaluation criteria aligned with the [implementation plan](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/implementation-plan.md). Each phase includes functional tests, quality metrics, acceptance criteria, and a sign-off checklist.

---

## Evaluation Approach

Each phase is evaluated across four dimensions:

| Dimension | What It Measures |
|---|---|
| **Functional Correctness** | Does the component do what it's supposed to do? |
| **Quality & Reliability** | Does it handle errors, edge cases, and produce consistent results? |
| **Performance** | Does it meet response time and throughput expectations? |
| **Integration** | Does it work correctly with components from previous phases? |

### Rating Scale

| Rating | Meaning |
|---|---|
| ✅ **Pass** | Meets all acceptance criteria |
| ⚠️ **Conditional** | Works but has known limitations documented |
| ❌ **Fail** | Does not meet minimum criteria; must be fixed before proceeding |

---

## Phase 1: Project Setup & Foundation

### 1.1 Functional Tests

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P1-F01 | Start FastAPI backend server | Server starts on `localhost:8000`; no errors in console | |
| P1-F02 | `GET /api/health` | Returns `200 OK` with `{ "status": "healthy" }` | |
| P1-F03 | Start Vite frontend dev server | Server starts on `localhost:5173`; renders app shell | |
| P1-F04 | Frontend → backend connectivity | Frontend can reach `/api/health` (CORS configured correctly) | |
| P1-F05 | Database auto-creation | SQLite file created at configured path on first startup | |
| P1-F06 | `FeedbackItem` model | Table `feedback_items` exists with all columns from architecture §3.1 | |
| P1-F07 | `RetrievalEpisode` model | Table `retrieval_episodes` exists with FK to `feedback_items` | |
| P1-F08 | `ProblemCluster` model | Table `problem_clusters` exists with all columns from architecture §3.4 | |
| P1-F09 | Environment config loading | Config loads from `.env`; fails gracefully if `GROQ_API_KEY` is missing | |
| P1-F10 | `.gitignore` validation | `.env`, `data/raw/`, `*.db`, `node_modules/`, `__pycache__/` are all ignored | |

### 1.2 Quality Criteria

| Criterion | Requirement |
|---|---|
| No startup errors | Both servers start without warnings or errors |
| Schema correctness | All model fields match architecture spec exactly |
| Config validation | Missing required env vars produce human-readable errors, not stack traces |
| Documentation | `README.md` has setup instructions for both backend and frontend |

### 1.3 Acceptance Criteria

- [ ] Backend starts and serves health check endpoint
- [ ] Frontend starts and renders navigation shell
- [ ] SQLite database auto-creates with correct schema
- [ ] All 3 ORM models importable and match architecture spec
- [ ] `.env.example` documents all required/optional variables
- [ ] Frontend can make API calls to backend (CORS working)

---

## Phase 2: Data Collection & Ingestion

### 2.1 Functional Tests

#### CSV/JSON Upload

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P2-F01 | Upload valid CSV (20 rows) | Returns `{ ingested: 20, duplicates: 0, skipped: 0 }` | |
| P2-F02 | Upload same CSV again | Returns `{ ingested: 0, duplicates: 20, skipped: 0 }` | |
| P2-F03 | Upload CSV with empty `text` rows | Rows with empty text skipped; others ingested | |
| P2-F04 | Upload CSV missing `text` column | Returns 400 with clear error message | |
| P2-F05 | Upload empty CSV (headers only) | Returns error: "No data rows found" | |
| P2-F06 | Upload JSON array of feedback | Items ingested correctly; source/date mapped | |
| P2-F07 | Upload large CSV (1000+ rows) | Completes without timeout; correct counts returned | |
| P2-F08 | `GET /api/ingest/status` | Returns accurate counts of total, relevant, pending | |

#### Source Adapters

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P2-F09 | Reddit scrape: valid subreddit + query | Returns items with `source: "reddit"`, correct metadata | |
| P2-F10 | Reddit scrape: invalid credentials | Returns clear auth error; no partial data stored | |
| P2-F11 | Reddit scrape: non-existent subreddit | Skips subreddit; returns results from others | |
| P2-F12 | YouTube scrape: valid query | Returns comments with `source: "youtube"`, `video_id` in metadata | |
| P2-F13 | YouTube scrape: video with disabled comments | Skips video; continues with others | |
| P2-F14 | Play Store scrape: Google Photos reviews | Returns reviews with `source: "playstore"`, ratings in metadata | |
| P2-F15 | Play Store scrape: wrong app ID | Returns clear error | |
| P2-F16 | Community adapter: valid thread | Returns thread + replies as separate `FeedbackItem`s | |
| P2-F17 | App Store adapter: valid query | Returns reviews with `source: "appstore"` | |
| P2-F18 | All adapters: consistent output | Every adapter produces valid `FeedbackItem` format | |

#### Deduplication

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P2-F19 | Same text, same source, same author | Deduped (1 stored, 1 skipped) | |
| P2-F20 | Same text, different author | Both stored (different fingerprints) | |
| P2-F21 | Same text with whitespace differences | Deduped after normalization | |
| P2-F22 | Cross-source: same text on Reddit and YouTube | Fingerprint dedup catches it if same author hash | |

### 2.2 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| Ingestion success rate | ≥ 95% of valid rows ingested | `ingested / (total - skipped)` |
| Dedup accuracy | 100% of exact duplicates caught | Upload same data twice; 0 new items second time |
| Adapter consistency | All adapters produce valid schema | Run schema validator on output of each adapter |
| Source attribution | 100% of items have `source` and `source_url` | Query DB for null source fields |

### 2.3 Performance Criteria

| Operation | Target |
|---|---|
| CSV upload (100 rows) | < 2 seconds |
| CSV upload (1000 rows) | < 10 seconds |
| Reddit scrape (100 posts) | < 60 seconds (API rate limited) |
| Dedup check (1000 items) | < 1 second |

### 2.4 Acceptance Criteria

- [ ] CSV/JSON upload works end-to-end with correct counts
- [ ] All 6 source types produce valid `FeedbackItem` records
- [ ] Deduplication prevents exact duplicates within and across sources
- [ ] Each adapter handles its specific error cases (auth, rate limit, not found)
- [ ] `/api/ingest/status` returns accurate counts
- [ ] Sample data (20-30 rows) available for testing subsequent phases

---

## Phase 3: AI Extraction Pipeline

### 3.1 Functional Tests

#### Relevance Classification

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P3-F01 | Classify clear photo-retrieval feedback | `is_relevant = true`, `relevance_score > 0.8` | |
| P3-F02 | Classify unrelated app review ("great app 5 stars") | `is_relevant = false`, `relevance_score < 0.3` | |
| P3-F03 | Classify ambiguous feedback | `is_relevant = true/false` with moderate score (0.4-0.7) | |
| P3-F04 | Batch classification (10 items) | All items classified; no crashes | |
| P3-F05 | Classification with Groq API failure | Item marked as `classification_pending`; batch continues | |

#### Structured Extraction

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P3-F06 | Extract from clear retrieval feedback | Valid `RetrievalEpisode` with populated fields | |
| P3-F07 | Extract from vague feedback | Episode created with some `null` fields; `user_goal` populated | |
| P3-F08 | Extract from irrelevant feedback | No episode created; item remains at `is_relevant = false` | |
| P3-F09 | Extraction produces valid JSON | Output parses correctly; all fields match schema | |
| P3-F10 | `supporting_evidence` is actual quote | Evidence string exists in the original `FeedbackItem.text` | |
| P3-F11 | Controlled vocabulary compliance | `memory_type`, `failure_reason`, `retrieval_method` use only valid enum values | |
| P3-F12 | Batch extraction (10 items) | All items processed; status updated per item | |
| P3-F13 | Extraction retry on API failure | Retries up to 3 times; marks as `failed` after exhaustion | |
| P3-F14 | Status tracking | `extraction_status` transitions: `pending → processing → completed/failed` | |
| P3-F15 | Re-extraction of previously extracted items | Old episode replaced with new extraction; `extracted_at` updated | |

### 3.2 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| Relevance accuracy | ≥ 85% agreement with human labels | Manually label 50 items; compare with classifier output |
| Extraction completeness | ≥ 70% of fields populated for relevant feedback | Count non-null fields per episode; average across dataset |
| Evidence faithfulness | ≥ 95% of `supporting_evidence` found in original text | Fuzzy substring match against source text |
| Schema compliance | 100% of extractions match JSON schema | Validate every extraction output against schema |
| Controlled vocabulary compliance | ≥ 95% use valid enum values | Check each enum field against allowed values |
| Extraction success rate | ≥ 90% of relevant items successfully extracted | `completed / (completed + failed)` |

### 3.3 Quality Evaluation Protocol

For a sample of **50 feedback items**, manually evaluate:

| Question | Rating (1-5) |
|---|---|
| Is `user_goal` accurately captured? | |
| Are `remembered_clues` correctly identified? | |
| Are `forgotten_info` items correct (not confused with remembered)? | |
| Is `retrieval_attempt` accurately described? | |
| Is `failure_reason` correctly classified? | |
| Is `memory_type` correct? | |
| Is `supporting_evidence` a genuine quote from the text? | |
| Are there any hallucinated details? | |

**Target**: Average rating ≥ 3.5/5 across all questions.

### 3.4 Performance Criteria

| Operation | Target |
|---|---|
| Single item relevance classification | < 2 seconds |
| Single item extraction | < 5 seconds |
| Batch of 10 items (classify + extract) | < 45 seconds |
| Full pipeline on 100 items | < 8 minutes |

### 3.5 Acceptance Criteria

- [ ] Relevance classifier correctly identifies photo-retrieval feedback (≥85% accuracy)
- [ ] Structured extraction produces valid `RetrievalEpisode` records
- [ ] `supporting_evidence` is faithfully quoted from source text (≥95%)
- [ ] All enum fields use controlled vocabulary values
- [ ] Batch processing handles API failures gracefully
- [ ] Status tracking works correctly across the extraction lifecycle
- [ ] Re-extraction support works for prompt iteration

---

## Phase 4: Embeddings & Vector Store

### 4.1 Functional Tests

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P4-F01 | ChromaDB initializes on startup | Persistent directory created; collections exist | |
| P4-F02 | Generate embedding for a single feedback item | Returns 1024-dim float vector | |
| P4-F03 | Generate embedding for a single episode | Returns 1024-dim float vector from concatenated text | |
| P4-F04 | Batch embed 50 feedback items | All 50 embeddings stored in `feedback_embeddings` collection | |
| P4-F05 | Batch embed 50 episodes | All 50 embeddings stored in `episode_embeddings` collection | |
| P4-F06 | Vector search: relevant query | Returns items semantically related to the query | |
| P4-F07 | Vector search: irrelevant query | Returns 0 results (all below similarity threshold) | |
| P4-F08 | Vector search with metadata filter | Only returns items matching filter criteria | |
| P4-F09 | Post-ingestion auto-embedding | New `FeedbackItem` is auto-embedded after CSV upload | |
| P4-F10 | Post-extraction auto-embedding | New `RetrievalEpisode` is auto-embedded after extraction | |
| P4-F11 | Delete feedback item → embedding removed | Embedding removed from ChromaDB when source record is deleted | |
| P4-F12 | Re-indexing endpoint | All embeddings regenerated; counts match relational DB | |
| P4-F13 | Health check includes ChromaDB | `/api/health` reports ChromaDB status | |

### 4.2 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| Embedding dimension | Exactly 1024 | Check vector length for BGE-large output |
| Semantic relevance (top-5) | ≥ 3/5 results are genuinely relevant | Manual evaluation of search results for 20 test queries |
| Index completeness | 100% of feedback + episodes have embeddings | Compare counts: relational DB vs ChromaDB collections |
| Embedding consistency | Same text → same embedding | Embed same text twice; verify identical vectors |
| Metadata accuracy | 100% of metadata fields correct | Spot-check 20 random entries against relational DB |

### 4.3 Semantic Search Quality Evaluation

For **20 test queries**, evaluate the top-5 results:

| Query | Relevant Results in Top-5 (out of 5) | Notes |
|---|---|---|
| "users who can't find vacation photos" | | |
| "screenshot retrieval failure" | | |
| "searching by person's face" | | |
| "forgot when a photo was taken" | | |
| "too many search results" | | |
| *(... 15 more domain-specific queries)* | | |

**Target**: Average ≥ 3.0 relevant results in top-5 (60% precision@5).

### 4.4 Performance Criteria

| Operation | Target |
|---|---|
| Single embedding generation (BGE) | < 100ms on GPU, < 500ms on CPU |
| Batch of 64 embeddings | < 3 seconds on GPU, < 15 seconds on CPU |
| Vector search (top-20, 10k collection) | < 200ms |
| Vector search (top-20, 50k collection) | < 500ms |
| Full re-indexing (1000 items) | < 5 minutes |

### 4.5 Acceptance Criteria

- [ ] ChromaDB initializes with both collections on startup
- [ ] BGE model generates 1024-dim embeddings correctly
- [ ] Batch embedding works for both feedback and episodes
- [ ] Vector search returns semantically relevant results (≥60% precision@5)
- [ ] Metadata filters work correctly
- [ ] Auto-embedding hooks fire after ingestion and extraction
- [ ] Health check covers ChromaDB status

---

## Phase 5: RAG Q&A Engine

### 5.1 Functional Tests

#### Basic RAG

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P5-F01 | Ask question with sufficient evidence | Returns grounded answer with ≥1 citation | |
| P5-F02 | Ask question with no evidence | Returns "Limited evidence available" message | |
| P5-F03 | Ask question with 1-2 evidence items | Returns answer prefixed with low-evidence warning | |
| P5-F04 | Empty question | Returns 400 error | |
| P5-F05 | Very long question (>2000 chars) | Returns 400 with max length error | |
| P5-F06 | Question unrelated to photo retrieval | Returns "not related to photo retrieval" message | |

#### Citations & Grounding

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P5-F07 | Citations reference real feedback items | Every `feedback_id` in citations exists in DB | |
| P5-F08 | Citation source URLs are valid | URLs in citations match the source `FeedbackItem.source_url` | |
| P5-F09 | Citation excerpts are from the actual source | Each excerpt is a substring of the cited `FeedbackItem.text` | |
| P5-F10 | Answer doesn't fabricate statistics | No percentages/numbers unless directly from evidence | |
| P5-F11 | Confidence rating reflects evidence quality | High evidence count → high confidence; low → low | |

#### Hybrid Retrieval

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P5-F12 | Vector-only search returns relevant results | Results are semantically relevant to the query | |
| P5-F13 | Keyword search finds exact term matches | Results contain the exact query terms | |
| P5-F14 | Hybrid merge produces better results than either alone | Combined results cover more relevant items | |
| P5-F15 | Reranking improves result ordering | Top results after reranking are more relevant | |

#### Filters & Advanced

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P5-F16 | Filter by source (e.g., Reddit only) | Only Reddit-sourced evidence in answer | |
| P5-F17 | Filter by date range | Only evidence within date range appears | |
| P5-F18 | Filter that excludes all data | Returns "No evidence matches filters" message | |
| P5-F19 | Query rewriting improves vague questions | Rewritten query produces more relevant results | |
| P5-F20 | Follow-up suggestions generated | Response includes 2-3 relevant follow-up questions | |
| P5-F21 | Q&A history stored and retrievable | Previous Q&A sessions accessible via `/api/ask/history` | |

### 5.2 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| Answer groundedness | ≥ 90% of claims backed by citations | Manual review of 30 Q&A pairs |
| Citation accuracy | 100% of citations reference valid source items | Automated validation against DB |
| Evidence diversity | ≥ 2 different sources cited per answer (when available) | Count distinct sources per answer |
| Answer relevance | ≥ 85% of answers directly address the question | Manual rating (relevant / partially relevant / irrelevant) |
| No fabrication | 0% fabricated quotes or statistics | Manual review of 30 answers |
| Follow-up quality | ≥ 70% of follow-ups are genuinely useful | Manual rating of follow-up suggestions |

### 5.3 RAG Quality Evaluation Protocol

For **30 test questions**, evaluate each answer:

| Question | Groundedness (1-5) | Relevance (1-5) | Citation Accuracy (Y/N) | Fabrication Found (Y/N) |
|---|---|---|---|---|
| "What kinds of old photos do users struggle to retrieve?" | | | | |
| "What information do users remember most often?" | | | | |
| "What retrieval workarounds do users use?" | | | | |
| "Show examples of users remembering an event but not the date." | | | | |
| "Which retrieval problems appear across multiple sources?" | | | | |
| "How do users describe visual memories they're searching for?" | | | | |
| "What makes photo search frustrating for large libraries?" | | | | |
| *(... 23 more questions)* | | | | |

**Targets**:
- Average groundedness ≥ 4.0/5
- Average relevance ≥ 3.5/5
- Citation accuracy: 100% valid
- Fabrication: 0 instances found

### 5.4 Performance Criteria

| Operation | Target |
|---|---|
| RAG Q&A (end-to-end, simple question) | < 5 seconds |
| RAG Q&A (end-to-end, complex question with filters) | < 8 seconds |
| Query embedding (BGE, local) | < 100ms |
| Vector retrieval (top-20) | < 200ms |
| Context assembly | < 50ms |
| Groq answer generation | < 3 seconds |

### 5.5 Acceptance Criteria

- [ ] Simple questions return grounded answers with citations in < 5 seconds
- [ ] Citations reference real, valid feedback items (100%)
- [ ] No fabricated quotes or statistics in any tested answer
- [ ] Low-evidence and no-evidence scenarios handled with appropriate warnings
- [ ] Hybrid retrieval produces better results than vector-only search
- [ ] Source and date range filters work correctly
- [ ] Follow-up suggestions are generated and relevant
- [ ] Q&A history is stored and retrievable

---

## Phase 6: Problem Clustering & Analysis

### 6.1 Functional Tests

#### Clustering

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P6-F01 | Cluster with ≥30 episodes | Produces 3-7 distinct clusters | |
| P6-F02 | Cluster with <10 episodes | Returns "Insufficient data" message | |
| P6-F03 | Re-cluster after new data ingestion | Cluster assignments update; old clusters may change | |
| P6-F04 | Noise points handled | Uncategorized episodes labeled as "Uncategorized / Mixed" | |
| P6-F05 | Cluster IDs assigned to episodes | Every episode has `problem_cluster` set (or "uncategorized") | |

#### Cluster Labelling

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P6-F06 | LLM generates cluster labels | Each cluster has a specific, descriptive label (not "Cluster 1") | |
| P6-F07 | LLM generates cluster summaries | Each cluster has a 2-3 sentence summary | |
| P6-F08 | Groq API failure during labelling | Falls back to seeded category labels | |

#### Cluster Profiles

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P6-F09 | Profile includes episode count | Count matches actual episodes in cluster | |
| P6-F10 | Profile includes common remembered clues | Top 3-5 clue types listed with frequencies | |
| P6-F11 | Profile includes common forgotten info | Top 3-5 forgotten info types listed | |
| P6-F12 | Profile includes failure reasons | Top failure reasons listed with frequencies | |
| P6-F13 | Profile includes source distribution | Per-source episode counts shown | |
| P6-F14 | Representative evidence selected | 3-5 most representative episodes included | |

#### Analytics

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P6-F15 | `GET /api/analytics/overview` | Returns total, relevant, episode, cluster counts | |
| P6-F16 | `GET /api/analytics/sources` | Returns per-source breakdown | |
| P6-F17 | `GET /api/analytics/distributions` | Returns memory type, failure reason distributions | |
| P6-F18 | `GET /api/analytics/trends` | Returns top remembered clues and forgotten info | |
| P6-F19 | Analytics on empty database | Returns all zeros; no errors | |

### 6.2 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| Cluster coherence | ≥ 70% of episodes in a cluster share a common theme | Manual review: sample 5 episodes per cluster, rate thematic coherence |
| Label accuracy | ≥ 80% of labels accurately describe the cluster content | Manual comparison of label vs. sampled episodes |
| Cluster stability | ≥ 70% of episodes remain in the same cluster on re-run | Run clustering twice; compute assignment overlap |
| Profile accuracy | All aggregate stats match actual data | Verify counts, frequencies against raw data |
| Seeded category coverage | ≥ 5 of 7 seeded categories represented | Check if major problem areas emerge in clusters |

### 6.3 Clustering Quality Evaluation Protocol

For each cluster produced, evaluate:

| Cluster Label | Episode Count | Coherence (1-5) | Label Accuracy (1-5) | Summary Quality (1-5) | Notes |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

**Targets**:
- Average coherence ≥ 3.5/5
- Average label accuracy ≥ 4.0/5
- Average summary quality ≥ 3.5/5

### 6.4 Performance Criteria

| Operation | Target |
|---|---|
| UMAP + HDBSCAN clustering (100 episodes) | < 10 seconds |
| UMAP + HDBSCAN clustering (1000 episodes) | < 60 seconds |
| Cluster labelling (all clusters) | < 30 seconds |
| Analytics overview query | < 200ms (cached) |
| Analytics distribution query | < 500ms (cached) |

### 6.5 Acceptance Criteria

- [ ] Clustering produces 3-7 meaningful clusters from ≥30 episodes
- [ ] Cluster labels are specific and descriptive (not generic)
- [ ] Cluster profiles contain accurate aggregate statistics
- [ ] ≥70% of episodes in each cluster share a common theme
- [ ] Re-clustering works and updates all references
- [ ] Analytics endpoints return correct data
- [ ] All analytics work on empty/minimal datasets without errors

---

## Phase 7: Research UI & Dashboard

### 7.1 Functional Tests

#### Design System & Shell

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P7-F01 | Dark theme renders correctly | All components use dark theme colors; no white flashes | |
| P7-F02 | Navigation works | Sidebar links navigate to Dashboard, Ask, Explore | |
| P7-F03 | Responsive layout (1920px) | Full sidebar + content; no overflow | |
| P7-F04 | Responsive layout (768px) | Collapsed sidebar or mobile nav; content readable | |
| P7-F05 | Google Fonts loaded | Inter and JetBrains Mono render correctly | |

#### Dashboard

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P7-F06 | Stat cards show correct numbers | Match `/api/analytics/overview` values | |
| P7-F07 | Source breakdown chart renders | Shows all sources with correct proportions | |
| P7-F08 | Empty state (no data) | Shows onboarding message, not blank charts | |
| P7-F09 | Upload CSV via drag-and-drop | File accepted; progress shown; stats update | |
| P7-F10 | Upload invalid file | Error message displayed; no crash | |
| P7-F11 | Trigger extraction button | Extraction starts; status updates on completion | |

#### Ask Engine

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P7-F12 | Submit question | Loading indicator shown; answer renders with markdown | |
| P7-F13 | Citation cards display | Expandable cards with source, excerpt, date, URL | |
| P7-F14 | Citation source link opens | External URL opens in new tab | |
| P7-F15 | Suggested questions clickable | Click fills input and submits | |
| P7-F16 | Follow-up chips clickable | Click submits the follow-up question | |
| P7-F17 | Filter by source | Multi-select works; answer uses only selected sources | |
| P7-F18 | Empty question submission | Error shown; no API call made | |
| P7-F19 | Long response renders correctly | Markdown formatting preserved; no overflow | |
| P7-F20 | Q&A history accessible | Previous questions visible in sidebar/panel | |

#### Problem Explorer

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P7-F21 | Cluster cards grid renders | Cards show label, summary, episode count | |
| P7-F22 | Sort by episode count | Cards reorder correctly | |
| P7-F23 | Click cluster card | Navigates to cluster detail page | |
| P7-F24 | Cluster detail: pattern breakdowns | Visual bars for clues, forgotten info, methods, failures | |
| P7-F25 | Cluster detail: evidence list | Evidence cards render with correct data | |
| P7-F26 | Cluster detail: source distribution | Mini chart shows source breakdown | |
| P7-F27 | Empty state (no clusters) | Message: "Clusters haven't been generated yet" | |
| P7-F28 | Back navigation works | Breadcrumb navigates back to explorer | |

#### Evidence Cards

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P7-F29 | Source badge color-coded | Reddit=orange, YouTube=red, PlayStore=green, etc. | |
| P7-F30 | Excerpt truncation | Long excerpts truncated with "Show more" | |
| P7-F31 | Expand/collapse animation | Smooth transition on expand/collapse | |
| P7-F32 | Source link opens externally | URL opens in new tab | |
| P7-F33 | Missing fields handled | Null fields hidden; card doesn't break | |

#### Auth & Production

| ID | Test | Expected Result | Status |
|---|---|---|---|
| P7-F34 | API key auth works | Valid key → access; invalid key → 403 | |
| P7-F35 | Login page renders | Form accepts API key; stores in session | |
| P7-F36 | Protected routes redirect | Unauthenticated user → login page | |
| P7-F37 | Rate limiting on `/api/ask` | Returns 429 after threshold exceeded | |
| P7-F38 | Production build works | `npm run build` succeeds; static files served correctly | |

### 7.2 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| First Contentful Paint | < 1.5 seconds | Lighthouse or browser DevTools |
| Largest Contentful Paint | < 2.5 seconds | Lighthouse |
| Time to Interactive | < 3 seconds | Lighthouse |
| Cumulative Layout Shift | < 0.1 | Lighthouse |
| Accessibility score | ≥ 80/100 | Lighthouse |
| No console errors | 0 errors in normal usage | Browser DevTools console |
| Cross-browser support | Works in Chrome, Firefox, Safari | Manual testing |

### 7.3 UX Quality Evaluation

| Criterion | Rating (1-5) | Notes |
|---|---|---|
| **Visual appeal**: Does the UI feel premium and modern? | | |
| **Dark theme**: Is the dark theme consistent and comfortable? | | |
| **Typography**: Is text readable and well-hierarchized? | | |
| **Animations**: Do micro-animations enhance UX without being distracting? | | |
| **Empty states**: Are empty states helpful (not blank screens)? | | |
| **Loading states**: Are loading indicators present and smooth? | | |
| **Error states**: Are errors user-friendly (not technical jargon)? | | |
| **Navigation**: Is it clear how to get between sections? | | |
| **Data density**: Does the dashboard show useful info without clutter? | | |
| **Evidence browsing**: Is it easy to explore evidence and drill down? | | |

**Target**: Average ≥ 3.5/5 across all criteria.

### 7.4 Performance Criteria

| Operation | Target |
|---|---|
| Dashboard load (cached analytics) | < 1 second |
| Ask Engine response display | < 5 seconds (including API call) |
| Problem Explorer load | < 2 seconds |
| Cluster detail page load | < 2 seconds |
| Evidence card expand/collapse | < 100ms animation |
| File upload (1MB CSV) | < 3 seconds |

### 7.5 Acceptance Criteria

- [ ] Design system produces a visually premium, modern dark-themed UI
- [ ] Dashboard shows correct metrics with animated charts
- [ ] CSV upload works end-to-end with drag-and-drop
- [ ] Ask Engine displays answers with expandable citation cards
- [ ] Follow-up suggestions and filter controls work
- [ ] Problem Explorer shows cluster cards with sort/filter
- [ ] Cluster detail page shows full pattern breakdown
- [ ] Evidence cards display correctly with source badges and expand/collapse
- [ ] Navigation between all pages works
- [ ] Empty states shown (not blank screens) when data is missing
- [ ] Login + API key auth works
- [ ] Production build runs without errors
- [ ] Lighthouse performance score ≥ 80

---

## End-to-End Evaluation

### E2E Flow Test

Run the complete pipeline from data upload to research insights:

| Step | Action | Validation | Status |
|---|---|---|---|
| 1 | Upload `sample_feedback.csv` (30 rows) | Items appear in DB; dashboard count updates | |
| 2 | Trigger extraction | Episodes created; extraction status = completed | |
| 3 | Verify embeddings | Both collections populated in ChromaDB | |
| 4 | Ask: "What photos do users struggle to find?" | Grounded answer with ≥1 citation | |
| 5 | Ask: "What do users remember vs forget?" | Answer distinguishes remembered and forgotten info | |
| 6 | Trigger clustering | 3+ clusters created with labels | |
| 7 | Open Problem Explorer | Cluster cards render with correct data | |
| 8 | Click a cluster | Detail page shows pattern breakdowns | |
| 9 | Click evidence card | Expands to show full episode details | |
| 10 | Verify source link | Opens original source URL | |

### Success Criteria (from Problem Statement)

| Criterion | Evaluation Method | Pass? |
|---|---|---|
| Reliably identify relevant photo-retrieval feedback | Test relevance classifier on 50 items; ≥85% accuracy | |
| Distinguish what users remember from what they forget | Inspect 20 episodes; verify remembered/forgotten correctly separated | |
| Identify recurring retrieval failure patterns | Verify clustering produces ≥3 meaningful problem areas | |
| Compare different retrieval problem areas using evidence | Verify cluster profiles contain comparative data | |
| Answer research questions with source-backed responses | Test 30 questions; verify all claims cite sources | |
| Allow every finding to be traced back to real feedback | Verify citation → FeedbackItem → source_url chain | |
| Surface meaningful opportunity areas | Verify clusters represent actionable problem areas, not just summaries | |

---

*This evaluation document should be used alongside the [implementation plan](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/implementation-plan.md) and [edge cases](file:///c:/Users/rparv/.antigravity-ide/Google%20Photos/docs/edge-cases.md). Update test results as each phase is completed.*
