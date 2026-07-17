# Walkthrough - UI Redesign & Codebase Diagnostic Verification

We completed the premium UI redesign of the **AuthentiCite** Next.js application, resolved multiple connection and integration bugs, and optimized dependency listings.

---

## 1. UI Redesign & Clutter Removal Completed

We redesigned the frontend with a premium, minimalist, and cohesive look (Deep Slate & Indigo glassmorphism):
1. **Globals & Animations**: Configured `.glass-panel`, `.glass-card` and `.bg-grid-mesh` styles inside `globals.css` with elegant custom scrollbars and micro-animations.
2. **Unified Branding**: Renamed all brand references from *ResearchAI* to **AuthentiCite** across all route headers and landing pages.
3. **Hero & Upload Redesign**: Simplified `page.tsx` and `DocumentUpload.tsx`. Removed the redundant feature matrices and badges to focus user attention entirely on the upload zone.
4. **Dashboard Polishing**: Restructured `dashboard/page.tsx` to make the document info header compact, styling block list rows with thin borders and elegant tags.
5. **Interactive Editor**: Polished `rewrite/page.tsx` and `CompareView.tsx` to improve comparative textareas and alerts.
6. **Layout Compiler Grid**: Streamlined `download/page.tsx` filters and card designs.

*The Next.js frontend built and compiled successfully (`next build`) without any errors.*

---

## 2. Technical Bug Fixes & Code Connections

### [FIX] CopyLeaks Scan Payload Bug
- **File**: `backend/app/similarity/copyleaks_service.py`
- **Problem**: The request payload sent `"text56": text` instead of the standard `"text"` parameter. Additionally, the text was sent as raw string instead of the base64-encoded string required by CopyLeaks. This would cause CopyLeaks API to always reject the requests.
- **Fix**: Encoded the text using `base64` and updated the payload mapping:
  ```python
  encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
  payload = { "text": encoded_text, ... }
  ```

### [FIX] DOCX Parser 'to_hex' Crash
- **File**: `backend/app/parser/docx_parser.py`
- **Problem**: Attempted to call `.to_hex()` on python-docx `RGBColor` objects, which failed because the class does not have that method.
- **Fix**: Formatted the RGB tuple into a standard hex string:
  ```python
  "color": f"#{r.font.color.rgb[0]:02x}{r.font.color.rgb[1]:02x}{r.font.color.rgb[2]:02x}"
  ```

### [FIX] Hardcoded Localhost API Request
- **File**: `frontend/src/components/CompareView.tsx`
- **Problem**: "Save Edits" calls were hardcoded to `http://127.0.0.1:8000`, bypassing `process.env.NEXT_PUBLIC_API_URL` configuration.
- **Fix**: Routed saves through the imported `rewriteSection` helper which respects your environment settings.

### [FIX] Missing scanned-PDF OCR dependency
- **Files**: `requirements.txt` & `backend/requirements.txt`
- **Problem**: Scanned PDF files fall back to image-rendering and OCR text extraction, requiring the `fitz` library (PyMuPDF), but `pymupdf` was not declared in any dependencies file.
- **Fix**: Added `pymupdf==1.24.2` to both requirements lists.

---

## 3. Performance Assessment & Recommendations

1. **Similarity Matrix Scan**: The similarity checking runs pairwise cosine comparisons over all database paragraphs in pure Python (`O(N * M)` complexity). 
   - *Recommendation*: While very fast for low-to-medium datasets, it should be migrated to a vector indexing database (like Qdrant or pgvector) if you scale to thousands of uploaded documents.
2. **Cold Starts on Render Free Tier**: Render Web Services sleep after 15 minutes of inactivity. When a user visits your app after a break, the backend container might take up to **50 seconds** to start up, causing frontend timeouts.
   - *Recommendation*: Set up an automated ping cron job (e.g. UptimeRobot) to keep the backend warm, or upgrade to Render's starter Web Service ($7/mo).
3. **Database Lifespan**: Because SQLite is used, database files in the container are wiped on redeploys/restarts.
   - *Recommendation*: Mount a Render **Persistent Disk** (at `/data`) and direct `DATABASE_URL` to it.
