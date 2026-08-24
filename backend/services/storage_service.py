"""
Storage and Claim Management Service.
Handles claim records, manual corrections, reviewer audit log, and demo dataset loading.
"""
import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.schemas.claim_schema import (
    AddressModel,
    ClaimDetailResponse,
    ClaimSummaryResponse,
    FieldReviewEntry,
    InsuranceModel,
    PatientModel,
    ProviderInfoModel,
    ServiceLineItem,
    ValidationSummary,
)


class StorageService:
    def __init__(self):
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir = Path("data/processed_api")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.claims: Dict[str, ClaimDetailResponse] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._load_existing_claims()

    def _load_existing_claims(self):
        """Loads any previously processed claims from disk."""
        for file in self.processed_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    claim = ClaimDetailResponse(**data)
                    self.claims[claim.claim_id] = claim
            except Exception as e:
                print(f"Error loading claim {file}: {e}")

    def save_claim(self, claim: ClaimDetailResponse):
        """Saves a claim in memory and persists to disk."""
        self.claims[claim.claim_id] = claim
        file_path = self.processed_dir / f"{claim.claim_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(claim.model_dump_json(indent=2))

    def get_claim(self, claim_id: str) -> Optional[ClaimDetailResponse]:
        return self.claims.get(claim_id)

    def find_by_hash(self, file_hash: str) -> Optional[ClaimDetailResponse]:
        """Finds a claim record matching the given SHA-256 content hash."""
        for claim in self.claims.values():
            if claim.file_hash and claim.file_hash == file_hash:
                return claim
        return None

    def list_claims(self, status_filter: Optional[str] = None, search: Optional[str] = None) -> List[ClaimSummaryResponse]:
        summaries = []
        for claim in self.claims.values():
            if status_filter and status_filter.lower() != "all":
                if claim.status.lower() != status_filter.lower() and claim.review_status != status_filter.lower():
                    continue

            if search:
                q = search.lower()
                p_name = claim.patient.name or ""
                fn = claim.filename or ""
                cid = claim.claim_id or ""
                ins_id = claim.insurance.insured_id or ""
                if q not in p_name.lower() and q not in fn.lower() and q not in cid.lower() and q not in ins_id.lower():
                    continue

            summaries.append(ClaimSummaryResponse(
                claim_id=claim.claim_id,
                filename=claim.filename,
                uploaded_at=claim.uploaded_at,
                patient_name=claim.patient.name,
                insured_id=claim.insurance.insured_id,
                total_charge=claim.total_charge,
                status=claim.review_status or claim.status,
                confidence_score=claim.confidence_score,
                error_count=claim.validation.error_count,
                warning_count=claim.validation.warning_count,
                image_url=claim.image_url,
            ))
        
        # Sort newest first
        summaries.sort(key=lambda s: s.uploaded_at, reverse=True)
        return summaries

    def record_review(self, claim_id: str, action: str, reviewer: str = "Reviewer", notes: Optional[str] = None, corrections: Optional[Dict[str, Any]] = None) -> Optional[ClaimDetailResponse]:
        claim = self.claims.get(claim_id)
        if not claim:
            return None

        timestamp = datetime.now().isoformat()

        if action == "approve":
            claim.review_status = "approved"
            claim.status = "approved"
        elif action == "reject":
            claim.review_status = "rejected"
            claim.status = "rejected"
        elif action == "review":
            claim.review_status = "needs_review"
            claim.status = "needs_review"

        if corrections:
            for field, new_val in corrections.items():
                orig_val = self._get_nested_field(claim, field)
                self._set_nested_field(claim, field, new_val)
                claim.manual_corrections.append(FieldReviewEntry(
                    field=field,
                    original_value=orig_val,
                    corrected_value=new_val,
                    reviewed_by=reviewer,
                    timestamp=timestamp
                ))

        self.save_claim(claim)
        return claim

    def export_csv(self) -> str:
        """Exports all claims as a CSV summary."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Claim ID", "Filename", "Uploaded At", "Patient Name", "Patient DOB",
            "Insured ID", "Insured Name", "Total Charge", "Status",
            "Confidence Score", "Errors", "Warnings"
        ])

        for claim in self.claims.values():
            writer.writerow([
                claim.claim_id,
                claim.filename,
                claim.uploaded_at,
                claim.patient.name or "",
                claim.patient.dob or "",
                claim.insurance.insured_id or "",
                claim.insurance.insured_name or "",
                f"{claim.total_charge:.2f}" if claim.total_charge is not None else "",
                claim.review_status or claim.status,
                f"{claim.confidence_score:.1f}%",
                claim.validation.error_count,
                claim.validation.warning_count,
            ])

        return output.getvalue()

    def load_demo_claims(self) -> List[ClaimSummaryResponse]:
        """Preloads demo claims from extracted_10 dataset if available."""
        ext_dir = Path("data/dataset/extracted_10")
        img_dir = Path("data/dataset/images")
        demo_summaries = []

        for i in range(1, 11):
            cid = f"claim_{i:03d}"
            ext_file = ext_dir / f"{cid}_extracted.json"
            if ext_file.exists() and cid not in self.claims:
                try:
                    with open(ext_file, "r", encoding="utf-8") as f:
                        extracted = json.load(f)

                    # Import validation dynamically
                    from backend.services.validation_service import validate_claim
                    val_summary = validate_claim(extracted)

                    field_confs = extracted.get("field_confidences", {})
                    avg_conf = (
                        (sum(field_confs.values()) / len(field_confs) * 100)
                        if field_confs else 98.5
                    )

                    patient_addr = extracted.get("patient_address", {})
                    insured_addr = extracted.get("insured_address", {})

                    service_items = [
                        ServiceLineItem(
                            line_number=line.get("line_number", idx + 1),
                            date_of_service=line.get("date_of_service"),
                            place_of_service=line.get("place_of_service"),
                            procedure_code=line.get("procedure_code"),
                            diagnosis_pointer=line.get("diagnosis_pointer"),
                            charges=line.get("charges"),
                            units=line.get("units"),
                            provider_npi=line.get("provider_npi"),
                        )
                        for idx, line in enumerate(extracted.get("service_lines", []))
                    ]

                    claim = ClaimDetailResponse(
                        claim_id=cid,
                        filename=f"{cid}.pdf",
                        file_type="application/pdf",
                        uploaded_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        image_url=f"/data/dataset/images/{cid}.png",
                        status="needs_review" if val_summary.warning_count > 0 else "processed",
                        confidence_score=round(avg_conf, 1),
                        patient=PatientModel(
                            name=extracted.get("patient_name"),
                            dob=extracted.get("patient_dob"),
                            address=AddressModel(
                                street=patient_addr.get("street"),
                                city=patient_addr.get("city"),
                                state=patient_addr.get("state"),
                                zip=patient_addr.get("zip"),
                                phone=patient_addr.get("phone"),
                            ),
                        ),
                        insurance=InsuranceModel(
                            insured_id=extracted.get("insured_id_number"),
                            insured_name=extracted.get("insured_name"),
                            policy_group=extracted.get("insurance_policy_group_number"),
                            plan_name=extracted.get("insurance_plan_name"),
                            address=AddressModel(
                                street=insured_addr.get("street"),
                                city=insured_addr.get("city"),
                                state=insured_addr.get("state"),
                                zip=insured_addr.get("zip"),
                                phone=insured_addr.get("phone"),
                            ),
                        ),
                        diagnosis_codes=extracted.get("diagnosis_codes", []),
                        service_lines=service_items,
                        federal_tax_id=extracted.get("federal_tax_id"),
                        patient_account_number=extracted.get("patient_account_number"),
                        total_charge=extracted.get("total_charge"),
                        amount_paid=extracted.get("amount_paid", 0.0),
                        signature_present=extracted.get("signature_present", False),
                        additional_claim_info=extracted.get("additional_claim_info"),
                        providers=ProviderInfoModel(
                            facility=extracted.get("service_facility"),
                            facility_npi=extracted.get("service_facility_npi"),
                            billing_provider=extracted.get("billing_provider"),
                            billing_npi=extracted.get("billing_provider_npi"),
                            referring_provider=extracted.get("referring_provider"),
                        ),
                        field_confidences=field_confs,
                        validation=val_summary,
                    )
                    self.save_claim(claim)
                except Exception as e:
                    print(f"Error loading demo claim {cid}: {e}")

        return self.list_claims()

    def _get_nested_field(self, claim: ClaimDetailResponse, path: str) -> Any:
        obj = claim
        for part in path.split("."):
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return None
        return obj

    def _set_nested_field(self, claim: ClaimDetailResponse, path: str, value: Any):
        parts = path.split(".")
        target = claim
        for part in parts[:-1]:
            if hasattr(target, part):
                target = getattr(target, part)
            elif isinstance(target, dict) and part in target:
                target = target[part]
            else:
                return
        final_key = parts[-1]
        if hasattr(target, final_key):
            setattr(target, final_key, value)
        elif isinstance(target, dict):
            target[final_key] = value


storage_service = StorageService()
