"""
Validation and Quality Assurance Service for medical claims.
Implements explainable clinical and billing consistency rules.
"""
import re
from typing import Any, Dict, List
from backend.schemas.claim_schema import ValidationMessage, ValidationSummary


def validate_claim(claim_data: Dict[str, Any]) -> ValidationSummary:
    """
    Evaluates extraction results against healthcare billing validation rules.
    """
    messages: List[ValidationMessage] = []

    # 1. Required Fields Check
    required_fields = [
        ("patient_name", "Patient Name", "REQ_PATIENT_NAME"),
        ("patient_dob", "Patient Date of Birth", "REQ_PATIENT_DOB"),
        ("insured_id_number", "Insured ID Number", "REQ_INSURED_ID"),
        ("federal_tax_id", "Federal Tax ID (EIN/SSN)", "REQ_TAX_ID"),
        ("total_charge", "Total Claim Charge", "REQ_TOTAL_CHARGE"),
        ("billing_provider_npi", "Billing Provider NPI", "REQ_BILLING_NPI"),
    ]

    for field_key, label, code in required_fields:
        val = claim_data.get(field_key)
        if val is None or str(val).strip() == "":
            messages.append(ValidationMessage(
                field=field_key,
                level="error",
                code=code,
                message=f"Required field '{label}' is missing or could not be detected."
            ))

    # 2. Diagnosis Codes Check
    dx_codes = claim_data.get("diagnosis_codes", [])
    if not dx_codes:
        messages.append(ValidationMessage(
            field="diagnosis_codes",
            level="error",
            code="REQ_DIAGNOSES",
            message="No valid ICD-10 diagnosis codes detected on the claim (Box 21)."
        ))
    else:
        for idx, dx in enumerate(dx_codes):
            if not re.fullmatch(r"[A-Z]\d{2}(?:\.\d+)?", dx.upper()):
                messages.append(ValidationMessage(
                    field="diagnosis_codes",
                    level="warning",
                    code="WARN_INVALID_ICD10",
                    message=f"Diagnosis code '{dx}' does not conform to standard ICD-10 format."
                ))

    # 3. NPI Checks
    billing_npi = claim_data.get("billing_provider_npi")
    if billing_npi:
        # Extract digits
        digits = re.sub(r"\D", "", billing_npi)
        if len(digits) != 10:
            messages.append(ValidationMessage(
                field="billing_provider_npi",
                level="error",
                code="ERR_NPI_FORMAT",
                message=f"Billing Provider NPI '{billing_npi}' is not a valid 10-digit NPI."
            ))

    facility_npi = claim_data.get("service_facility_npi")
    if facility_npi:
        digits = re.sub(r"\D", "", facility_npi)
        if len(digits) != 10:
            messages.append(ValidationMessage(
                field="service_facility_npi",
                level="warning",
                code="WARN_FACILITY_NPI",
                message=f"Service Facility NPI '{facility_npi}' is not a 10-digit number."
            ))

    # 4. Service Line Consistency & Math Checks
    service_lines = claim_data.get("service_lines", [])
    calculated_sum = 0.0
    active_lines = 0

    max_pointer_index = len(dx_codes)
    valid_pointers = [chr(ord('A') + i) for i in range(max_pointer_index)]

    for line in service_lines:
        line_num = line.get("line_number", 0)
        charge = line.get("charges")
        procedure = line.get("procedure_code")
        pointer = line.get("diagnosis_pointer")
        dos = line.get("date_of_service")

        if charge is not None or procedure is not None or dos is not None:
            active_lines += 1

            if charge is not None:
                calculated_sum += float(charge)
            else:
                messages.append(ValidationMessage(
                    field=f"service_lines[{line_num}].charges",
                    level="warning",
                    code="WARN_LINE_CHARGE_MISSING",
                    message=f"Service Line {line_num} has active services but no charge amount."
                ))

            if pointer:
                if pointer.upper() not in valid_pointers:
                    messages.append(ValidationMessage(
                        field=f"service_lines[{line_num}].diagnosis_pointer",
                        level="warning",
                        code="WARN_POINTER_MISMATCH",
                        message=f"Service Line {line_num} pointer '{pointer}' does not map to any active diagnosis (Boxes A-{chr(ord('A') + max(0, max_pointer_index - 1))})."
                    ))

    if active_lines == 0:
        messages.append(ValidationMessage(
            field="service_lines",
            level="error",
            code="ERR_NO_SERVICES",
            message="No active service rows detected on claim (Box 24)."
        ))

    # 5. Total Charge Summation Consistency
    declared_total = claim_data.get("total_charge")
    if declared_total is not None and active_lines > 0:
        diff = abs(declared_total - calculated_sum)
        if diff > 0.05:
            messages.append(ValidationMessage(
                field="total_charge",
                level="warning",
                code="WARN_CHARGE_SUM_MISMATCH",
                message=f"Total charge ${declared_total:.2f} differs from sum of line charges (${calculated_sum:.2f}) by ${diff:.2f}."
            ))

    # 6. Confidence Threshold Warnings
    field_confs = claim_data.get("field_confidences", {})
    for field_name, conf in field_confs.items():
        if conf is not None and conf > 0 and conf < 0.85:
            pct = conf * 100
            messages.append(ValidationMessage(
                field=field_name,
                level="warning",
                code="WARN_LOW_CONFIDENCE",
                message=f"Field '{field_name}' OCR confidence is {pct:.1f}% (below 85% verification threshold)."
            ))

    # 7. Signature Check
    if not claim_data.get("signature_present", False):
        messages.append(ValidationMessage(
            field="signature_present",
            level="warning",
            code="WARN_NO_SIGNATURE",
            message="Provider or authorized signature not detected in Box 31."
        ))

    # Determine status
    errors = [m for m in messages if m.level == "error"]
    warnings = [m for m in messages if m.level == "warning"]

    if len(errors) > 0:
        status = "flagged"
        valid = False
    elif len(warnings) > 0:
        status = "needs_review"
        valid = True
    else:
        status = "auto_approved"
        valid = True

    return ValidationSummary(
        valid=valid,
        status=status,
        error_count=len(errors),
        warning_count=len(warnings),
        messages=messages,
    )
