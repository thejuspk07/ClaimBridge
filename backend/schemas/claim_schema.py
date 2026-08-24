"""
Data models and schemas for ClaimBridge API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AddressModel(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None


class PatientModel(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    sex: Optional[str] = None
    address: Optional[AddressModel] = None


class InsuranceModel(BaseModel):
    insured_id: Optional[str] = None
    insured_name: Optional[str] = None
    policy_group: Optional[str] = None
    plan_name: Optional[str] = None
    address: Optional[AddressModel] = None


class ServiceLineItem(BaseModel):
    line_number: int
    date_of_service: Optional[str] = None
    place_of_service: Optional[str] = None
    procedure_code: Optional[str] = None
    diagnosis_pointer: Optional[str] = None
    charges: Optional[float] = None
    units: Optional[int] = None
    provider_npi: Optional[str] = None


class ProviderInfoModel(BaseModel):
    facility: Optional[str] = None
    facility_npi: Optional[str] = None
    billing_provider: Optional[str] = None
    billing_npi: Optional[str] = None
    referring_provider: Optional[str] = None


class ValidationMessage(BaseModel):
    field: str
    level: str  # "error", "warning", "info"
    code: str
    message: str


class ValidationSummary(BaseModel):
    valid: bool
    status: str  # "auto_approved", "needs_review", "flagged"
    error_count: int
    warning_count: int
    messages: List[ValidationMessage] = []


class FieldReviewEntry(BaseModel):
    field: str
    original_value: Any = None
    corrected_value: Any = None
    reviewed_by: Optional[str] = None
    timestamp: Optional[str] = None


class ClaimDetailResponse(BaseModel):
    claim_id: str
    filename: str
    file_type: str
    uploaded_at: str
    image_url: str
    status: str  # "processing", "processed", "needs_review", "approved", "rejected", "failed"
    confidence_score: float  # 0 - 100
    processing_time_ms: Optional[int] = None
    
    # Core claim data
    patient: PatientModel
    insurance: InsuranceModel
    diagnosis_codes: List[str] = []
    service_lines: List[ServiceLineItem] = []
    
    # Billing & Clinical
    federal_tax_id: Optional[str] = None
    patient_account_number: Optional[str] = None
    total_charge: Optional[float] = None
    amount_paid: Optional[float] = 0.0
    signature_present: bool = False
    additional_claim_info: Optional[str] = None
    providers: ProviderInfoModel
    
    # Validation & Field-level metrics
    field_confidences: Dict[str, float] = {}
    validation: ValidationSummary
    manual_corrections: List[FieldReviewEntry] = []
    review_status: Optional[str] = None  # "pending", "approved", "rejected"
    file_hash: Optional[str] = None  # SHA-256 content hash for dedup


class ClaimSummaryResponse(BaseModel):
    claim_id: str
    filename: str
    uploaded_at: str
    patient_name: Optional[str] = None
    insured_id: Optional[str] = None
    total_charge: Optional[float] = None
    status: str
    confidence_score: float
    error_count: int
    warning_count: int
    image_url: str


class ReviewActionRequest(BaseModel):
    action: str  # "approve", "reject", "correct"
    reviewer: Optional[str] = "Reviewer"
    notes: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None


class BatchProcessResponse(BaseModel):
    job_id: str
    total_files: int
    status: str
    processed_count: int = 0
    failed_count: int = 0
    claims: List[ClaimSummaryResponse] = []
