import json
from pathlib import Path


# ============================================================
# FOLDERS
# ============================================================

GROUND_TRUTH_DIR = Path(
    "data/dataset/ground_truth"
)

EXTRACTED_DIR = Path(
    "data/dataset/extracted_10"
)


# ============================================================
# FIELDS WE WANT TO CHECK
# ============================================================

BASIC_FIELDS = [
    "patient_name",
    "patient_dob",
    "insured_id_number",
    "insured_name",
    "federal_tax_id",
    "patient_account_number",
    "total_charge",
    "amount_paid",
    "signature_present",
]


# ============================================================
# SMALL HELPER
# ============================================================

def same(a, b):
    """
    Compare two values safely.

    Example:

    '1560.98'
    and
    1560.98

    should be considered the same.
    """

    if a is None and b is None:
        return True

    if a is None or b is None:
        return False

    # Money values
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 0.01

    return str(a).strip().lower() == str(b).strip().lower()


# ============================================================
# TOTAL COUNTERS
# ============================================================

total_checks = 0
correct_checks = 0

claim_scores = []


# ============================================================
# PROCESS 10 CLAIMS
# ============================================================

for claim_number in range(1, 11):

    gt_file = (
        GROUND_TRUTH_DIR
        / f"claim_{claim_number:03d}.json"
    )

    ext_file = (
        EXTRACTED_DIR
        / f"claim_{claim_number:03d}_extracted.json"
    )


    if not gt_file.exists():
        print(
            f"Missing ground truth: {gt_file}"
        )
        continue

    if not ext_file.exists():
        print(
            f"Missing extraction: {ext_file}"
        )
        continue


    # --------------------------------------------------------
    # LOAD JSON FILES
    # --------------------------------------------------------

    with open(
        gt_file,
        "r",
        encoding="utf-8"
    ) as file:
        ground_truth = json.load(file)


    with open(
        ext_file,
        "r",
        encoding="utf-8"
    ) as file:
        extracted = json.load(file)


    claim_total = 0
    claim_correct = 0


    print()
    print(
        f"========== CLAIM {claim_number:03d} =========="
    )


    # ========================================================
    # BASIC FIELDS
    # ========================================================

    for field in BASIC_FIELDS:

        expected = ground_truth.get(field)
        actual = extracted.get(field)

        claim_total += 1
        total_checks += 1

        if same(expected, actual):

            claim_correct += 1
            correct_checks += 1

            print(
                f"PASS | {field}"
            )

        else:

            print(
                f"FAIL | {field}"
            )

            print(
                f"      Expected: {expected}"
            )

            print(
                f"      Actual  : {actual}"
            )


    # ========================================================
    # DIAGNOSIS CODES
    # ========================================================

    expected_diagnosis = (
        ground_truth.get(
            "diagnosis_codes",
            []
        )
    )

    actual_diagnosis = (
        extracted.get(
            "diagnosis_codes",
            []
        )
    )


    claim_total += 1
    total_checks += 1


    if (
        expected_diagnosis
        == actual_diagnosis
    ):

        claim_correct += 1
        correct_checks += 1

        print(
            "PASS | diagnosis_codes"
        )

    else:

        print(
            "FAIL | diagnosis_codes"
        )

        print(
            f"      Expected: "
            f"{expected_diagnosis}"
        )

        print(
            f"      Actual  : "
            f"{actual_diagnosis}"
        )


    # ========================================================
    # SERVICE LINES
    # ========================================================

    expected_lines = (
        ground_truth.get(
            "service_lines",
            []
        )
    )

    actual_lines = (
        extracted.get(
            "service_lines",
            []
        )
    )


    # --------------------------------------------------------
    # Number of rows
    # --------------------------------------------------------

    claim_total += 1
    total_checks += 1


    if len(expected_lines) == len(actual_lines):

        claim_correct += 1
        correct_checks += 1

        print(
            "PASS | service_line_count"
        )

    else:

        print(
            "FAIL | service_line_count"
        )

        print(
            f"      Expected: "
            f"{len(expected_lines)}"
        )

        print(
            f"      Actual  : "
            f"{len(actual_lines)}"
        )


    # --------------------------------------------------------
    # Compare every service line
    # --------------------------------------------------------

    SERVICE_FIELDS = [
        "date_of_service",
        "place_of_service",
        "procedure_code",
        "diagnosis_pointer",
        "charges",
        "units",
        "provider_npi",
    ]


    for row_index, expected_line in enumerate(
        expected_lines
    ):

        if row_index >= len(actual_lines):

            for field in SERVICE_FIELDS:

                claim_total += 1
                total_checks += 1

                print(
                    f"FAIL | "
                    f"service_line_{row_index + 1}_{field}"
                )

            continue


        actual_line = actual_lines[row_index]


        for field in SERVICE_FIELDS:

            expected = expected_line.get(field)
            actual = actual_line.get(field)

            claim_total += 1
            total_checks += 1


            if same(expected, actual):

                claim_correct += 1
                correct_checks += 1

                print(
                    f"PASS | "
                    f"service_line_{row_index + 1}_"
                    f"{field}"
                )

            else:

                print(
                    f"FAIL | "
                    f"service_line_{row_index + 1}_"
                    f"{field}"
                )

                print(
                    f"      Expected: "
                    f"{expected}"
                )

                print(
                    f"      Actual  : "
                    f"{actual}"
                )


    # ========================================================
    # CLAIM ACCURACY
    # ========================================================

    claim_accuracy = (
        claim_correct
        / claim_total
        * 100
        if claim_total
        else 0
    )


    claim_scores.append(
        claim_accuracy
    )


    print(
        f"Claim accuracy: "
        f"{claim_accuracy:.2f}%"
    )


# ============================================================
# OVERALL ACCURACY
# ============================================================

overall_accuracy = (
    correct_checks
    / total_checks
    * 100
    if total_checks
    else 0
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("==========================================")
print("10-CLAIM EVALUATION")
print("==========================================")

print(
    f"Total checks : {total_checks}"
)

print(
    f"Correct      : {correct_checks}"
)

print(
    f"Wrong        : "
    f"{total_checks - correct_checks}"
)

print(
    f"Accuracy     : "
    f"{overall_accuracy:.2f}%"
)

print("==========================================")


# ============================================================
# SAVE REPORT
# ============================================================

report = {
    "claims_evaluated": 10,
    "total_checks": total_checks,
    "correct_checks": correct_checks,
    "wrong_checks": (
        total_checks - correct_checks
    ),
    "accuracy_percent": round(
        overall_accuracy,
        2
    ),
    "claim_accuracies": claim_scores,
}


with open(
    "data/dataset/evaluation_10.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        report,
        file,
        indent=4
    )


print(
    "Saved: "
    "data/dataset/evaluation_10.json"
)