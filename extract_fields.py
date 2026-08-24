import json
import re
from pathlib import Path


# ============================================================
# FILES
# ============================================================

OCR_PATH = Path("data/processed/ocr_output.json")
OUTPUT_PATH = Path("data/processed/extracted_claim.json")


# ============================================================
# LOAD OCR JSON
# ============================================================

with open(
    OCR_PATH,
    "r",
    encoding="utf-8"
) as file:

    ocr_data = json.load(file)


# ============================================================
# BASIC HELPERS
# ============================================================

def center(item):
    """
    Get the center X/Y of an OCR bounding box.
    """

    box = item["bbox"]

    cx = (
        box["x1"] +
        box["x2"]
    ) / 2

    cy = (
        box["y1"] +
        box["y2"]
    ) / 2

    return cx, cy


def in_region(item, region):
    """
    Check whether the OCR item's center
    lies inside a rectangular region.

    region = (x1, y1, x2, y2)
    """

    x1, y1, x2, y2 = region

    cx, cy = center(item)

    return (
        x1 <= cx <= x2
        and
        y1 <= cy <= y2
    )


def find_in_region(
    region,
    min_confidence=0.0
):
    """
    Return OCR detections inside a region.
    """

    results = []

    for item in ocr_data:

        if item["confidence"] < min_confidence:
            continue

        if in_region(
            item,
            region
        ):
            results.append(item)

    return results


def text_items(
    region,
    min_confidence=0.0
):
    """
    Return OCR items from a region.
    """

    return [
        item
        for item in find_in_region(
            region,
            min_confidence
        )
    ]


def longest_text(
    region,
    min_confidence=0.0
):
    """
    Pick the longest OCR text in a region.
    """

    matches = text_items(
        region,
        min_confidence
    )

    if not matches:
        return None

    return max(
        matches,
        key=lambda item:
        len(item["text"].strip())
    )


def numeric_text(
    region,
    min_confidence=0.0
):
    """
    Return OCR items containing only digits.
    """

    matches = text_items(
        region,
        min_confidence
    )

    output = []

    for item in matches:

        value = item["text"].strip()

        if value.isdigit():
            output.append(item)

    return output


def value_with_highest_confidence(items):
    """
    Pick the highest-confidence OCR result.
    """

    if not items:
        return None

    return max(
        items,
        key=lambda item:
        item["confidence"]
    )


def parse_money(value):
    """
    Convert OCR money text into float.
    """

    if value is None:
        return None

    value = value.replace(
        "$",
        ""
    )

    value = value.replace(
        ",",
        ""
    )

    value = value.strip()

    try:
        return float(value)

    except ValueError:
        return None


def is_npi(value):
    """
    NPI = exactly 10 digits.
    """

    return bool(
        re.fullmatch(
            r"\d{10}",
            value
        )
    )


def is_icd10(value):
    """
    Simple ICD-10 style check.
    """

    return bool(
        re.fullmatch(
            r"[A-Z]\d{2}(?:\.\d+)?",
            value.upper()
        )
    )


def is_procedure_code(value):
    """
    CPT/HCPCS-like numeric code.
    """

    return (
        value.isdigit()
        and
        len(value) == 5
    )


def normalize_diagnosis_text(text):
    """
    Correct common OCR mistakes for diagnosis codes.

    Important:
    This function is ONLY used for diagnosis-code
    extraction.

    Example:
        OCR: 110
        Correct: I10
    """

    text = text.strip().upper()

    ocr_corrections = {
        "110": "I10",
    }

    return ocr_corrections.get(
        text,
        text
    )


def normalize_two_digit_year(year):
    """
    Convert a two-digit birth year into a four-digit year.

    Examples:
        66 -> 1966
        03 -> 2003
        99 -> 1999
        26 -> 2026

    For DOB, years <= 25 are treated as 2000s.
    Years > 25 are treated as 1900s.
    """

    year = int(year)

    if year <= 25:
        return f"20{year:02d}"

    return f"19{year:02d}"


# ============================================================
# FIELD REGIONS
#
# PNG/OCR coordinate system.
#
# Batch images:
# 1368 x 1728
# ============================================================


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

