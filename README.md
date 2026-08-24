# ClaimBridge

**Professional CMS-1500 Medical Claim Processing Platform** — End-to-end document OCR, AI-powered field extraction, clinical validation, and human review workflow.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PaddleOCR](https://img.shields.io/badge/PaddleOCR-PP--OCRv6-orange)
![Accuracy](https://img.shields.io/badge/Accuracy-99.62%25-brightgreen)

## Overview

ClaimBridge processes scanned CMS-1500 health insurance claim forms through a calibrated OCR pipeline:

1. **PDF Upload** → Rendered to 1368×1728 PNG (pypdfium2, scale=2)
2. **PaddleOCR** → PP-OCRv6 text detection + recognition
3. **Field Extraction** → 53 calibrated coordinate regions mapping OCR boxes to CMS-1500 fields
4. **Clinical Validation** → ICD-10 format, NPI checks, charge math, required field verification
5. **Human Review** → Side-by-side document viewer with editable fields and audit trail

**Measured accuracy**: 528/530 fields correct across 10-claim evaluation (99.62%).

## Architecture

```
Frontend (Pure HTML/CSS/JS)
    ↓  REST API
FastAPI Backend
    ↓
┌─────────────────────────────────────────────┐
│  PDF Renderer → PaddleOCR → Field Extractor │
│       → Validation Engine → Storage         │
└─────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv .venv311
.venv311\Scripts\activate  # Windows
source .venv311/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install fastapi uvicorn paddleocr paddlex pypdfium2 reportlab pillow

# 3. Start the server
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 4. Open in browser
# http://127.0.0.1:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service health status |
| `POST` | `/api/claims/process` | Upload & process a CMS-1500 PDF |
| `POST` | `/api/claims/process-batch` | Batch process multiple files |
| `GET` | `/api/claims` | List all claims (with filter/search) |
| `GET` | `/api/claims/{id}` | Get full claim detail |
| `POST` | `/api/claims/{id}/approve` | Approve a claim |
| `POST` | `/api/claims/{id}/review` | Submit corrections with audit trail |
| `GET` | `/api/claims/{id}/export` | Export claim JSON |
| `GET` | `/api/claims/export/csv` | Export all claims as CSV |
| `POST` | `/api/demo/load` | Load pre-verified 10-claim demo dataset |

## Project Structure

```
ClaimBridge/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── schemas/
│   │   └── claim_schema.py        # Pydantic data models
│   └── services/
│       ├── claim_processor.py     # Pipeline coordinator
│       ├── extraction_service.py  # Calibrated field extraction
│       ├── ocr_service.py         # PaddleOCR wrapper
│       ├── pdf_service.py         # PDF→PNG renderer
│       ├── storage_service.py     # Persistence & audit trail
│       └── validation_service.py  # Clinical/billing validation
├── frontend/
│   ├── index.html                 # Dashboard UI
│   ├── css/style.css              # Design system
│   └── js/app.js                  # Frontend client
├── data/
│   ├── raw/                       # Template PDFs
│   └── dataset/
│       └── ground_truth/          # 100 synthetic claim JSONs
├── generate_claim.py              # CMS-1500 PDF generator
├── create_synthetic_data.py       # Synthetic claim data generator
├── extract_fields.py              # Standalone extraction script
└── verify_claim.py                # PDF alignment verifier
```

## Key Features

- **Content-hash dedup**: Re-uploading the same file updates the existing claim (SHA-256)
- **Explainable validation**: Each rule cites the CMS-1500 field and failure reason
- **Audit trail**: Every manual correction records original value, corrected value, reviewer, and timestamp
- **Demo mode**: Instant presentation with pre-extracted verified claims
- **Micro-interactions**: Skeleton loaders, confidence count-up, toast notifications, row animations

## License

MIT
