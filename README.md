---
title: PatentVision AI Backend
emoji: 📐
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
short_description: FastAPI AI backend for patent technical drawings
---

# PatentVision AI (v2.1)

Turns photographs of physical products into clean black-and-white, patent-office ready technical drawings and automatically compiles an official 7-page patent representation PDF document.
Implements the complete workflow specified in the PatentVision AI PRD v2.1.

```
backend/    FastAPI + SQLAlchemy + Alembic + OpenCV + ReportLab (Python) → served at /api
frontend/   Next.js 15 + React 19 + TypeScript + Tailwind CSS dashboard → served at /
vercel.json Vercel Services: full-stack deployment on a unified domain
```

> Representations and drawings are technical drafts that assist patent preparation. They do not substitute for formal patent-office legal advice and should be reviewed by an authorized patent professional.

---

## What's New in v2.1

1. **7 Fixed Upload Slots**: Strict patent-office view representations:
   - 1. **Perspective View** (3D perspective / exploded view)
   - 2. **Front View** (Direct front elevation)
   - 3. **Rear View** (Direct rear elevation)
   - 4. **Right Side View** (Direct right profile)
   - 5. **Left Side View** (Direct left profile)
   - 6. **Top View** (Direct top / plan elevation)
   - 7. **Bottom View** (Direct bottom / underside elevation)
2. **Single-Session Multi-Photo Upload**: Drop all 7 photos at once with smart filename heuristic mapping (e.g. `front`, `rear`, `right`, `left`, `top`, `bottom`, `perspective`), plus drag-and-drop replacement on individual slots.
3. **Enhanced AI Image Pipeline — Two-Stage Processing**:
   - **Stage 1 — Automatic Background Removal**: Every uploaded photo is first processed by a U-2-Net deep-learning segmentation model (via `rembg`) to isolate the product from any background (white, coloured, office/room, floor). The segmented foreground mask is validated for quality, border cropping, and multi-component contamination.
   - **Stage 2 — Mask-Isolated Edge Extraction**: Canny and Laplacian edge detection run only within the validated product mask, ensuring background edges, shadows, and unrelated objects are never drawn.
   - Advanced background isolation excluding lateral border-touching artifacts (e.g. office chairs, desks) while preserving vertical multi-component assemblies.
   - Surface branding, logo, and printed text detection and suppression (`branding.py`).
   - Structural seam, hole, latch, joint, and knob preservation.
   - `background_remover_method` metric returned with every AI result (`rembg` | `classical` | `grabcut`).
4. **Drawing Quality Validation**:
   - Multi-component and boundary contamination metrics.
   - Contaminated or ambiguous drawings are flagged as `Review required` and never falsely marked as `Completed`.
5. **Drawing Review & Approval Workflow**:
   - Interactive drawing inspection, approval (`Approved`), rejection (`Rejected`), and per-slot reprocessing.
6. **Official 7-Page Patent Representation PDF**:
   - Exact layout and page order matching the official patent standard (`Jug 2-in-1.pdf` reference).
   - Each page features applicant information, page numbering (`Page No.: X of 7`), centered technical illustration, bold view title, statement of novelty, disclaimer, filing date, and patent agent signature placeholder or uploaded signature image.
7. **Strict Document Generation Lock**:
   - PDF generation is strictly locked until all 7 required views are uploaded, processed, and approved.

---

## Quick Start

### Backend (http://localhost:8000, docs at `/docs`)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt   # includes reportlab, pytest, ruff, opencv
copy .env.example .env          # set PV_SECRET_KEY to a secure random string
alembic upgrade head            # apply migrations including 0003_perspective_and_document_metadata
uvicorn app.main:app --reload
```

> **Background removal model**: On first run the backend downloads `u2net.onnx` (~170 MB) from GitHub to `~/.rembg/models/u2net/`. This requires a one-time internet connection. Subsequent runs are offline. If running in an air-gapped environment, manually copy the model file to that path.

### Frontend (http://localhost:3000)

```bash
cd frontend
npm install
npm run dev                     # proxies /api/* to http://127.0.0.1:8000
```

---

## Free Cloud Demo Deployment (GitHub Actions + Hugging Face)

The recommended demo deployment uses two Hugging Face Spaces:
- **Backend:** Docker Space running FastAPI, OpenCV and rembg.
- **Frontend:** Gradio Space calling the backend API.
- **Database and files:** local SQLite and local filesystem inside the backend container.

> **Important:** Hugging Face free Spaces have ephemeral local storage. Accounts, projects, uploaded images, generated drawings, signatures and PDFs can be lost when the Space restarts or rebuilds. This is a demonstration deployment, not suitable for production records.

### One-time setup
1. Create a Hugging Face **write** access token at [Hugging Face Settings → Access Tokens](https://huggingface.co/settings/tokens).
2. In GitHub, open **Settings → Secrets and variables → Actions → Secrets** and add/update `HF_TOKEN` with that token.
3. Push to `main`, or manually run **Actions → Deploy PatentVision AI to Hugging Face Spaces → Run workflow**.
4. The workflow creates/updates `<your-hf-username>/patentvision-backend` and `<your-hf-username>/patentvision-frontend`, configures their connection, and uploads the application.

### Demo URLs
- Backend: `https://<username>-patentvision-backend.hf.space`
- API docs: `https://<username>-patentvision-backend.hf.space/docs`
- Gradio frontend: `https://<username>-patentvision-frontend.hf.space`