REGION_INSURANCE_ID = (
    820, 280,
    1000, 310
)

REGION_PATIENT_NAME = (
    120, 325,
    280, 355
)

REGION_DOB = (
    525, 330,
    675, 365
)

REGION_INSURED_NAME = (
    815, 325,
    1160, 355
)


# ------------------------------------------------------------
# PATIENT ADDRESS
# ------------------------------------------------------------

REGION_PATIENT_STREET = (
    120, 375,
    280, 405
)

REGION_PATIENT_CITY = (
    110, 400,
    300, 475
)

REGION_PATIENT_STATE = (
    450, 400,
    540, 470
)

REGION_PATIENT_ZIP = (
    115, 470,
    220, 510
)

REGION_PATIENT_PHONE = (
    290, 465,
    500, 510
)


# ------------------------------------------------------------
# INSURED ADDRESS
# ------------------------------------------------------------

REGION_INSURED_STREET = (
    815, 375,
    1010, 405
)

REGION_INSURED_CITY = (
    815, 400,
    980, 475
)

REGION_INSURED_STATE = (
    1130, 400,
    1210, 470
)

REGION_INSURED_ZIP = (
    815, 470,
    900, 510
)

REGION_INSURED_PHONE = (
    995, 465,
    1140, 510
)


# ------------------------------------------------------------
# OTHER INSURED
# ------------------------------------------------------------

REGION_OTHER_INSURED = (
    120, 520,
    500, 555
)

REGION_OTHER_POLICY = (
    120, 555,
    500, 600
)


# ------------------------------------------------------------
# ITEM 11
# ------------------------------------------------------------

REGION_POLICY_GROUP = (
    820, 515,
    1100, 550
)

REGION_INSURED_DOB = (
    820, 560,
    970, 600
)

REGION_PLAN_NAME = (
    815, 655,
    980, 695
)


# ------------------------------------------------------------
# CLAIM INFORMATION
# ------------------------------------------------------------

REGION_ILLNESS_DATE = (
    115, 850,
    300, 890
)

REGION_REFERRING_PROVIDER = (
    115, 900,
    330, 940
)

REGION_HOSPITALIZATION = (
    830, 900,
    1210, 935
)

REGION_ADDITIONAL_INFO = (
    115, 950,
    500, 980
)


# ------------------------------------------------------------
# DIAGNOSIS A-D
# ------------------------------------------------------------

DIAGNOSIS_REGIONS = [
    (130, 1000, 220, 1040),
    (320, 1000, 410, 1040),
    (500, 1000, 590, 1040),
    (680, 1000, 770, 1040),
]


# ------------------------------------------------------------
# ITEM 22 / 23
# ------------------------------------------------------------

REGION_RESUBMISSION = (
    815, 1045,
    860, 1080
)

REGION_ORIGINAL_REF = (
    980, 1045,
    1100, 1080
)

REGION_PRIOR_AUTH = (
    815, 1080,
    940, 1120
)


# ============================================================
# SERVICE LINE REGIONS
# ============================================================

SERVICE_ROWS = [
    1150,
    1200,
    1248,
    1297,
    1345,
    1390,
]


# ------------------------------------------------------------
# SERVICE LINE X RANGES
# ------------------------------------------------------------

SERVICE_PROCEDURE_X = (
    450,
    530
)

SERVICE_DX_X = (
    740,
    785
)

SERVICE_CHARGE_X = (
    805,
    900
)

SERVICE_UNITS_X = (
    930,
    980
)

SERVICE_NPI_X = (
    1075,
    1165
)

SERVICE_DATE_X = (
    110,
    215
)

SERVICE_POS_X = (
    360,
    410
)


# ============================================================
# BOTTOM FIELDS
# ============================================================

REGION_TAX_ID = (
    115, 1425,
    230, 1460
)

REGION_ACCOUNT = (
    420, 1425,
    550, 1460
)

REGION_TOTAL_CHARGE = (
    815, 1425,
    900, 1460
)

REGION_AMOUNT_PAID = (
    975, 1425,
    1040, 1460
)

