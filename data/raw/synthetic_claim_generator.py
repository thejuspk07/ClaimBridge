"""
CMS-1500 synthetic claim generator.

Coordinate system: PDF points, origin bottom-left, page = 684 x 864 pt.
All coordinates below are drawString baselines.

VERIFICATION STATUS
--------------------
64 coordinates in this file were cross-checked against a real rendered
PDF (claim_001.pdf) using pdfplumber word-extraction: every expected
value was found within 0.3pt of its declared (x, y). Those are marked
VERIFIED in the comments below.

11 checkbox coordinates were never exercised by that sample (the
sample's JSON never set insurance_type to MEDICAID/TRICARE/etc, never
set patient_sex to F, never set relationship to Self/Child/Other, and
auto_accident was False). Those keep their pre-existing declared
values but are marked TODO - they are UNVERIFIED, not confirmed wrong,
just unconfirmed. To close them out, generate a test JSON that
exercises each one and send me the resulting PDF (not a PNG - I need
the vector text to verify positions precisely).
"""

import json
from pathlib import Path

from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


# ============================================================
# FILE PATHS
# ============================================================

JSON_PATH = Path("data/processed/claim_001.json")
TEMPLATE_PATH = Path("data/raw/Sample 1500_2012_02.pdf")
OVERLAY_PATH = Path("data/raw/overlay.pdf")
OUTPUT_PATH = Path("data/raw/claim_001.pdf")

PAGE_WIDTH = 684
PAGE_HEIGHT = 864


# ============================================================
# FIELD_COORDS  (single-value text fields + checkboxes)
# Every entry: "label": (x, y, size)
# ============================================================

FIELD_COORDS = {
    # ---- VERIFIED (0.0-0.3pt deviation against claim_001.pdf) ----
    "item1a_insured_id":            (416, 713, 8),
    "item2_patient_name":           (64, 691, 9),
    "item3_dob_month":              (271, 687, 8),
    "item3_dob_day":                (299, 687, 8),
    "item3_dob_year":               (321, 687, 8),
    "item3_sex_m":                  (352, 686, 9),
    "item4_insured_name":           (380, 691, 7),
    "item5_street":                 (35, 652, 7),
    "item5_city":                   (35, 615, 7),
    "item5_state":                  (245, 615, 7),
    "item5_zip":                    (35, 577, 7),
    "item5_phone":                  (170, 577, 7),
    "item6_spouse":                 (293, 649, 9),
    "item7_street":                 (380, 652, 7),
    "item7_city":                   (380, 615, 7),
    "item7_state":                  (610, 615, 7),
    "item7_zip":                    (380, 577, 7),
    "item7_phone":                  (510, 577, 7),
    "item9_other_insured_name":     (35, 540, 7),
    "item9a_other_policy_group":    (35, 505, 7),
    "item10a_employment":           (280, 508, 9),
    "item10c_other_accident":       (280, 461, 9),
    "item11_policy_group":          (380, 540, 7),
    "item11a_insured_dob_mm":       (390, 505, 7),
    "item11a_insured_dob_dd":       (418, 505, 7),
    "item11a_insured_dob_yy":       (440, 505, 7),
    "item11c_plan_name":            (380, 447, 7),
    "item11d_another_plan":         (392, 409, 9),
    "item14_illness_date":          (35, 420, 7),
    "item17_referring_provider":    (35, 382, 7),
    "item18_hosp_from":             (390, 382, 7),
    "item18_hosp_to":               (505, 382, 7),
    "item19_additional_info":       (35, 350, 7),
    "item21_diag_a":                (35, 300, 7),
    "item21_diag_b":                (170, 300, 7),
    "item21_diag_c":                (300, 300, 7),
    "item21_diag_d":                (435, 300, 7),
    "item22_resubmission_code":     (380, 300, 7),
    "item22_original_ref":          (475, 300, 7),
    "item23_prior_auth":            (380, 275, 7),
    "item25_federal_tax_id":        (35, 88, 7),
    "item26_patient_account":       (220, 88, 7),
    "item27_accept_assignment":     (340, 88, 9),
    "item28_total_charge":          (420, 88, 7),
    "item29_amount_paid":           (510, 88, 7),
    "item31_signature":             (65, 75, 9),
    "item32_facility_street":       (220, 55, 7),
    "item32_facility_city":         (220, 42, 7),
    "item32_facility_state":        (300, 42, 7),
    "item32_facility_zip":          (350, 42, 7),
    "item32a_facility_npi":         (350, 28, 7),
    "item33_billing_street":        (380, 55, 7),
    "item33_billing_city":          (380, 42, 7),
    "item33_billing_state":         (450, 42, 7),
    "item33_billing_zip":           (500, 42, 7),
    "item33a_billing_npi":          (500, 28, 7),
    "item1_medicare":               (36, 714, 9),

    # ---- TODO: unverified checkboxes (unchanged from original script) ----
    "item1_medicaid":                (91, 714, 9),   # TODO
    "item1_tricare":                 (145, 714, 9),  # TODO
    "item1_champva":                 (208, 714, 9),  # TODO
    "item1_group_health_plan":       (274, 714, 9),  # TODO
    "item1_feca_blk_lung":           (338, 714, 9),  # TODO
    "item1_other":                   (392, 714, 9),  # TODO
    "item3_sex_f":                   (369, 686, 9),  # TODO
    "item6_self":                    (254, 649, 9),  # TODO
    "item6_child":                   (326, 649, 9),  # TODO
    "item6_other":                   (359, 649, 9),  # TODO
    "item10b_auto_accident":         (280, 485, 9),  # TODO
}

