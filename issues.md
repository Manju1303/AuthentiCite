# AuthentiCite Codebase Evaluation & Technical Audit Report (`issues.md`)

This report provides a comprehensive evaluation of the **AuthentiCite** codebase (Backend FastAPI, Plagiarism & Autonomous Research Agents, AI Generator, and Next.js Frontend).

---

## 📊 Summary of Codebase Evaluation

| Audit Domain | Status / Rating | Summary |
| :--- | :--- | :--- |
| **Backend Architecture** | 🟢 **Good (8.5/10)** | Well-structured FastAPI backend with multi-stage agents, RAG, and background tasks. |
| **Plagiarism & Research Engine** | 🟢 **Excellent (9.0/10)** | SBERT neural embeddings (`all-MiniLM-L6-v2`), N-gram winnowing, and live literature search APIs. |
| **Concurrency & Async** | 🟡 **Needs Improvement** | Mixing blocking sync `httpx.post` calls within async FastAPI request handlers. |
| **Database & Transaction Locks** | 🟡 **Moderate Risk** | SQLite WAL mode configured, but missing explicit transaction retry logic under background worker load. |
| **Frontend & API Integration** | 🟢 **Good (8.0/10)** | Clean React Next.js components with dashboard, comparison view, and live advisor. |

---

## 🚨 Detailed Issues & Risk Analysis

### 1. Concurrency & Synchronous I/O in Async Workers (High Severity)
- **Location**: `backend/app/rewrite/rewrite_engine.py` (`_rewrite_text_internal`) & `backend/app/similarity/citation_resolver.py`
- **Issue**: Synchronous `httpx.post(...)` calls are invoked inside FastAPI routes and background tasks (`run_autonomous_pipeline`).
- **Impact**: Under concurrent document uploads, blocking HTTP network requests stall the FastAPI asyncio event loop, causing request timeouts and high latency.
- **Recommended Fix**: Replace synchronous `httpx.post()` with `async httpx.AsyncClient().post()` across the rewrite engine pipeline.

---

### 2. SQLite Database Table Locking Under Concurrent Background Workers (Medium Severity)
- **Location**: `backend/app/database.py` & `backend/app/similarity/pipeline_worker.py`
- **Issue**: `run_autonomous_pipeline` executes multiple sequential SQLite queries (`update_paper_status`, `add_sections`, `update_section_rewrite`, `analyze_paper_similarity`).
- **Impact**: If multiple users upload documents simultaneously, SQLite may raise `sqlite3.OperationalError: database is locked`.
- **Recommended Fix**: Implement connection pooling or exponential retry decorators (`@retry_on_db_lock`) for SQLite writes, and set `PRAGMA busy_timeout = 60000;`.

---

### 3. Silent Fallback Without Failure Flagging in Rewrite Engine (Medium Severity)
- **Location**: `backend/app/rewrite/rewrite_engine.py` (Line 178)
- **Issue**: If all configured LLM API keys (Gemini, DeepSeek, Claude) fail or Ollama is offline, the function silently returns `"[Rewritten Fallback] " + text`.
- **Impact**: The user and background worker are unaware that AI rewriting failed, leading to raw manuscript text being retained with false zero similarity status.
- **Recommended Fix**: Raise a descriptive exception or set a `fallback_applied=True` warning flag in section metadata so the UI displays an editing alert.

---

### 4. Memory Usage during Large Manuscript & PDF/DOCX Parsing (Low-Medium Severity)
- **Location**: `backend/app/parser/pdf_parser.py` & `backend/app/parser/docx_parser.py`
- **Issue**: Uploaded files and extracted media/images are processed entirely in-memory without stream buffer size limits.
- **Impact**: Uploading extremely large PDFs (>100MB / 200+ pages) may trigger Out-Of-Memory (OOM) errors in containerized environments.
- **Recommended Fix**: Enforce maximum upload file size validation (`MAX_UPLOAD_SIZE = 50 * 1024 * 1024` bytes) in `/api/v1/papers/upload`.

---

### 5. False Positive Flagging on Common Headings & Citations (Low Severity)
- **Location**: `backend/app/similarity/analyzer.py` (Line 213)
- **Issue**: Default `SIMILARITY_THRESHOLD = 0.20` flags short standard academic phrases (e.g., *"Section II. Literature Review"* or citation titles).
- **Impact**: Inflation of flagged block counts on standard structural templates.
- **Recommended Fix**: Filter out short sentences (< 10 words) or standard section headers from similarity flagging.

---

### 6. Frontend Environment Configuration & Base URL Fallback (Low Severity)
- **Location**: `frontend/src/lib/api.ts`
- **Issue**: `API_BASE_URL` falls back to `http://localhost:8000/api/v1`.
- **Impact**: When deploying frontend to Vercel/Netlify without setting `NEXT_PUBLIC_API_URL`, network calls fail to reach backend.
- **Recommended Fix**: Add fallback validation and user-friendly connection toast messages when API server is unreachable.

---

## 🛠️ Action Plan & Next Steps

1. **Async Conversion**: Refactor `rewrite_engine.py` to use `httpx.AsyncClient`.
2. **DB Locking Mitigation**: Add `PRAGMA busy_timeout = 60000;` and write retries in `database.py`.
3. **Upload Guardrails**: Add 50MB file size limit check in `main.py`.
4. **Header Exclusion**: Exclude structural headers (< 10 words) from similarity indexing.