REGION_SIGNATURE = (
    115, 1545,
    220, 1590
)

REGION_FACILITY = (
    425, 1485,
    650, 1540
)

REGION_FACILITY_NPI = (
    480, 1545,
    600, 1585
)

REGION_BILLING_PROVIDER = (
    815, 1485,
    1000, 1540
)

REGION_BILLING_NPI = (
    980, 1545,
    1100, 1585
)


# ============================================================
# EXTRACT HEADER FIELDS
# ============================================================


# ------------------------------------------------------------
# PATIENT NAME
# ------------------------------------------------------------

item = longest_text(
    REGION_PATIENT_NAME,
    0.80
)

patient_name = (
    item["text"]
    if item
    else None
)

patient_name_confidence = (
    item["confidence"]
    if item
    else 0.0
)


# ------------------------------------------------------------
# INSURED ID
# ------------------------------------------------------------

insured_id = None
insured_id_confidence = 0.0

for item in text_items(
    REGION_INSURANCE_ID,
    0.80
):

    value = item["text"].strip()

    if value.startswith("INS"):

        insured_id = value

        insured_id_confidence = (
            item["confidence"]
        )

        break


# ------------------------------------------------------------
# INSURED NAME
# ------------------------------------------------------------

item = longest_text(
    REGION_INSURED_NAME,
    0.80
)

insured_name = (
    item["text"]
    if item
    else None
)

insured_name_confidence = (
    item["confidence"]
    if item
    else 0.0
)


# ============================================================
# DOB
# ============================================================

dob_items = numeric_text(
    REGION_DOB,
    0.80
)

dob_items.sort(
    key=lambda item:
    center(item)[0]
)

dob_values = [
    item["text"]
    for item in dob_items
]

patient_dob = None
patient_dob_confidence = 0.0


if len(dob_values) >= 3:

    month = dob_values[0]
    day = dob_values[1]
    year = dob_values[2]

    # Convert the 2-digit year correctly.
    full_year = normalize_two_digit_year(
        year
    )

    patient_dob = (
        f"{day}/{month}/{full_year}"
    )

    patient_dob_confidence = min(
        item["confidence"]
        for item in dob_items[:3]
    )


# ============================================================
# ADDRESS FIELDS
# ============================================================


# ------------------------------------------------------------
# PATIENT STREET
# ------------------------------------------------------------

item = longest_text(
    REGION_PATIENT_STREET,
    0.80
)

patient_street = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# PATIENT CITY
# ------------------------------------------------------------

item = longest_text(
    REGION_PATIENT_CITY,
    0.80
)

patient_city = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# PATIENT STATE
# ------------------------------------------------------------

item = longest_text(
    REGION_PATIENT_STATE,
    0.80
)

patient_state = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# PATIENT ZIP
# ------------------------------------------------------------

item = longest_text(
    REGION_PATIENT_ZIP,
    0.80
)

patient_zip = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# PATIENT PHONE
# ------------------------------------------------------------

item = longest_text(
    REGION_PATIENT_PHONE,
    0.80
)

patient_phone = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# INSURED STREET
# ------------------------------------------------------------

item = longest_text(
    REGION_INSURED_STREET,
    0.80
)

insured_street = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# INSURED CITY
# ------------------------------------------------------------

item = longest_text(
    REGION_INSURED_CITY,
    0.80
)

insured_city = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# INSURED STATE
# ------------------------------------------------------------

item = longest_text(
    REGION_INSURED_STATE,
    0.80
)

insured_state = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# INSURED ZIP
# ------------------------------------------------------------

item = longest_text(
    REGION_INSURED_ZIP,
    0.80
)

insured_zip = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# INSURED PHONE
# ------------------------------------------------------------

item = longest_text(
    REGION_INSURED_PHONE,
    0.80
)

insured_phone = (
    item["text"]
    if item
    else None
)


# ============================================================
# OTHER INSURED
# ============================================================

item = longest_text(
    REGION_OTHER_INSURED,
    0.80
)

other_insured_name = (
    item["text"]
    if item
    else None
)