# ============================================================
# SERVICE_LINE_COORDS  (VERIFIED - 6 rows, 24pt spacing, exact)
# ============================================================

SERVICE_ROW_TOP_Y = 280
SERVICE_ROW_HEIGHT = 24

SERVICE_LINE_X = {
    "date": 63,
    "place_of_service": 194,
    "procedure": 235,
    "diagnosis_pointer": 378,
    "charges": 414,
    "units": 500,
    "provider_npi": 560,
}

SERVICE_LINE_COORDS = {
    row: {field: (x, SERVICE_ROW_TOP_Y - (row - 1) * SERVICE_ROW_HEIGHT)
          for field, x in SERVICE_LINE_X.items()}
    for row in range(1, 7)
}


# ============================================================
# HELPERS
# ============================================================

def draw_text(pdf, x, y, value, size=8):
    """Draw a text value. x = distance from left, y = distance from bottom."""
    if value is None or value == "":
        return
    pdf.setFont("Helvetica", size)
    pdf.drawString(x, y, str(value))


def draw_checkbox(pdf, x, y, checked, size=9):
    """Draw an X at (x, y) if checked is truthy."""
    if not checked:
        return
    pdf.setFont("Helvetica-Bold", size)
    pdf.drawString(x, y, "X")


def draw_field(pdf, key, value):
    """Draw a text value using its FIELD_COORDS entry."""
    x, y, size = FIELD_COORDS[key]
    draw_text(pdf, x, y, value, size)


def draw_checkbox_field(pdf, key, checked):
    """Draw a checkbox using its FIELD_COORDS entry."""
    x, y, size = FIELD_COORDS[key]
    draw_checkbox(pdf, x, y, checked, size)


def draw_service_line(pdf, row_num, service):
    """Draw one row (1-6) of item 24 from a service-line dict."""
    coords = SERVICE_LINE_COORDS[row_num]
    draw_text(pdf, *coords["date"], service.get("date_of_service", ""))
    draw_text(pdf, *coords["place_of_service"], service.get("place_of_service", ""))
    draw_text(pdf, *coords["procedure"], service.get("procedure_code", ""))
    draw_text(pdf, *coords["diagnosis_pointer"], service.get("diagnosis_pointer", ""))
    draw_text(pdf, *coords["charges"], f'{service.get("charges", 0):.2f}')
    draw_text(pdf, *coords["units"], service.get("units", ""))
    draw_text(pdf, *coords["provider_npi"], service.get("provider_npi", ""))


