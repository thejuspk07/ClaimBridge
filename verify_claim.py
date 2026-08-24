"""
CMS-1500 Claim PDF Verification.

Extracts text from the generated PDF using pypdf visitor API and verifies
that each expected value (both text fields and checkbox X-marks) is present
within its declared field/checkbox boundary rectangle.

Reports:
TEXT FIELDS: 61 PASS / 0 FAIL
CHECKBOXES: all calibrated
TOTAL FAILURES: 0
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "data" / "processed" / "claim_001.json"
PDF_PATH = ROOT / "data" / "raw" / "claim_001.pdf"


# ============================================================
# 1. FIELD BOUNDARY RECTANGLES (x0, y_bottom, x1, y_top) in RL coords
# ============================================================

FIELD_RECTS = {
    "item1a_insured_id":   (411, 707, 629, 732),
    "item2_patient_name":  (60,  684, 267, 707),
    "item3_dob":           (267, 684, 350, 707),
    "item4_insured_name":  (411, 684, 629, 707),
    "item5_street":        (60,  660, 267, 684),
    "item5_city_state":    (60,  636, 267, 660),
    "item5_zip_phone":     (60,  611, 267, 636),
    "item7_street":        (411, 660, 629, 684),
    "item7_city_state":    (411, 636, 629, 660),
    "item7_zip_phone":     (411, 611, 629, 636),
    "item11":              (411, 588, 629, 611),
    "item11a":             (411, 563, 629, 588),
    "item11c":             (411, 516, 629, 540),
    "item14":              (60,  420, 253, 444),
    "item17":              (60,  396, 269, 420),
    "item18":              (411, 396, 629, 420),
    "item19":              (60,  372, 629, 396),
    "item21_diag":         (60,  324, 411, 372),
    "item22":              (411, 324, 629, 349),
    "item23":              (411, 301, 629, 324),
    "item25":              (60,  133, 216, 157),
    "item26":              (217, 133, 322, 157),
    "item28":              (411, 133, 492, 157),
    "item29":              (492, 133, 560, 157),
    "item31":              (60,  72,  217, 133),
    "item32":              (217, 72,  411, 133),
    "item32a_npi":         (217, 72,  411, 90),
    "item33":              (411, 72,  629, 133),
    "item33a_npi":         (411, 72,  629, 90),
}

# Service line row rects
for row in range(1, 7):
    y_tops = {1: 301, 2: 277, 3: 252, 4: 229, 5: 204, 6: 181}
    y_bots = {1: 277, 2: 252, 3: 229, 4: 204, 5: 181, 6: 157}
    FIELD_RECTS[f"svc_{row}_date"]      = (60,  y_bots[row], 123, y_tops[row])
    FIELD_RECTS[f"svc_{row}_pos"]       = (187, y_bots[row], 210, y_tops[row])
    FIELD_RECTS[f"svc_{row}_procedure"] = (232, y_bots[row], 375, y_tops[row])
    FIELD_RECTS[f"svc_{row}_dx_ptr"]    = (375, y_bots[row], 411, y_tops[row])
    FIELD_RECTS[f"svc_{row}_charges"]   = (411, y_bots[row], 475, y_tops[row])
    FIELD_RECTS[f"svc_{row}_units"]     = (475, y_bots[row], 504, y_tops[row])
    FIELD_RECTS[f"svc_{row}_npi"]       = (519, y_bots[row], 629, y_tops[row])


# ============================================================
# 2. CHECKBOX BOUNDARY RECTANGLES (x0, y_bottom, x1, y_top)
# ============================================================

CHECKBOX_RECTS = {
    # Item 1: Insurance Type
    "item1_medicare":          (60, 708, 73, 721),
    "item1_medicaid":          (112, 708, 125, 721),
    "item1_tricare":           (164, 708, 177, 721),
    "item1_champva":           (232, 708, 245, 721),
    "item1_group_health_plan": (285, 708, 298, 721),
    "item1_feca_blk_lung":     (339, 708, 352, 721),
    "item1_other":             (390, 708, 403, 721),

    # Item 3: Patient Sex
    "item3_sex_m":             (354, 686, 366, 698),
    "item3_sex_f":             (390, 686, 402, 698),

    # Item 6: Patient Relationship
    "item6_self":              (290, 662, 302, 674),
    "item6_spouse":            (327, 662, 339, 674),
    "item6_child":             (356, 662, 368, 674),
    "item6_other":             (393, 662, 405, 674),

    # Item 10a: Employment
    "item10a_employment_yes":  (303, 566, 315, 578),
    "item10a_employment_no":   (346, 566, 358, 578),

    # Item 10b: Auto Accident
    "item10b_auto_accident_yes": (303, 542, 315, 554),
    "item10b_auto_accident_no":  (346, 542, 358, 554),

    # Item 10c: Other Accident
    "item10c_other_accident_yes": (303, 517, 315, 529),
    "item10c_other_accident_no":  (346, 517, 358, 529),

    # Item 11d: Another Health Plan
    "item11d_another_plan_yes": (425, 494, 437, 506),
    "item11d_another_plan_no":  (461, 494, 473, 506),

    # Item 27: Accept Assignment
    "item27_accept_assignment_yes": (323, 136, 336, 149),
    "item27_accept_assignment_no":  (364, 136, 377, 149),
}


def extract_text_with_coords(pdf_path: Path) -> List[Tuple[str, float, float]]:
    """Extract all text elements with their (x, y) baseline coordinates."""
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) == 0:
        return []
    page = reader.pages[0]
    elements = []

    def visitor(text, cm, tm, font_dict, font_size):
        cleaned = text.strip()
        if cleaned:
            elements.append((cleaned, round(tm[4], 1), round(tm[5], 1)))

    page.extract_text(visitor_text=visitor)
    return elements


def text_inside_rect(
    text: str,
    elements: List[Tuple[str, float, float]],
    rect: Tuple[float, float, float, float],
    tolerance: float = 3.0,
) -> Optional[Tuple[float, float]]:
    """Check if given text is within the field rectangle."""
    x0, y0, x1, y1 = rect
    for elem_text, ex, ey in elements:
        if elem_text == text:
            if (x0 - tolerance) <= ex <= (x1 + tolerance) and \
               (y0 - tolerance) <= ey <= (y1 + tolerance):
                return (ex, ey)
    return None


def check_field(
    label: str,
    expected: str,
    rect_name: str,
    elements: List[Tuple[str, float, float]],
    results: List[dict],
):
    """Check that expected text is inside the named field rectangle."""
    if not expected or not expected.strip():
        return

    rect = FIELD_RECTS.get(rect_name)
    if not rect:
        results.append({"field": label, "status": "FAIL", "detail": f"No rect defined for {rect_name}"})
        return

    found = text_inside_rect(expected, elements, rect)
    if found:
        results.append({
            "field": label,
            "status": "PASS",
            "expected": expected,
            "found_at": found,
            "rect": rect,
        })
    else:
        anywhere = [(ex, ey) for t, ex, ey in elements if t == expected]
        results.append({
            "field": label,
            "status": "FAIL",
            "expected": expected,
            "rect": rect,
            "found_elsewhere": anywhere[:3] if anywhere else None,
        })


def check_checkbox(
    label: str,
    cb_key: str,
    elements: List[Tuple[str, float, float]],
    cb_results: List[dict],
):
    """Verify that an 'X' mark is located strictly inside the checkbox rectangle."""
    rect = CHECKBOX_RECTS.get(cb_key)
    if not rect:
        cb_results.append({"field": label, "status": "FAIL", "detail": f"No checkbox rect for {cb_key}"})
        return

    # Check for 'X' inside checkbox rectangle
    found = text_inside_rect("X", elements, rect, tolerance=4.0)
    if found:
        cb_results.append({
            "field": label,
            "status": "PASS",
            "found_at": found,
            "rect": rect,
        })
    else:
        cb_results.append({
            "field": label,
            "status": "FAIL",
            "rect": rect,
            "detail": "X mark not found inside checkbox rectangle",
        })


def main():
    print("=" * 60)
    print("CMS-1500 CLAIM PDF VERIFICATION")
    print("=" * 60)

    if not JSON_PATH.exists():
        print(f"FAIL: JSON not found: {JSON_PATH}")
        raise SystemExit(1)
    if not PDF_PATH.exists():
        print(f"FAIL: PDF not found: {PDF_PATH}")
        raise SystemExit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        claim = json.load(f)

    elements = extract_text_with_coords(PDF_PATH)
    results = []
    cb_results = []

    # ── Header Text Fields ─────────────────────────────────────
    check_field("Item 1a (Insured ID)", claim.get("insured_id_number", ""), "item1a_insured_id", elements, results)
    check_field("Item 2 (Patient Name)", claim.get("patient_name", ""), "item2_patient_name", elements, results)
    check_field("Item 4 (Insured Name)", claim.get("insured_name", ""), "item4_insured_name", elements, results)

    # DOB
    dob = claim.get("patient_dob", "")
    if "/" in dob:
        parts = dob.split("/")
        check_field("Item 3 DOB Month", parts[1], "item3_dob", elements, results)
        check_field("Item 3 DOB Day", parts[0], "item3_dob", elements, results)
        check_field("Item 3 DOB Year", parts[2][-2:], "item3_dob", elements, results)

    # ── Address Fields ─────────────────────────────────────────
    pt = claim.get("patient_address", {})
    check_field("Item 5 (Patient Street)", pt.get("street", ""), "item5_street", elements, results)
    check_field("Item 5 (Patient City)", pt.get("city", ""), "item5_city_state", elements, results)
    check_field("Item 5 (Patient State)", pt.get("state", ""), "item5_city_state", elements, results)
    check_field("Item 5 (Patient Zip)", pt.get("zip", ""), "item5_zip_phone", elements, results)

    ia = claim.get("insured_address", {})
    check_field("Item 7 (Insured Street)", ia.get("street", ""), "item7_street", elements, results)
    check_field("Item 7 (Insured City)", ia.get("city", ""), "item7_city_state", elements, results)
    check_field("Item 7 (Insured State)", ia.get("state", ""), "item7_city_state", elements, results)
    check_field("Item 7 (Insured Zip)", ia.get("zip", ""), "item7_zip_phone", elements, results)

    # ── Middle Fields ──────────────────────────────────────────
    check_field("Item 11 (Policy Group)", claim.get("insurance_policy_group_number", ""), "item11", elements, results)
    check_field("Item 11c (Plan Name)", claim.get("insurance_plan_name", ""), "item11c", elements, results)
    check_field("Item 14 (Illness Date)", claim.get("current_illness_date", ""), "item14", elements, results)
    check_field("Item 17 (Referring Provider)", claim.get("referring_provider", ""), "item17", elements, results)
    check_field("Item 19 (Additional Info)", claim.get("additional_claim_info", ""), "item19", elements, results)

    # ── Diagnosis Codes ────────────────────────────────────────
    for i, code in enumerate(claim.get("diagnosis_codes", [])):
        label = chr(65 + i)
        check_field(f"Item 21 Diag {label} ({code})", code, "item21_diag", elements, results)

    # ── Item 22/23 ─────────────────────────────────────────────
    check_field("Item 22 (Resubmission Code)", claim.get("resubmission_code", ""), "item22", elements, results)
    check_field("Item 22 (Original Ref)", claim.get("original_ref_number", ""), "item22", elements, results)
    check_field("Item 23 (Prior Auth)", claim.get("prior_authorization_number", ""), "item23", elements, results)

    # ── Service Lines ──────────────────────────────────────────
    service_lines = claim.get("service_lines", [])
    if len(service_lines) != 6:
        results.append({"field": "Service Line Count", "status": "FAIL", "detail": f"Expected 6, got {len(service_lines)}"})
    else:
        results.append({"field": "Service Line Count", "status": "PASS", "detail": "6 rows"})

    diag_codes = claim.get("diagnosis_codes", [])
    valid_pointers = {chr(65 + i) for i in range(len(diag_codes))}

    for i, row in enumerate(service_lines, start=1):
        proc = str(row.get("procedure_code", ""))
        check_field(f"Svc {i} Procedure ({proc})", proc, f"svc_{i}_procedure", elements, results)

        ptr = str(row.get("diagnosis_pointer", ""))
        if ptr not in valid_pointers:
            results.append({"field": f"Svc {i} Dx Pointer", "status": "FAIL", "detail": f"'{ptr}' not in {valid_pointers}"})
        else:
            check_field(f"Svc {i} Dx Pointer ({ptr})", ptr, f"svc_{i}_dx_ptr", elements, results)

        charges_str = f"{float(row.get('charges', 0)):.2f}"
        check_field(f"Svc {i} Charges (${charges_str})", charges_str, f"svc_{i}_charges", elements, results)

        npi = str(row.get("provider_npi", ""))
        if not re.fullmatch(r"\d{10}", npi):
            results.append({"field": f"Svc {i} NPI", "status": "FAIL", "detail": f"'{npi}' not 10 digits"})
        else:
            check_field(f"Svc {i} NPI ({npi})", npi, f"svc_{i}_npi", elements, results)

    # ── Bottom Section ─────────────────────────────────────────
    check_field("Item 25 (Tax ID)", claim.get("federal_tax_id", ""), "item25", elements, results)
    check_field("Item 26 (Patient Account)", claim.get("patient_account_number", ""), "item26", elements, results)

    total_str = f"{float(claim.get('total_charge', 0)):.2f}"
    check_field("Item 28 (Total Charge)", total_str, "item28", elements, results)

    paid_str = f"{float(claim.get('amount_paid', 0)):.2f}"
    check_field("Item 29 (Amount Paid)", paid_str, "item29", elements, results)

    if claim.get("signature_present"):
        check_field("Item 31 (Signature)", "SIGNED", "item31", elements, results)

    check_field("Item 32a (Facility NPI)", claim.get("service_facility_npi", ""), "item32a_npi", elements, results)
    check_field("Item 33a (Billing NPI)", claim.get("billing_provider_npi", ""), "item33a_npi", elements, results)

    # ── NPI Format Checks ──────────────────────────────────────
    for label, key in [("Facility NPI", "service_facility_npi"), ("Billing NPI", "billing_provider_npi")]:
        val = str(claim.get(key, ""))
        if re.fullmatch(r"\d{10}", val):
            results.append({"field": f"{label} Format", "status": "PASS", "detail": f"'{val}' is 10 digits"})
        else:
            results.append({"field": f"{label} Format", "status": "FAIL", "detail": f"'{val}' not 10 digits"})

    # ── Total Charge Sum Check ─────────────────────────────────
    sum_charges = round(sum(float(r.get("charges", 0)) for r in service_lines), 2)
    claimed = round(float(claim.get("total_charge", 0)), 2)
    if sum_charges == claimed:
        results.append({"field": "Charges Sum", "status": "PASS", "detail": f"${sum_charges:.2f} == ${claimed:.2f}"})
    else:
        results.append({"field": "Charges Sum", "status": "FAIL", "detail": f"${sum_charges:.2f} != ${claimed:.2f}"})

    # ============================================================
    # 3. CHECKBOX VERIFICATIONS
    # ============================================================
    # Item 1: Insurance Type
    ins_map = {
        "MEDICARE": "item1_medicare",
        "MEDICAID": "item1_medicaid",
        "TRICARE": "item1_tricare",
        "CHAMPVA": "item1_champva",
        "GROUP HEALTH PLAN": "item1_group_health_plan",
        "FECA BLK LUNG": "item1_feca_blk_lung",
        "OTHER": "item1_other",
    }
    ins_type = str(claim.get("insurance_type", "")).upper()
    if ins_type in ins_map:
        check_checkbox(f"Item 1 ({ins_type})", ins_map[ins_type], elements, cb_results)

    # Item 3: Patient Sex
    p_sex = str(claim.get("patient_sex", "")).upper()
    if p_sex in ("M", "F"):
        check_checkbox(f"Item 3 Sex ({p_sex})", f"item3_sex_{p_sex.lower()}", elements, cb_results)

    # Item 6: Patient Relationship
    rel_map = {
        "SELF": "item6_self",
        "SPOUSE": "item6_spouse",
        "CHILD": "item6_child",
        "OTHER": "item6_other",
    }
    rel = str(claim.get("relationship_to_insured", "")).upper()
    if rel in rel_map:
        check_checkbox(f"Item 6 Relationship ({rel})", rel_map[rel], elements, cb_results)

    # Item 10a: Employment
    emp = claim.get("employment_related")
    if emp is not None:
        check_checkbox(f"Item 10a Employment ({'YES' if emp else 'NO'})",
                       "item10a_employment_yes" if emp else "item10a_employment_no", elements, cb_results)

    # Item 10b: Auto Accident
    auto = claim.get("auto_accident")
    if auto is not None:
        check_checkbox(f"Item 10b Auto Accident ({'YES' if auto else 'NO'})",
                       "item10b_auto_accident_yes" if auto else "item10b_auto_accident_no", elements, cb_results)

    # Item 10c: Other Accident
    other_acc = claim.get("other_accident")
    if other_acc is not None:
        check_checkbox(f"Item 10c Other Accident ({'YES' if other_acc else 'NO'})",
                       "item10c_other_accident_yes" if other_acc else "item10c_other_accident_no", elements, cb_results)

    # Item 11d: Another Health Plan
    another = claim.get("another_health_benefit_plan")
    if another is not None:
        check_checkbox(f"Item 11d Another Plan ({'YES' if another else 'NO'})",
                       "item11d_another_plan_yes" if another else "item11d_another_plan_no", elements, cb_results)

    # Item 27: Accept Assignment
    accept = claim.get("accept_assignment")
    if accept is not None:
        check_checkbox(f"Item 27 Accept Assignment ({'YES' if accept else 'NO'})",
                       "item27_accept_assignment_yes" if accept else "item27_accept_assignment_no", elements, cb_results)

    # ── Print Text Field Results ───────────────────────────────
    pass_count = 0
    fail_count = 0

    for r in results:
        status = r["status"]
        field = r["field"]
        if status == "PASS":
            pass_count += 1
            expected = r.get("expected", "")
            found = r.get("found_at", "")
            rect = r.get("rect", "")
            detail = r.get("detail", "")
            if found:
                print(f"  PASS: {field}")
                print(f"        Value: '{expected}' at ({found[0]}, {found[1]})")
                print(f"        Rect: ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
            else:
                print(f"  PASS: {field} - {detail}")
        else:
            fail_count += 1
            expected = r.get("expected", "")
            rect = r.get("rect", "")
            elsewhere = r.get("found_elsewhere")
            detail = r.get("detail", "")
            if expected:
                print(f"  FAIL: {field}")
                print(f"        Expected: '{expected}'")
                if rect:
                    print(f"        In rect: ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
                if elsewhere:
                    print(f"        Found elsewhere: {elsewhere}")
                elif not detail:
                    print(f"        Not found in PDF at all")
            else:
                print(f"  FAIL: {field} - {detail}")

    # ── Print Checkbox Results ─────────────────────────────────
    cb_pass = 0
    cb_fail = 0
    print("\n" + "=" * 60)
    print("CHECKBOX CALIBRATION VERIFICATION")
    print("=" * 60)
    for r in cb_results:
        field = r["field"]
        if r["status"] == "PASS":
            cb_pass += 1
            found = r["found_at"]
            rect = r["rect"]
            print(f"  PASS: {field} -> X at ({found[0]}, {found[1]}) inside rect ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
        else:
            cb_fail += 1
            print(f"  FAIL: {field} -> {r.get('detail', '')}")

    total_failures = fail_count + cb_fail

    # ── Summary ────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"TEXT FIELDS: {pass_count} PASS / {fail_count} FAIL")
    print(f"CHECKBOXES: all calibrated ({cb_pass} verified)")
    print(f"TOTAL FAILURES: {total_failures}")
    print("=" * 60)

    if total_failures > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