item = longest_text(
    REGION_OTHER_POLICY,
    0.80
)

other_policy_group = (
    item["text"]
    if item
    else None
)


# ============================================================
# ITEM 11
# ============================================================

item = longest_text(
    REGION_POLICY_GROUP,
    0.80
)

policy_group = (
    item["text"]
    if item
    else None
)

item = longest_text(
    REGION_PLAN_NAME,
    0.80
)

insurance_plan = (
    item["text"]
    if item
    else None
)


# ============================================================
# CLAIM INFORMATION
# ============================================================

item = longest_text(
    REGION_ILLNESS_DATE,
    0.80
)

illness_date = (
    item["text"]
    if item
    else None
)

item = longest_text(
    REGION_REFERRING_PROVIDER,
    0.80
)

referring_provider = (
    item["text"]
    if item
    else None
)

item = longest_text(
    REGION_HOSPITALIZATION,
    0.80
)

hospitalization = (
    item["text"]
    if item
    else None
)

item = longest_text(
    REGION_ADDITIONAL_INFO,
    0.80
)

additional_info = (
    item["text"]
    if item
    else None
)


# ============================================================
# DIAGNOSIS CODES
# ============================================================

diagnosis_codes = []
diagnosis_confidences = []


for region in DIAGNOSIS_REGIONS:

    matches = find_in_region(
        region,
        0.75
    )

    candidates = []


    for item in matches:

        raw_text = item["text"].strip()

        # Normalize common OCR mistake:
        # I10 -> 110
        text = normalize_diagnosis_text(
            raw_text
        )

        if is_icd10(text):

            corrected_item = dict(item)

            corrected_item["text"] = text

            candidates.append(
                corrected_item
            )


    best = value_with_highest_confidence(
        candidates
    )


    if best:

        diagnosis_codes.append(
            best["text"]
        )

        diagnosis_confidences.append(
            best["confidence"]
        )


# ============================================================
# SERVICE LINES
# ============================================================

service_lines = []


