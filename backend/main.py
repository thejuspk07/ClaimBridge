"""
ClaimBridge FastAPI Application Entry Point.
Provides enterprise REST API for medical claim document processing.
"""
import uuid
from typing import List, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.schemas.claim_schema import (
    BatchProcessResponse,
    ClaimDetailResponse,
    ClaimSummaryResponse,
    ReviewActionRequest,
)
from backend.services.claim_processor import claim_processor
from backend.services.storage_service import storage_service

app = FastAPI(
    title="ClaimBridge API",
    description="Professional End-to-End Medical Claim Processing Pipeline",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directories exist
Path("data/uploads").mkdir(parents=True, exist_ok=True)
Path("data/dataset/images").mkdir(parents=True, exist_ok=True)
Path("frontend").mkdir(parents=True, exist_ok=True)

# Mount static asset routes
app.mount("/data/uploads", StaticFiles(directory="data/uploads"), name="uploads")
app.mount("/data/dataset/images", StaticFiles(directory="data/dataset/images"), name="dataset_images")
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/api/health")
async def health_check():
    """Returns backend and OCR service health status."""
    return {
        "status": "healthy",
        "service": "ClaimBridge Backend",
        "engine": "PaddleOCR PP-OCRv6 (CPU)",
        "accuracy_target": "99.62%",
        "version": "1.0.0"
    }


@app.post("/api/claims/process", response_model=ClaimDetailResponse)
async def process_single_claim(file: UploadFile = File(...)):
    """
    Processes an uploaded CMS-1500 claim file (PDF or PNG).
    Runs PDF rendering, PaddleOCR, calibrated field extraction, and clinical validation.
    """
    try:
        result = await claim_processor.process_file(file)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/claims/process-batch", response_model=BatchProcessResponse)
async def process_batch_claims(files: List[UploadFile] = File(...)):
    """
    Processes multiple CMS-1500 claims sequentially.
    """
    job_id = f"batch_{uuid.uuid4().hex[:6]}"
    processed_summaries: List[ClaimSummaryResponse] = []
    failed_count = 0

    for file in files:
        try:
            claim_detail = await claim_processor.process_file(file)
            processed_summaries.append(ClaimSummaryResponse(
                claim_id=claim_detail.claim_id,
                filename=claim_detail.filename,
                uploaded_at=claim_detail.uploaded_at,
                patient_name=claim_detail.patient.name,
                insured_id=claim_detail.insurance.insured_id,
                total_charge=claim_detail.total_charge,
                status=claim_detail.status,
                confidence_score=claim_detail.confidence_score,
                error_count=claim_detail.validation.error_count,
                warning_count=claim_detail.validation.warning_count,
                image_url=claim_detail.image_url,
            ))
        except Exception as e:
            print(f"Batch processing error on {file.filename}: {e}")
            failed_count += 1

    return BatchProcessResponse(
        job_id=job_id,
        total_files=len(files),
        status="completed",
        processed_count=len(processed_summaries),
        failed_count=failed_count,
        claims=processed_summaries,
    )


@app.get("/api/claims", response_model=List[ClaimSummaryResponse])
async def list_claims(
    status: Optional[str] = Query(None, description="Filter by status (all, processed, needs_review, approved, rejected)"),
    search: Optional[str] = Query(None, description="Search query by name, ID, or filename"),
):
    """Lists all processed claims with optional filtering and search."""
    return storage_service.list_claims(status_filter=status, search=search)


@app.get("/api/claims/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim_detail(claim_id: str):
    """Retrieves full extracted claim details, field confidences, and validation results."""
    claim = storage_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")
    return claim


@app.post("/api/claims/{claim_id}/approve", response_model=ClaimDetailResponse)
async def approve_claim(claim_id: str):
    """Marks a claim as approved by human reviewer."""
    claim = storage_service.record_review(claim_id, action="approve", reviewer="Admin Reviewer")
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")
    return claim


@app.post("/api/claims/{claim_id}/review", response_model=ClaimDetailResponse)
async def submit_claim_review(claim_id: str, review_req: ReviewActionRequest):
    """Submits manual field corrections or updates human review status."""
    claim = storage_service.record_review(
        claim_id=claim_id,
        action=review_req.action,
        reviewer=review_req.reviewer or "Reviewer",
        notes=review_req.notes,
        corrections=review_req.corrections,
    )
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")
    return claim


@app.get("/api/claims/{claim_id}/export")
async def export_claim_json(claim_id: str):
    """Exports structured claim JSON."""
    claim = storage_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")
    return Response(
        content=claim.model_dump_json(indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={claim_id}_extracted.json"}
    )


@app.get("/api/claims/export/csv")
async def export_all_claims_csv():
    """Exports CSV summary of all processed claims."""
    csv_data = storage_service.export_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=claimbridge_summary.csv"}
    )


@app.post("/api/demo/load", response_model=List[ClaimSummaryResponse])
async def load_demo_dataset():
    """Preloads the verified 10-claim dataset into the active queue for instant demo."""
    return storage_service.load_demo_claims()


@app.get("/")
async def serve_dashboard():
    """Serves the main frontend dashboard."""
    index_path = Path("frontend/index.html")
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_path)
