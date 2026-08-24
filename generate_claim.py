"""
CMS-1500 (02/12) Synthetic Claim Generator.

Renders structured claim JSON data onto the official CMS-1500 PDF template
using coordinates calibrated against the actual template field boundaries.

Coordinate system: PDF points, origin bottom-left, page = 684 x 864 pt.
Field boundaries determined from pdfplumber line extraction of the template.

CALIBRATION METHOD
------------------
All coordinates below were derived from the actual template PDF
(Sample 1500_2012_02.pdf) using pdfplumber to extract every horizontal
and vertical line, then mapping each field's writable region:

  writable_baseline_y = field_bottom_border + offset  (typically 3-6 pt)
  writable_x = field_left_border + 3 pt padding

Field boundaries verified against a 10pt-grid overlay PNG rendered at 2x.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

# ============================================================
# 1. FILE PATHS & PAGE DIMENSIONS
# ============================================================

ROOT = Path(__file__).resolve().parent

JSON_PATH = ROOT / "data" / "processed" / "claim_001.json"
TEMPLATE_PATH = ROOT / "data" / "raw" / "Sample 1500_2012_02.pdf"
OVERLAY_PATH = ROOT / "data" / "raw" / "overlay.pdf"
OUTPUT_PATH = ROOT / "data" / "raw" / "claim_001.pdf"

PAGE_WIDTH = 684
PAGE_HEIGHT = 864


# ============================================================
# 2. CALIBRATED FIELD COORDINATES
#
# Format: "field_name": (x, y_baseline, font_size)
#
# Template boundary reference (rl_y = ReportLab Y, bottom-up):
#   Form top:    rl_y=732
#   Form bottom: rl_y=72
#   Left edge:   x=60
#   Right edge:  x=629
#   Center div:  x=267 (left half) / x=411 (right half start)
#
# Row boundaries (horizontal lines):
#   Item 1 row:      top=732, bot=707   → baseline ~713
#   Item 2/3/4 row:  top=707, bot=684   → baseline ~691
#   Item 5st/6/7st:  top=684, bot=660   → baseline ~666
#   Item 5ci/8/7ci:  top=660, bot=636   → baseline ~642
#   Item 5zi/7zi:    top=636, bot=611   → baseline ~617
#   Item 9/11:       top=611, bot=588   → baseline ~594
#   Item 9a/10a/11a: top=588, bot=565   → baseline ~571
#   Item 9b/10b/11b: top=565, bot=540   → baseline ~546
#   Item 9c/10c/11c: top=540, bot=516   → baseline ~522
#   Item 9d/10d/11d: top=516, bot=492   → baseline ~498
#   Item 12/13:      top=492, bot=444   → baseline ~455
#   Item 14/15/16:   top=444, bot=420   → baseline ~426
#   Item 17/17a/18:  top=420, bot=396   → baseline ~402
#   Item 19/20:      top=396, bot=372   → baseline ~378
#   Item 21 diag:    top=372, bot=324   → cells at 351/339/327
#   Item 22/23:      top=324, bot=301   → baseline ~308
#   Svc row 1:       top=301, bot=277   → baseline ~283
#   Svc row 2:       top=277, bot=252   → baseline ~258
#   Svc row 3:       top=252, bot=229   → baseline ~235
#   Svc row 4:       top=229, bot=204   → baseline ~210
#   Svc row 5:       top=204, bot=181   → baseline ~187
#   Svc row 6:       top=181, bot=157   → baseline ~163
#   Item 25-30:      top=157, bot=133   → baseline ~140
#   Item 31-33:      top=133, bot=72    → street ~110, city ~93, npi ~78
# ============================================================

FIELD_COORDS = {
    # ── Item 1: Insurance Type Checkboxes ──────────────────────
    # Row: top=732, bot=707. Checkboxes: rect=(x0, 708, x1, 721), size 13x13.
    "item1_medicare":          (63.5,  711.5, 9),
    "item1_medicaid":          (115.5, 711.5, 9),
    "item1_tricare":           (167.5, 711.5, 9),
    "item1_champva":           (235.5, 711.5, 9),
    "item1_group_health_plan": (288.5, 711.5, 9),
    "item1_feca_blk_lung":     (342.5, 711.5, 9),
    "item1_other":             (393.5, 711.5, 9),

    # ── Item 1a: Insured's ID Number ──────────────────────────
    # Same row as Item 1, right portion. x=411 to x=629.
    "item1a_insured_id": (416, 713, 8),  # VERIFIED

    # ── Item 2: Patient's Name ────────────────────────────────
    # Row: top=707, bot=684. Left half x=60 to x=267.
    "item2_patient_name": (64, 691, 9),  # VERIFIED

    # ── Item 3: Patient's Birth Date & Sex ────────────────────
    # Same row as Item 2, between x=267 and x=411.
    "item3_dob_month": (271, 687, 8),  # VERIFIED
    "item3_dob_day":   (299, 687, 8),  # VERIFIED
    "item3_dob_year":  (321, 687, 8),  # VERIFIED
    "item3_sex_m":     (357, 689, 9),  # checkbox rect=(354,686,366,698)
    "item3_sex_f":     (393, 689, 9),  # checkbox rect=(390,686,402,698)

    # ── Item 4: Insured's Name ────────────────────────────────
    # Same row as Item 2, right half x=411 to x=629.
    "item4_insured_name": (415, 691, 7),

    # ── Item 5: Patient's Address ─────────────────────────────
    # Street: row top=684, bot=660. Left half x=60 to x=267.
    "item5_street": (64, 666, 7),
    # City: row top=660, bot=636. x=60 to x=240.
    "item5_city":   (64, 642, 7),
    # State: same row as city. x=240 to x=267.
    "item5_state":  (243, 642, 7),
    # Zip: row top=636, bot=611. x=60 to x=154.
    "item5_zip":    (64, 617, 7),
    # Phone: same row as zip. x=154 to x=267.
    "item5_phone":  (157, 617, 7),

    # ── Item 6: Patient Relationship to Insured ───────────────
    # Row top=684, bot=660 (same as Item 5 street), center area x=267-411.
    "item6_self":   (293, 664.5, 9),
    "item6_spouse": (330, 664.5, 9),
    "item6_child":  (367, 664.5, 9),
    "item6_other":  (402, 664.5, 9),

    # ── Item 7: Insured's Address ─────────────────────────────
    # Street: row top=684, bot=660, right half x=411 to x=629.
    "item7_street": (415, 666, 7),
    # City: row top=660, bot=636. x=411 to x=582.
    "item7_city":   (415, 642, 7),
    # State: same row as city. x=582 to x=629.
    "item7_state":  (585, 642, 7),
    # Zip: row top=636, bot=611. x=411 to x=504.
    "item7_zip":    (415, 617, 7),
    # Phone: same row as zip. x=504 to x=629.
    "item7_phone":  (507, 617, 7),

    # ── Item 9: Other Insured's Name ──────────────────────────
    # Row top=611, bot=588. Left half x=60 to x=267.
    "item9_other_insured_name": (64, 594, 7),

    # ── Item 9a: Other Insured's Policy/Group ─────────────────
    # Row top=588, bot=565. Left half x=60 to x=267.
    "item9a_other_policy_group": (64, 571, 7),

    # ── Item 10a: Employment Related ──────────────────────────
    # Row top=588, bot=565. Center area x=267 to x=411.
    "item10a_employment_yes": (306, 568.5, 9),
    "item10a_employment_no":  (348, 568.5, 9),

    # ── Item 10b: Auto Accident ───────────────────────────────
    # Row top=565, bot=540. Center area.
    "item10b_auto_accident_yes": (306, 544.5, 9),
    "item10b_auto_accident_no":  (348, 544.5, 9),

    # ── Item 10c: Other Accident ──────────────────────────────
    # Row top=540, bot=516. Center area.
    "item10c_other_accident_yes": (306, 519.5, 9),
    "item10c_other_accident_no":  (348, 519.5, 9),

    # ── Item 11: Insured's Policy Group / FECA Number ─────────
    # Row top=611, bot=588. Right half x=411 to x=629.
    "item11_policy_group": (415, 594, 7),

    # ── Item 11a: Insured's Date of Birth & Sex ──────────────
    # Row top=588, bot=565. Right half.
    "item11a_insured_dob_mm": (415, 571, 7),
    "item11a_insured_dob_dd": (443, 571, 7),
    "item11a_insured_dob_yy": (465, 571, 7),
    "item11a_insured_sex_m":  (510, 571, 9),
    "item11a_insured_sex_f":  (550, 571, 9),

    # ── Item 11c: Insurance Plan Name ─────────────────────────
    # Row top=540, bot=516. Right half x=411 to x=629.
    "item11c_plan_name": (415, 522, 7),

    # ── Item 11d: Is There Another Health Benefit Plan? ───────
    # Row top=516, bot=492. Right half.
    "item11d_another_plan_yes": (428, 497, 9),
    "item11d_another_plan_no":  (464, 497, 9),

    # ── Item 14: Date of Current Illness ──────────────────────
    # Row top=444, bot=420. Left portion x=60 to x=253.
    "item14_illness_date": (64, 426, 7),

    # ── Item 17: Referring Provider ───────────────────────────
    # Row top=420, bot=396. Left portion x=60 to x=269.
    "item17_referring_provider": (64, 402, 7),

    # ── Item 18: Hospitalization Dates ────────────────────────
    # Row top=420, bot=396. Right area.
    # FROM: near x=494, TO: near x=564.
    "item18_hosp_from": (497, 402, 7),
    "item18_hosp_to":   (567, 402, 7),

    # ── Item 19: Additional Claim Information ─────────────────
    # Row top=396, bot=372. Full width x=60 to x=629.
    "item19_additional_info": (64, 378, 7),

    # ── Item 21: Diagnosis Codes (ICD-10) ─────────────────────
    # Diagnosis cell grid between rl_y=372 and rl_y=324.
    # Underline rows at rl_y: 349, 338, 325.
    # Baselines: row1=351, row2=339, row3=327.
    # Column cells (from template lines):
    #   Col 1 (A/E/I): x=74 to x=125 → write at x=77
    #   Col 2 (B/F/J): x=167 to x=218 → write at x=170
    #   Col 3 (C/G/K): x=261 to x=312 → write at x=264
    #   Col 4 (D/H/L): x=355 to x=406 → write at x=358
    "item21_diag_a": (77,  351, 7),
    "item21_diag_b": (170, 351, 7),
    "item21_diag_c": (264, 351, 7),
    "item21_diag_d": (358, 351, 7),
    "item21_diag_e": (77,  339, 7),
    "item21_diag_f": (170, 339, 7),
    "item21_diag_g": (264, 339, 7),
    "item21_diag_h": (358, 339, 7),
    "item21_diag_i": (77,  327, 7),
    "item21_diag_j": (170, 327, 7),
    "item21_diag_k": (264, 327, 7),
    "item21_diag_l": (358, 327, 7),

    # ── Item 22: Resubmission Code & Original Ref ─────────────
    # Row top=348, bot=324 (right half x=411 to x=629).
    # Resubmission code: x=411 to ~494. Original ref: x=494 to x=629.
    "item22_resubmission_code": (415, 330, 7),
    "item22_original_ref":      (497, 330, 7),

    # ── Item 23: Prior Authorization Number ───────────────────
    # Row top=324, bot=301 (right half x=411 to x=629).
    "item23_prior_auth": (415, 308, 7),

    # ── Item 25: Federal Tax ID ───────────────────────────────
    # Row top=157, bot=133. x=60 to x=216.
    "item25_federal_tax_id": (64, 140, 7),

    # ── Item 26: Patient's Account Number ─────────────────────
    # Row top=157, bot=133. x=217 to x=322.
    "item26_patient_account": (220, 140, 7),

    # ── Item 27: Accept Assignment ────────────────────────────
    # Row top=157, bot=133. x=322 to x=411.
    "item27_accept_assignment_yes": (328, 138.5, 9),
    "item27_accept_assignment_no":  (369, 138.5, 9),

    # ── Item 28: Total Charge ─────────────────────────────────
    # Row top=157, bot=133. x=411 to x=492.
    "item28_total_charge": (416, 140, 7),

    # ── Item 29: Amount Paid ──────────────────────────────────
    # Row top=157, bot=133. x=492 to x=560.
    "item29_amount_paid": (496, 140, 7),

    # ── Item 31: Signature ────────────────────────────────────
    # Row top=133, bot=72. Left block x=60 to x=217.
    "item31_signature": (65, 75, 9),  # VERIFIED

    # ── Item 32: Service Facility Location Information ────────
    # Row top=133, bot=72. Middle block x=217 to x=411.
    # Street: baseline ~110.
    "item32_facility_name":   (220, 120, 6),
    "item32_facility_street": (220, 110, 6),
    "item32_facility_city":   (220, 100, 6),
    "item32_facility_state":  (310, 100, 6),
    "item32_facility_zip":    (340, 100, 6),
    # NPI: on the rl_y=86 line. x=217 to x=300 for "a." then x=300 to x=411.
    "item32a_facility_npi":   (250, 78, 7),

    # ── Item 33: Billing Provider Info ────────────────────────
    # Row top=133, bot=72. Right block x=411 to x=629.
    "item33_billing_name":   (415, 120, 6),
    "item33_billing_street": (415, 110, 6),
    "item33_billing_city":   (415, 100, 6),
    "item33_billing_state":  (485, 100, 6),
    "item33_billing_zip":    (510, 100, 6),
    # NPI: on rl_y=86. x=494 to x=629.
    "item33a_billing_npi":   (500, 78, 7),
}


# ============================================================
# 3. SERVICE LINE COORDINATES (Item 24)
#
# 6 rows between rl_y=301 (top) and rl_y=157 (bottom).
# Row boundaries from template lines:
#   Row 1: top=301, bot=277 → baseline ~283
#   Row 2: top=277, bot=252 → baseline ~258
#   Row 3: top=252, bot=229 → baseline ~235
#   Row 4: top=229, bot=204 → baseline ~210
#   Row 5: top=204, bot=181 → baseline ~187
#   Row 6: top=181, bot=157 → baseline ~163
#
# Column boundaries from template vertical lines:
#   24A Date From: x=60 to x=123 → write at x=63
#   24B POS:       x=187 to x=210 → write at x=190
#   24D Procedure: x=232 to x=284 → write at x=235 (VERIFIED)
#   24E Dx Ptr:    x=375 to x=411 → write at x=378 (VERIFIED)
#   24F Charges:   x=411 to x=475 → write at x=414 (VERIFIED)
#   24G Units:     x=475 to x=504 → write at x=478
#   24J NPI:       x=540 to x=629 → write at x=543
# ============================================================

SERVICE_ROW_Y = {
    1: 283,
    2: 258,
    3: 235,
    4: 210,
    5: 187,
    6: 163,
}

SERVICE_COL_X = {
    "date":              63,   # 24A
    "place_of_service": 190,   # 24B
    "procedure":        235,   # 24D (VERIFIED)
    "diagnosis_pointer": 378,  # 24E (VERIFIED)
    "charges":          414,   # 24F (VERIFIED)
    "units":            478,   # 24G
    "provider_npi":     543,   # 24J
}

SERVICE_LINE_COORDS = {
    row: {field: (x, SERVICE_ROW_Y[row]) for field, x in SERVICE_COL_X.items()}
    for row in range(1, 7)
}


# ============================================================
# 4. FIELD BOUNDARY RECTANGLES (for verification)
# Each: (x0, y0_bottom, x1, y1_top) in ReportLab coords.
# ============================================================

FIELD_RECTS = {
    "item1a_insured_id":   (411, 707, 629, 732),
    "item2_patient_name":  (60,  684, 267, 707),
    "item3_dob":           (267, 684, 350, 707),
    "item4_insured_name":  (411, 684, 629, 707),
    "item5_street":        (60,  660, 267, 684),
    "item5_city":          (60,  636, 240, 660),
    "item5_state":         (240, 636, 267, 660),
    "item5_zip":           (60,  611, 154, 636),
    "item5_phone":         (154, 611, 267, 636),
    "item7_street":        (411, 660, 629, 684),
    "item7_city":          (411, 636, 582, 660),
    "item7_state":         (582, 636, 629, 660),
    "item7_zip":           (411, 611, 504, 636),
    "item7_phone":         (504, 611, 629, 636),
    "item9":               (60,  588, 267, 611),
    "item9a":              (60,  565, 267, 588),
    "item11":              (411, 588, 629, 611),
    "item11a":             (411, 565, 629, 588),
    "item11c":             (411, 516, 629, 540),
    "item14":              (60,  420, 253, 444),
    "item17":              (60,  396, 269, 420),
    "item18":              (494, 396, 629, 420),
    "item19":              (60,  372, 629, 396),
    "item21_a":            (74,  338, 125, 349),
    "item21_b":            (167, 338, 218, 349),
    "item21_c":            (261, 338, 312, 349),
    "item21_d":            (355, 338, 406, 349),
    "item22":              (411, 324, 629, 348),
    "item23":              (411, 301, 629, 324),
    "item25":              (60,  133, 216, 157),
    "item26":              (217, 133, 322, 157),
    "item27":              (322, 133, 411, 157),
    "item28":              (411, 133, 492, 157),
    "item29":              (492, 133, 560, 157),
    "item31":              (60,  72,  217, 133),
    "item32":              (217, 72,  411, 133),
    "item33":              (411, 72,  629, 133),
}


# ============================================================
# 5. DRAWING HELPERS
# ============================================================

def draw_text(pdf: canvas.Canvas, x: float, y: float, value: Any, size: int = 8) -> None:
    """Draw text at baseline (x, y)."""
    if value is None or str(value).strip() == "":
        return
    pdf.setFont("Helvetica", size)
    pdf.drawString(x, y, str(value).strip())


def draw_checkbox(pdf: canvas.Canvas, x: float, y: float, checked: bool, size: int = 9) -> None:
    """Draw an X mark if checked."""
    if not checked:
        return
    pdf.setFont("Helvetica-Bold", size)
    pdf.drawString(x, y, "X")


def draw_field(pdf: canvas.Canvas, key: str, value: Any) -> None:
    """Draw a text field using FIELD_COORDS."""
    if key not in FIELD_COORDS:
        return
    x, y, size = FIELD_COORDS[key]
    draw_text(pdf, x, y, value, size)


def draw_checkbox_field(pdf: canvas.Canvas, key: str, checked: bool) -> None:
    """Draw a checkbox using FIELD_COORDS."""
    if key not in FIELD_COORDS:
        return
    x, y, size = FIELD_COORDS[key]
    draw_checkbox(pdf, x, y, checked, size)


def parse_date(date_str: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse DD/MM/YYYY into (day, month, year)."""
    if not date_str:
        return None, None, None
    s = str(date_str).strip()
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            return parts[0].zfill(2), parts[1].zfill(2), parts[2]
    return None, None, None