for line_number, row_y in enumerate(
    SERVICE_ROWS,
    start=1
):

    y1 = row_y - 25
    y2 = row_y + 25


    # ========================================================
    # DATE OF SERVICE
    #
    # Handles:
    #
    # 02/08/2026
    #
    # OR:
    #
    # 21/07
    # 2026
    #
    # OR:
    #
    # 16/04/
    # 2026
    # ========================================================

    date_matches = find_in_region(
        (
            SERVICE_DATE_X[0],
            y1,
            SERVICE_DATE_X[1],
            y2
        ),
        0.60
    )


    date_matches.sort(
        key=lambda item:
        center(item)[0]
    )


    service_date = None
    date_parts = []


    # --------------------------------------------------------
    # STEP 1: complete date
    # --------------------------------------------------------

    for item in date_matches:

        text = item["text"].strip()

        if re.fullmatch(
            r"\d{2}/\d{2}/\d{4}",
            text
        ):

            service_date = text

            break


    # --------------------------------------------------------
    # STEP 2: collect split parts
    # --------------------------------------------------------

    if service_date is None:

        for item in date_matches:

            text = item["text"].strip()


            if re.fullmatch(
                r"\d{2}/\d{2}/?",
                text
            ):

                date_parts.append(
                    text.rstrip("/")
                )


            elif re.fullmatch(
                r"\d{4}",
                text
            ):

                date_parts.append(
                    text
                )


    # --------------------------------------------------------
    # STEP 3: reconstruct split date
    # --------------------------------------------------------

    if service_date is None:

        combined = "".join(
            date_parts
        )

        match = re.search(
            r"(\d{2})/(\d{2})/?(\d{4})",
            combined
        )

        if match:

            day = match.group(1)
            month = match.group(2)
            year = match.group(3)

            service_date = (
                f"{day}/{month}/{year}"
            )


    # ========================================================
    # PLACE OF SERVICE
    # ========================================================

    pos_matches = find_in_region(
        (
            SERVICE_POS_X[0],
            y1,
            SERVICE_POS_X[1],
            y2
        ),
        0.75
    )

    place_of_service = None

    for item in pos_matches:

        text = item["text"].strip()

        if text in {
            "11",
            "21",
            "22",
            "23"
        }:

            place_of_service = text

            break


    # ========================================================
    # PROCEDURE CODE
    # ========================================================

    procedure_matches = find_in_region(
        (
            SERVICE_PROCEDURE_X[0],
            y1,
            SERVICE_PROCEDURE_X[1],
            y2
        ),
        0.75
    )

    procedure = None

    for item in procedure_matches:

        text = item["text"].strip()

        if is_procedure_code(text):

            procedure = text

            break


    # ========================================================
    # DIAGNOSIS POINTER
    # ========================================================

    pointer_matches = find_in_region(
        (
            SERVICE_DX_X[0],
            y1,
            SERVICE_DX_X[1],
            y2
        ),
        0.75
    )

    diagnosis_pointer = None

    for item in pointer_matches:

        text = item["text"].strip()

        if re.fullmatch(
            r"[A-L]",
            text,
            re.IGNORECASE
        ):

            diagnosis_pointer = (
                text.upper()
            )

            break


    # ========================================================
    # CHARGE
    # ========================================================

    charge_matches = find_in_region(
        (
            SERVICE_CHARGE_X[0],
            y1,
            SERVICE_CHARGE_X[1],
            y2
        ),
        0.75
    )

    charge = None

    for item in charge_matches:

        parsed = parse_money(
            item["text"]
        )

        if parsed is not None:

            charge = parsed

            break


    # ========================================================
    # UNITS
    # ========================================================

    units_matches = find_in_region(
        (
            SERVICE_UNITS_X[0],
            y1,
            SERVICE_UNITS_X[1],
            y2
        ),
        0.75
    )

    units = None

    for item in units_matches:

        text = item["text"].strip()

        if text.isdigit():

            units = int(text)

            break


    # ========================================================
    # PROVIDER NPI
    # ========================================================

    npi_matches = find_in_region(
        (
            SERVICE_NPI_X[0],
            y1,
            SERVICE_NPI_X[1],
            y2
        ),
        0.75
    )

    provider_npi = None

    for item in npi_matches:

        text = item["text"].strip()

        if is_npi(text):

            provider_npi = text

            break


    # ========================================================
    # SAVE SERVICE LINE
    # ========================================================

    service_lines.append(
        {
            "line_number":
                line_number,

            "date_of_service":
                service_date,

            "place_of_service":
                place_of_service,

            "procedure_code":
                procedure,

            "diagnosis_pointer":
                diagnosis_pointer,

            "charges":
                charge,

            "units":
                units,

            "provider_npi":
                provider_npi,
        }
    )


# ============================================================
# BOTTOM FIELDS
# ============================================================


# ------------------------------------------------------------
# TAX ID
# ------------------------------------------------------------

item = longest_text(
    REGION_TAX_ID,
    0.80
)

federal_tax_id = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# PATIENT ACCOUNT
# ------------------------------------------------------------

item = longest_text(
    REGION_ACCOUNT,
    0.80
)

patient_account_number = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# TOTAL CHARGE
# ------------------------------------------------------------

item = longest_text(
    REGION_TOTAL_CHARGE,
    0.80
)

total_charge = (
    parse_money(
        item["text"]
    )
    if item
    else None
)


# ------------------------------------------------------------
# AMOUNT PAID
# ------------------------------------------------------------

item = longest_text(
    REGION_AMOUNT_PAID,
    0.60
)

amount_paid = (
    parse_money(
        item["text"]
    )
    if item
    else None
)


# ------------------------------------------------------------
# SIGNATURE
# ------------------------------------------------------------

item = longest_text(
    REGION_SIGNATURE,
    0.80
)

signature = (
    item["text"]
    if item
    else None
)

signature_present = (
    signature is not None
)


# ------------------------------------------------------------
# SERVICE FACILITY
# ------------------------------------------------------------

item = longest_text(
    REGION_FACILITY,
    0.70
)

service_facility = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# SERVICE FACILITY NPI
# ------------------------------------------------------------

item = longest_text(
    REGION_FACILITY_NPI,
    0.80
)