# ============================================================
# LOAD CLAIM JSON
# ============================================================

with open(JSON_PATH, "r", encoding="utf-8") as f:
    claim = json.load(f)

print("==========================================")
print("Loading synthetic claim")
print("==========================================")
print(f"Patient      : {claim['patient_name']}")
print(f"DOB          : {claim['patient_dob']}")
print(f"Insured ID   : {claim['insured_id_number']}")
print(f"Diagnoses    : {claim['diagnosis_codes']}")
print(f"Service rows : {len(claim['service_lines'])}")
print(f"Total charge : ${claim['total_charge']:.2f}")
print()


# ============================================================
# BUILD OVERLAY
# ============================================================

overlay = canvas.Canvas(str(OVERLAY_PATH), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
overlay.setFillColorRGB(0, 0, 0)

# Item 1 - insurance type
INSURANCE_TYPE_KEYS = {
    "MEDICARE": "item1_medicare",
    "MEDICAID": "item1_medicaid",
    "TRICARE": "item1_tricare",
    "CHAMPVA": "item1_champva",
    "GROUP HEALTH PLAN": "item1_group_health_plan",
    "FECA BLK LUNG": "item1_feca_blk_lung",
    "OTHER": "item1_other",
}
insurance_type = claim.get("insurance_type", "")
if insurance_type in INSURANCE_TYPE_KEYS:
    draw_checkbox_field(overlay, INSURANCE_TYPE_KEYS[insurance_type], True)

draw_field(overlay, "item1a_insured_id", claim["insured_id_number"])
draw_field(overlay, "item2_patient_name", claim["patient_name"])

day, month, year = claim["patient_dob"].split("/")
draw_field(overlay, "item3_dob_month", month)
draw_field(overlay, "item3_dob_day", day)
draw_field(overlay, "item3_dob_year", year[-2:])

if claim.get("patient_sex") == "M":
    draw_checkbox_field(overlay, "item3_sex_m", True)
else:
    draw_checkbox_field(overlay, "item3_sex_f", True)

draw_field(overlay, "item4_insured_name", claim.get("insured_name", ""))

patient_address = claim.get("patient_address", {})
draw_field(overlay, "item5_street", patient_address.get("street", ""))
draw_field(overlay, "item5_city", patient_address.get("city", ""))
draw_field(overlay, "item5_state", patient_address.get("state", ""))
draw_field(overlay, "item5_zip", patient_address.get("zip", ""))
draw_field(overlay, "item5_phone", patient_address.get("phone", ""))

RELATIONSHIP_KEYS = {
    "Self": "item6_self",
    "Spouse": "item6_spouse",
    "Child": "item6_child",
    "Other": "item6_other",
}
relationship = claim.get("relationship_to_insured", "")
if relationship in RELATIONSHIP_KEYS:
    draw_checkbox_field(overlay, RELATIONSHIP_KEYS[relationship], True)

insured_address = claim.get("insured_address", {})
draw_field(overlay, "item7_street", insured_address.get("street", ""))
draw_field(overlay, "item7_city", insured_address.get("city", ""))
draw_field(overlay, "item7_state", insured_address.get("state", ""))
draw_field(overlay, "item7_zip", insured_address.get("zip", ""))
draw_field(overlay, "item7_phone", insured_address.get("phone", ""))

draw_field(overlay, "item9_other_insured_name", claim.get("other_insured_name", ""))
draw_field(overlay, "item9a_other_policy_group", claim.get("other_insured_policy_group", ""))

draw_checkbox_field(overlay, "item10a_employment", claim.get("employment_related"))
draw_checkbox_field(overlay, "item10b_auto_accident", claim.get("auto_accident"))
draw_checkbox_field(overlay, "item10c_other_accident", claim.get("other_accident"))

draw_field(overlay, "item11_policy_group", claim.get("insurance_policy_group_number", ""))

if claim.get("insured_dob"):
    i_day, i_month, i_year = claim["insured_dob"].split("/")
    draw_field(overlay, "item11a_insured_dob_mm", i_month)
    draw_field(overlay, "item11a_insured_dob_dd", i_day)
    draw_field(overlay, "item11a_insured_dob_yy", i_year[-2:])

draw_field(overlay, "item11c_plan_name", claim.get("insurance_plan_name", ""))
draw_checkbox_field(overlay, "item11d_another_plan", claim.get("another_health_benefit_plan"))

draw_field(overlay, "item14_illness_date", claim.get("current_illness_date", ""))
draw_field(overlay, "item17_referring_provider", claim.get("referring_provider", ""))

hospitalization = claim.get("hospitalization_dates", {})
draw_field(overlay, "item18_hosp_from", hospitalization.get("from", ""))
draw_field(overlay, "item18_hosp_to", hospitalization.get("to", ""))

draw_field(overlay, "item19_additional_info", claim.get("additional_claim_info", ""))

diag_keys = ["item21_diag_a", "item21_diag_b", "item21_diag_c", "item21_diag_d"]
for code, key in zip(claim.get("diagnosis_codes", []), diag_keys):
    draw_field(overlay, key, code)

draw_field(overlay, "item22_resubmission_code", claim.get("resubmission_code", ""))
draw_field(overlay, "item22_original_ref", claim.get("original_ref_number", ""))
draw_field(overlay, "item23_prior_auth", claim.get("prior_authorization_number", ""))

for index, service in enumerate(claim.get("service_lines", [])[:6]):
    draw_service_line(overlay, index + 1, service)

draw_field(overlay, "item25_federal_tax_id", claim.get("federal_tax_id", ""))
draw_field(overlay, "item26_patient_account", claim.get("patient_account_number", ""))
draw_checkbox_field(overlay, "item27_accept_assignment", claim.get("accept_assignment"))
draw_field(overlay, "item28_total_charge", f'{claim.get("total_charge", 0):.2f}')
draw_field(overlay, "item29_amount_paid", f'{claim.get("amount_paid", 0):.2f}')

if claim.get("signature_present"):
    draw_field(overlay, "item31_signature", "SIGNED")

facility = claim.get("service_facility", {})
draw_field(overlay, "item32_facility_street", facility.get("street", ""))
draw_field(overlay, "item32_facility_city", facility.get("city", ""))
draw_field(overlay, "item32_facility_state", facility.get("state", ""))
draw_field(overlay, "item32_facility_zip", facility.get("zip", ""))
draw_field(overlay, "item32a_facility_npi", claim.get("service_facility_npi", ""))

provider = claim.get("billing_provider", {})
draw_field(overlay, "item33_billing_street", provider.get("street", ""))
draw_field(overlay, "item33_billing_city", provider.get("city", ""))
draw_field(overlay, "item33_billing_state", provider.get("state", ""))
draw_field(overlay, "item33_billing_zip", provider.get("zip", ""))
draw_field(overlay, "item33a_billing_npi", claim.get("billing_provider_npi", ""))

overlay.save()
print(f"Overlay created: {OVERLAY_PATH}")


# ============================================================
# MERGE ONTO TEMPLATE
# ============================================================

original = PdfReader(str(TEMPLATE_PATH))
overlay_pdf = PdfReader(str(OVERLAY_PATH))

page = original.pages[0]
page.merge_page(overlay_pdf.pages[0])

writer = PdfWriter()
writer.add_page(page)

with open(OUTPUT_PATH, "wb") as f:
    writer.write(f)

print()
print("==========================================")
print("FULL SYNTHETIC CLAIM CREATED")
print("==========================================")
print(f"PDF  : {OUTPUT_PATH}")
print(f"JSON : {JSON_PATH}")
print(f"Rows : {len(claim['service_lines'])}")
print(f"Total: ${claim['total_charge']:.2f}")
print("==========================================")