def draw_service_line(pdf: canvas.Canvas, row_num: int, service: Dict[str, Any]) -> None:
    """Draw one service row (1-6) of Item 24."""
    coords = SERVICE_LINE_COORDS.get(row_num)
    if not coords:
        return
    draw_text(pdf, *coords["date"], service.get("date_of_service", ""), 6)
    draw_text(pdf, *coords["place_of_service"], service.get("place_of_service", ""), 7)
    draw_text(pdf, *coords["procedure"], service.get("procedure_code", ""), 7)
    draw_text(pdf, *coords["diagnosis_pointer"], service.get("diagnosis_pointer", ""), 7)
    charges = service.get("charges")
    if charges is not None:
        try:
            draw_text(pdf, *coords["charges"], f"{float(charges):.2f}", 7)
        except (ValueError, TypeError):
            draw_text(pdf, *coords["charges"], str(charges), 7)
    draw_text(pdf, *coords["units"], str(service.get("units", "")), 7)
    draw_text(pdf, *coords["provider_npi"], service.get("provider_npi", ""), 6)


# ============================================================
# 6. OVERLAY BUILDER
# ============================================================

def build_overlay(claim: Dict[str, Any], overlay_path: Union[str, Path]) -> None:
    """Render all claim fields onto the overlay PDF."""
    o = canvas.Canvas(str(overlay_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    o.setFillColorRGB(0, 0, 0)

    # ── Item 1: Insurance Type ────────────────────────────────
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
        draw_checkbox_field(o, ins_map[ins_type], True)

    # ── Item 1a: Insured's ID ─────────────────────────────────
    draw_field(o, "item1a_insured_id", claim.get("insured_id_number", ""))

    # ── Item 2: Patient Name ──────────────────────────────────
    draw_field(o, "item2_patient_name", claim.get("patient_name", ""))

    # ── Item 3: Patient DOB & Sex ─────────────────────────────
    p_day, p_month, p_year = parse_date(claim.get("patient_dob"))
    if p_month:
        draw_field(o, "item3_dob_month", p_month)
    if p_day:
        draw_field(o, "item3_dob_day", p_day)
    if p_year:
        draw_field(o, "item3_dob_year", p_year[-2:])
    p_sex = str(claim.get("patient_sex", "")).upper()
    if p_sex == "M":
        draw_checkbox_field(o, "item3_sex_m", True)
    elif p_sex == "F":
        draw_checkbox_field(o, "item3_sex_f", True)

    # ── Item 4: Insured's Name ────────────────────────────────
    draw_field(o, "item4_insured_name", claim.get("insured_name", ""))

    # ── Item 5: Patient Address ───────────────────────────────
    pt = claim.get("patient_address", {})
    draw_field(o, "item5_street", pt.get("street", ""))
    draw_field(o, "item5_city", pt.get("city", ""))
    draw_field(o, "item5_state", pt.get("state", ""))
    draw_field(o, "item5_zip", pt.get("zip", ""))
    draw_field(o, "item5_phone", pt.get("phone", ""))

    # ── Item 6: Patient Relationship ──────────────────────────
    rel_map = {
        "SELF": "item6_self",
        "SPOUSE": "item6_spouse",
        "CHILD": "item6_child",
        "OTHER": "item6_other",
    }
    rel = str(claim.get("relationship_to_insured", "")).upper()
    if rel in rel_map:
        draw_checkbox_field(o, rel_map[rel], True)

    # ── Item 7: Insured Address ───────────────────────────────
    ia = claim.get("insured_address", {})
    draw_field(o, "item7_street", ia.get("street", ""))
    draw_field(o, "item7_city", ia.get("city", ""))
    draw_field(o, "item7_state", ia.get("state", ""))
    draw_field(o, "item7_zip", ia.get("zip", ""))
    draw_field(o, "item7_phone", ia.get("phone", ""))

    # ── Item 9 / 9a: Other Insured ────────────────────────────
    draw_field(o, "item9_other_insured_name", claim.get("other_insured_name", ""))
    draw_field(o, "item9a_other_policy_group", claim.get("other_insured_policy_group", ""))

    # ── Item 10a: Employment Related ──────────────────────────
    emp = claim.get("employment_related")
    if emp is not None:
        draw_checkbox_field(o, "item10a_employment_yes" if emp else "item10a_employment_no", True)

    # ── Item 10b: Auto Accident ───────────────────────────────
    auto = claim.get("auto_accident")
    if auto is not None:
        draw_checkbox_field(o, "item10b_auto_accident_yes" if auto else "item10b_auto_accident_no", True)

    # ── Item 10c: Other Accident ──────────────────────────────
    other_acc = claim.get("other_accident")
    if other_acc is not None:
        draw_checkbox_field(o, "item10c_other_accident_yes" if other_acc else "item10c_other_accident_no", True)

    # ── Item 11: Policy Group ─────────────────────────────────
    draw_field(o, "item11_policy_group", claim.get("insurance_policy_group_number", ""))

    # ── Item 11a: Insured DOB & Sex ───────────────────────────
    if claim.get("insured_dob"):
        i_day, i_month, i_year = parse_date(claim.get("insured_dob"))
        if i_month:
            draw_field(o, "item11a_insured_dob_mm", i_month)
        if i_day:
            draw_field(o, "item11a_insured_dob_dd", i_day)
        if i_year:
            draw_field(o, "item11a_insured_dob_yy", i_year[-2:])
    ins_sex = str(claim.get("insured_sex", "")).upper()
    if ins_sex == "M":
        draw_checkbox_field(o, "item11a_insured_sex_m", True)
    elif ins_sex == "F":
        draw_checkbox_field(o, "item11a_insured_sex_f", True)

    # ── Item 11c: Plan Name ───────────────────────────────────
    draw_field(o, "item11c_plan_name", claim.get("insurance_plan_name", ""))

    # ── Item 11d: Another Health Plan ─────────────────────────
    another = claim.get("another_health_benefit_plan")
    if another is not None:
        draw_checkbox_field(o, "item11d_another_plan_yes" if another else "item11d_another_plan_no", True)

    # ── Item 14: Illness Date ─────────────────────────────────
    draw_field(o, "item14_illness_date", claim.get("current_illness_date", ""))

    # ── Item 17: Referring Provider ───────────────────────────
    draw_field(o, "item17_referring_provider", claim.get("referring_provider", ""))

    # ── Item 18: Hospitalization Dates ────────────────────────
    hosp = claim.get("hospitalization_dates", {})
    draw_field(o, "item18_hosp_from", hosp.get("from", ""))
    draw_field(o, "item18_hosp_to", hosp.get("to", ""))

    # ── Item 19: Additional Claim Info ────────────────────────
    draw_field(o, "item19_additional_info", claim.get("additional_claim_info", ""))

    # ── Item 21: Diagnosis Codes ──────────────────────────────
    diag_keys = [
        "item21_diag_a", "item21_diag_b", "item21_diag_c", "item21_diag_d",
        "item21_diag_e", "item21_diag_f", "item21_diag_g", "item21_diag_h",
        "item21_diag_i", "item21_diag_j", "item21_diag_k", "item21_diag_l",
    ]
    for code, key in zip(claim.get("diagnosis_codes", []), diag_keys):
        draw_field(o, key, code)

    # ── Item 22: Resubmission / Original Ref ──────────────────
    draw_field(o, "item22_resubmission_code", claim.get("resubmission_code", ""))
    draw_field(o, "item22_original_ref", claim.get("original_ref_number", ""))

    # ── Item 23: Prior Authorization ──────────────────────────
    draw_field(o, "item23_prior_auth", claim.get("prior_authorization_number", ""))

    # ── Item 24: Service Lines (6 rows) ───────────────────────
    for idx, service in enumerate(claim.get("service_lines", [])[:6]):
        draw_service_line(o, idx + 1, service)

    # ── Item 25: Federal Tax ID ───────────────────────────────
    draw_field(o, "item25_federal_tax_id", claim.get("federal_tax_id", ""))

    # ── Item 26: Patient Account Number ───────────────────────
    draw_field(o, "item26_patient_account", claim.get("patient_account_number", ""))

    # ── Item 27: Accept Assignment ────────────────────────────
    accept = claim.get("accept_assignment")
    if accept is not None:
        draw_checkbox_field(o, "item27_accept_assignment_yes" if accept else "item27_accept_assignment_no", True)

    # ── Item 28: Total Charge ─────────────────────────────────
    total = claim.get("total_charge")
    if total is not None:
        try:
            draw_field(o, "item28_total_charge", f"{float(total):.2f}")
        except (ValueError, TypeError):
            draw_field(o, "item28_total_charge", str(total))

    # ── Item 29: Amount Paid ──────────────────────────────────
    paid = claim.get("amount_paid", 0.0)
    try:
        draw_field(o, "item29_amount_paid", f"{float(paid):.2f}")
    except (ValueError, TypeError):
        draw_field(o, "item29_amount_paid", str(paid))

    # ── Item 31: Signature ────────────────────────────────────
    if claim.get("signature_present", True):
        draw_field(o, "item31_signature", "SIGNED")

    # ── Item 32: Service Facility ─────────────────────────────
    fac = claim.get("service_facility", {})
    draw_field(o, "item32_facility_street", fac.get("street", ""))
    city_st_zip = f"{fac.get('city', '')}, {fac.get('state', '')} {fac.get('zip', '')}"
    draw_field(o, "item32_facility_city", city_st_zip.strip(", "))
    draw_field(o, "item32a_facility_npi", claim.get("service_facility_npi", ""))

    # ── Item 33: Billing Provider ─────────────────────────────
    prov = claim.get("billing_provider", {})
    draw_field(o, "item33_billing_street", prov.get("street", ""))
    prov_csz = f"{prov.get('city', '')}, {prov.get('state', '')} {prov.get('zip', '')}"
    draw_field(o, "item33_billing_city", prov_csz.strip(", "))
    draw_field(o, "item33a_billing_npi", claim.get("billing_provider_npi", ""))

    o.save()


# ============================================================
# 7. MERGE OVERLAY ONTO TEMPLATE
# ============================================================

def generate_claim(
    json_path: Path = JSON_PATH,
    template_path: Path = TEMPLATE_PATH,
    overlay_path: Path = OVERLAY_PATH,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Load JSON, build overlay, merge onto template, save output PDF."""
    if not json_path.exists():
        raise FileNotFoundError(f"Claim JSON not found: {json_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"Template PDF not found: {template_path}")

    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        claim = json.load(f)

    print("==========================================")
    print("Generating CMS-1500 Claim PDF")
    print("==========================================")
    print(f"JSON Source  : {json_path}")
    print(f"Patient Name : {claim.get('patient_name')}")
    print(f"Insured ID   : {claim.get('insured_id_number')}")
    print(f"DOB          : {claim.get('patient_dob')}")
    print(f"Diagnosis    : {claim.get('diagnosis_codes')}")
    print(f"Service Rows : {len(claim.get('service_lines', []))}")
    print(f"Total Charge : ${float(claim.get('total_charge', 0)):.2f}")
    print("==========================================")

    # Build overlay
    build_overlay(claim, overlay_path)
    print(f"Overlay  : {overlay_path}")

    # Merge overlay onto template
    template_reader = PdfReader(str(template_path))
    overlay_reader = PdfReader(str(overlay_path))
    page = template_reader.pages[0]
    page.merge_page(overlay_reader.pages[0])

    writer = PdfWriter()
    writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Output   : {output_path}")
    print("==========================================")
    return output_path


if __name__ == "__main__":
    generate_claim()