service_facility_npi = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# BILLING PROVIDER
# ------------------------------------------------------------

item = longest_text(
    REGION_BILLING_PROVIDER,
    0.70
)

billing_provider = (
    item["text"]
    if item
    else None
)


# ------------------------------------------------------------
# BILLING PROVIDER NPI
# ------------------------------------------------------------

item = longest_text(
    REGION_BILLING_NPI,
    0.80
)

billing_provider_npi = (
    item["text"]
    if item
    else None
)


# ============================================================
# CONFIDENCE SUMMARY
# ============================================================

field_confidences = {

    "patient_name":
        patient_name_confidence,

    "patient_dob":
        patient_dob_confidence,

    "insured_id_number":
        insured_id_confidence,

    "insured_name":
        insured_name_confidence,
}


# ------------------------------------------------------------
# Diagnosis confidence
# ------------------------------------------------------------

if diagnosis_confidences:

    field_confidences[
        "diagnosis_codes"
    ] = (

        sum(
            diagnosis_confidences
        )
        /
        len(
            diagnosis_confidences
        )
    )


# ------------------------------------------------------------
# Service confidence
# ------------------------------------------------------------

service_confidences = []


for line in service_lines:

    for item in ocr_data:

        text = item["text"].strip()


        if text in {
            line["procedure_code"],
            line["diagnosis_pointer"],
            line["provider_npi"],
        }:

            service_confidences.append(
                item["confidence"]
            )


if service_confidences:

    field_confidences[
        "service_lines"
    ] = (

        sum(
            service_confidences
        )
        /
        len(
            service_confidences
        )
    )


# ============================================================
# BUILD FINAL EXTRACTED CLAIM
# ============================================================

extracted_claim = {

    "patient_name":
        patient_name,

    "patient_dob":
        patient_dob,

    "insured_id_number":
        insured_id,

    "insured_name":
        insured_name,

    "patient_address": {

        "street":
            patient_street,

        "city":
            patient_city,

        "state":
            patient_state,

        "zip":
            patient_zip,

        "phone":
            patient_phone,
    },

    "insured_address": {

        "street":
            insured_street,

        "city":
            insured_city,

        "state":
            insured_state,

        "zip":
            insured_zip,

        "phone":
            insured_phone,
    },

    "other_insured_name":
        other_insured_name,

    "other_insured_policy_group":
        other_policy_group,

    "insurance_policy_group_number":
        policy_group,

    "insurance_plan_name":
        insurance_plan,

    "current_illness_date":
        illness_date,

    "referring_provider":
        referring_provider,

    "hospitalization":
        hospitalization,

    "additional_claim_info":
        additional_info,

    "diagnosis_codes":
        diagnosis_codes,

    "service_lines":
        service_lines,

    "federal_tax_id":
        federal_tax_id,

    "patient_account_number":
        patient_account_number,

    "total_charge":
        total_charge,

    "amount_paid":
        amount_paid,

    "signature_present":
        signature_present,

    "service_facility":
        service_facility,

    "service_facility_npi":
        service_facility_npi,

    "billing_provider":
        billing_provider,

    "billing_provider_npi":
        billing_provider_npi,

    "field_confidences":
        field_confidences,
}


# ============================================================
# SAVE RESULT
# ============================================================

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        extracted_claim,
        file,
        indent=4
    )


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print()
print(
    "=========================================="
)

print(
    "FULL FIELD EXTRACTION COMPLETE"
)

print(
    "=========================================="
)

print(
    f"Patient       : {patient_name}"
)

print(
    f"DOB           : {patient_dob}"
)

print(
    f"Insured ID    : {insured_id}"
)

print(
    f"Insured Name  : {insured_name}"
)

print(
    f"Diagnoses     : {diagnosis_codes}"
)

print(
    f"Service rows  : {len(service_lines)}"
)

print(
    f"Total charge  : {total_charge}"
)

print(
    f"Amount paid   : {amount_paid}"
)

print(
    f"Signature     : {signature_present}"
)

print(
    f"Saved to      : {OUTPUT_PATH}"
)

print(
    "=========================================="
)