The workflow uses the Hugging Face Hub API to create Spaces and upload files. See [Hugging Face Hub API](https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api).

## Running Automated Tests

### Backend Tests (pytest)
Runs unit, API, migration, visual regression, quality validation, and end-to-end 7-view pipeline tests:
```bash
cd backend
pytest -v
```
*(All 131 tests passing)*

### Frontend Tests (vitest & typecheck)
```bash
cd frontend
npm test -- --run               # 46 vitest tests passing
npm run typecheck               # tsc --noEmit (0 errors)
npm run build                   # Next.js 15 production build
```

---

## Database Migrations

The database schema is managed via Alembic. Version `0003` adds support for:
- `Perspective` view type in `images` and `REQUIRED_VIEW_TYPES`.
- `approval_status` and `is_active` on `images`.
- `quality_status` and `quality_warnings` on `ai_results`.
- `document_metadata` table for applicant, novelty statement, disclaimers, agent info, and signatures.
- `project_documents` table for tracking generated 7-page PDF releases.

To apply migrations:
```bash
alembic upgrade head
```
To roll back:
```bash
alembic downgrade -1
```

---

## API Reference

All protected routes require `Authorization: Bearer <token>`.

### 7-View Slot Management
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects/{id}/views` | Returns the 7-slot status, readiness, missing, and unapproved views |
| `POST` | `/projects/{id}/views/{view_type}` | Upload or replace a photo in a specific view slot |
| `DELETE` | `/projects/{id}/views/{view_type}` | Remove the photo and drawings from a view slot |

### Drawing Review & Quality Control
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/images/{id}/review` | Submit drawing review action (`approve` or `reject`) with optional notes |
| `POST` | `/ai/process/{id}` | Process an image; generates mask, outline, drawing, and SVG |
| `POST` | `/ai/process/project/{id}` | Batch process all pending views in a project |

### Patent Document & PDF Generation
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects/{id}/document-metadata` | Get project document metadata and signature status |
| `PUT` | `/projects/{id}/document-metadata` | Update applicant name, title, date, novelty statement, disclaimer, and agent info |
| `POST` | `/projects/{id}/document-metadata/signature` | Upload agent/applicant signature image (PNG/JPG) |
| `DELETE` | `/projects/{id}/document-metadata/signature` | Remove uploaded signature image |
| `POST` | `/projects/{id}/documents` | Generate official 7-page patent PDF (requires all 7 views approved) |
| `GET` | `/projects/{id}/documents` | List generated patent PDF documents |
| `GET` | `/documents/{id}/download` | Download generated patent PDF |
| `GET` | `/documents/{id}/preview` | Preview patent PDF inline in browser |

### Projects & Images
| Method | Endpoint | Description |
|---|---|---|
| `POST`, `GET` | `/projects` | Create and list projects |
| `GET`, `PUT`, `DELETE` | `/projects/{id}` | Read, update, delete project (cascades records and files) |
| `GET` | `/images/{id}` | Read image status, approval, and result URLs |
| `GET` | `/ai/results/{id}/download?kind=...` | Download original, mask, outline, drawing PNG, or SVG |

---

## Known Scope & Operating Notes

1. **Drawing Quality & Review**: The pipeline flags surface branding and multi-component silhouettes as `Review required`. Patent professionals should review the drawing on the inspector page (`/images/[id]`) and approve or reprocess before generating the PDF.
2. **rembg Cold-Start Latency**: The first image processed after server startup loads the U-2-Net ONNX model into memory (~25 s one-time warm-up). Subsequent images are fast (~2–4 s each).
3. **Serverless Limits**: Uploads are capped at 40 MB client-side and optimized in the browser before transfer to satisfy serverless payload limits.
4. **Legal Disclaimer**: Generated documents include placeholders and drafting notices to emphasize that representation sheets require authorized patent attorney / agent verification before formal submission to intellectual property offices.
