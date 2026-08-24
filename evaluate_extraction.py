import json
from pathlib import Path


# ============================================================
# FILES
# ============================================================

GROUND_TRUTH_PATH = Path(
    "data/processed/claim_001.json"
)

EXTRACTED_PATH = Path(
    "data/processed/extracted_claim.json"
)


# ============================================================
# LOAD BOTH JSON FILES
# ============================================================

with open(
    GROUND_TRUTH_PATH,
    "r",
    encoding="utf-8"
) as file:
    ground_truth = json.load(file)


with open(
    EXTRACTED_PATH,
    "r",
    encoding="utf-8"
) as file:
    extracted = json.load(file)


# ============================================================
# COMPARISON STORAGE
# ============================================================

results = []


def compare_field(name, expected, actual):
    """
    Compare one field.

    Think:
    teacher answer vs student answer.
    """

    correct = expected == actual

    results.append(
        {
            "field": name,
            "expected": expected,
            "actual": actual,
            "correct": correct,
        }
    )


# ============================================================
# BASIC CLAIM FIELDS
# ============================================================

compare_field(
    "patient_name",
    ground_truth.get("patient_name"),
    extracted.get("patient_name"),
)

compare_field(
    "patient_dob",
    ground_truth.get("patient_dob"),
    extracted.get("patient_dob"),
)

compare_field(
    "insured_id_number",
    ground_truth.get("insured_id_number"),
    extracted.get("insured_id_number"),
)

compare_field(
    "insured_name",
    ground_truth.get("insured_name"),
    extracted.get("insured_name"),
)


# ============================================================
# DIAGNOSIS CODES
# ============================================================

expected_diagnosis = ground_truth.get(
    "diagnosis_codes",
    []
)

actual_diagnosis = extracted.get(
    "diagnosis_codes",
    []
)

compare_field(
    "diagnosis_codes",
    expected_diagnosis,
    actual_diagnosis,
)


# ============================================================
# SERVICE LINES
# ============================================================

expected_lines = ground_truth.get(
    "service_lines",
    []
)

actual_lines = extracted.get(
    "service_lines",
    []
)


# ------------------------------------------------------------
# Number of service rows
# ------------------------------------------------------------

compare_field(
    "service_line_count",
    len(expected_lines),
    len(actual_lines),
)


# ------------------------------------------------------------
# Compare each service line
# ------------------------------------------------------------

for index, expected in enumerate(
    expected_lines
):

    if index >= len(actual_lines):

        results.append(
            {
                "field":
                    f"service_line_{index + 1}",
                "expected": expected,
                "actual": None,
                "correct": False,
            }
        )

        continue

    actual = actual_lines[index]


    compare_field(
        f"service_line_{index + 1}_procedure",
        expected.get("procedure_code"),
        actual.get("procedure_code"),
    )

    compare_field(
        f"service_line_{index + 1}_diagnosis_pointer",
        expected.get("diagnosis_pointer"),
        actual.get("diagnosis_pointer"),
    )

    compare_field(
        f"service_line_{index + 1}_charges",
        expected.get("charges"),
        actual.get("charges"),
    )

    compare_field(
        f"service_line_{index + 1}_provider_npi",
        expected.get("provider_npi"),
        actual.get("provider_npi"),
    )


# ============================================================
# TOTAL CHARGE
# ============================================================

compare_field(
    "total_charge",
    ground_truth.get("total_charge"),
    extracted.get("total_charge"),
)


# ============================================================
# AMOUNT PAID
# ============================================================

compare_field(
    "amount_paid",
    ground_truth.get("amount_paid"),
    extracted.get("amount_paid"),
)


# ============================================================
# SIGNATURE
# ============================================================

compare_field(
    "signature_present",
    ground_truth.get("signature_present"),
    extracted.get("signature_present"),
)


# ============================================================
# CALCULATE ACCURACY
# ============================================================

total_fields = len(results)

correct_fields = sum(
    1
    for result in results
    if result["correct"]
)


accuracy = (
    correct_fields / total_fields * 100
    if total_fields
    else 0
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("==========================================")
print("CLAIM EXTRACTION EVALUATION")
print("==========================================")

for result in results:

    status = (
        "PASS"
        if result["correct"]
        else "FAIL"
    )

    print(
        f"{status:4} | "
        f"{result['field']}"
    )

    if not result["correct"]:

        print(
            f"      Expected: "
            f"{result['expected']}"
        )

        print(
            f"      Actual  : "
            f"{result['actual']}"
        )


print("------------------------------------------")

print(
    f"Correct fields : "
    f"{correct_fields}/{total_fields}"
)

print(
    f"Accuracy       : "
    f"{accuracy:.2f}%"
)

print("==========================================")


# ============================================================
# SAVE EVALUATION REPORT
# ============================================================

report = {
    "correct_fields": correct_fields,
    "total_fields": total_fields,
    "accuracy_percent": round(
        accuracy,
        2
    ),
    "results": results,
}


REPORT_PATH = Path(
    "data/processed/evaluation_report.json"
)

with open(
    REPORT_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        report,
        file,
        indent=4
    )


print(
    f"Report saved to: {REPORT_PATH}"
)