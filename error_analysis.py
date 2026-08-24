import json
from pathlib import Path
from collections import Counter


GROUND_TRUTH_DIR = Path(
    "data/dataset/ground_truth"
)

EXTRACTED_DIR = Path(
    "data/dataset/extracted_10"
)


errors = Counter()


for i in range(1, 11):

    gt_file = (
        GROUND_TRUTH_DIR /
        f"claim_{i:03d}.json"
    )

    ext_file = (
        EXTRACTED_DIR /
        f"claim_{i:03d}_extracted.json"
    )

    with open(gt_file, encoding="utf-8") as f:
        gt = json.load(f)

    with open(ext_file, encoding="utf-8") as f:
        ext = json.load(f)


    # -----------------------------
    # Basic fields
    # -----------------------------

    fields = [
        "patient_name",
        "patient_dob",
        "insured_id_number",
        "insured_name",
        "total_charge",
        "amount_paid",
        "signature_present",
    ]

    for field in fields:

        expected = gt.get(field)
        actual = ext.get(field)

        if str(expected).strip().lower() != str(actual).strip().lower():
            errors[field] += 1


    # -----------------------------
    # Diagnosis
    # -----------------------------

    if gt.get("diagnosis_codes") != ext.get("diagnosis_codes"):
        errors["diagnosis_codes"] += 1


    # -----------------------------
    # Service lines
    # -----------------------------

    gt_lines = gt.get("service_lines", [])
    ext_lines = ext.get("service_lines", [])


    for row, gt_line in enumerate(gt_lines):

        if row >= len(ext_lines):
            errors[
                f"service_line_{row+1}"
            ] += 1
            continue


        ext_line = ext_lines[row]


        for field in [
            "date_of_service",
            "place_of_service",
            "procedure_code",
            "diagnosis_pointer",
            "charges",
            "units",
            "provider_npi",
        ]:

            expected = gt_line.get(field)
            actual = ext_line.get(field)

            if str(expected).strip().lower() != str(actual).strip().lower():

                errors[
                    f"service_line_{row+1}_{field}"
                ] += 1


# ============================================================
# REPORT
# ============================================================

print()
print("==========================================")
print("ERROR ANALYSIS")
print("==========================================")

if not errors:

    print("No errors found.")

else:

    for field, count in errors.most_common():

        print(
            f"{field:35} "
            f"{count} error(s)"
        )

print("==========================================")