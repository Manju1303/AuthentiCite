# Implementation Plan - Integrate Advanced AI & Plagiarism Stack

This plan outlines the integration of:
1. **CrewAI** for multi-agent paper rewriting.
2. **Marker** for high-fidelity PDF parsing (IEEE style).
3. **CopyLeaks API** for external plagiarism checks.
4. **Gemma 3 / Qwen 3 / Llama 3.3** via Ollama/Gemini as the rewrite models.
5. **LibreOffice Headless** verification details.
6. A free deployment method for FastAPI and Next.js with unlimited live hosting.

## User Review Required

> [!IMPORTANT]
> - **Heavy AI dependencies (Marker and CrewAI)** will be implemented with programmatic try-except imports. If PyTorch, CUDA, or CrewAI packages are not present locally, they will fail gracefully and fall back to the existing TF-IDF/PyPDF/Direct LLM pipelines.
> - **CopyLeaks API** requires credential configurations in `.env`. We will implement a configurable switch (`USE_COPYLEAKS`).

## Proposed Changes

---

### 1. Configuration Settings

#### [MODIFY] [config.py](file:///d:/Github/plagarism/backend/app/config.py)
Add settings for:
- `COPYLEAKS_EMAIL` and `COPYLEAKS_API_KEY`
- `USE_COPYLEAKS` (boolean flag to toggle CopyLeaks vs. local TF-IDF analyzer)
- `USE_CREWAI` (boolean flag to toggle CrewAI multi-agent rewriting)
- `USE_MARKER` (boolean flag to toggle Marker-pdf parser)

---

### 2. Multi-Agent Orchestration (CrewAI)

#### [NEW] [crew_rewriter.py](file:///d:/Github/plagarism/backend/app/rewrite/crew_rewriter.py)
Implement a multi-agent system:
- **Academic Researcher Agent**: Extract context and preserve formulas.
- **Peer Reviewer Agent**: Evaluate similarity and suggest structural shifts.
- **Copy Editor Agent**: Finalize the paragraph rewrite using a scientific tone.
- Graceful fallback: If CrewAI or langchain packages cannot be imported, default to direct single-turn LLM calls.

---

### 3. PDF Parsing (Marker)

#### [NEW] [marker_parser.py](file:///d:/Github/plagarism/backend/app/parser/marker_parser.py)
Integrate `marker-pdf` parser programmatically:
- Convert the PDF pages to clean Markdown, extracting sections, mathematical LaTeX formulas, and tables.
- Fallback: Default to standard `pypdf` + `tesseract` OCR if `marker` is not installed.

---

### 4. Plagiarism Analysis (CopyLeaks API)

#### [NEW] [copyleaks_service.py](file:///d:/Github/plagarism/backend/app/similarity/copyleaks_service.py)
Implement the CopyLeaks Scan API client:
- Fetch bearer token via CopyLeaks Login API.
- Submit text blocks or files for comparison.
- Map the CopyLeaks scan results into the section similarity list.

---

### 5. Routing and Glue Code

#### [MODIFY] [__init__.py](file:///d:/Github/plagarism/backend/app/parser/__init__.py)
Update to check `settings.USE_MARKER` and route to `marker_parser` accordingly.

#### [MODIFY] [analyzer.py](file:///d:/Github/plagarism/backend/app/similarity/analyzer.py)
If `settings.USE_COPYLEAKS` is True and credentials exist, route scans to `copyleaks_service.py`.

#### [MODIFY] [rewrite_engine.py](file:///d:/Github/plagarism/backend/app/rewrite/rewrite_engine.py)
Update to use CrewAI multi-agent rewriting if `settings.USE_CREWAI` is active.

---

### 6. Deployment Documentation

#### [NEW] [deployment_guide.md](file:///d:/Github/plagarism/deployment_guide.md)
Document deployment procedures:
- **Frontend (Next.js)**: Free Vercel hosting.
- **Backend (FastAPI)**: Free Hugging Face Spaces (with Docker) or Koyeb free tier. Both offer 24/7 unlimited live running without cold sleeps.
- **LibreOffice headless**: Detail how to set up `libreoffice` in Docker containers (via apt-get) so PDF export works out-of-the-box.

## Verification Plan

### Automated Validation
- Run unit/mock tests to verify API routing.
- Check import robustness when packages are absent.

### Manual Verification
- Deploy locally, submit a PDF, and run rewrite checks to confirm fallback/integration logs are clean.
