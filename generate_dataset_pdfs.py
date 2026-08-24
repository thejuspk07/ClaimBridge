import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

GROUND_TRUTH_DIR = Path(
    "data/dataset/ground_truth"
)

WORKING_JSON = Path(
    "data/processed/claim_001.json"
)

WORKING_PDF = Path(
    "data/raw/claim_001.pdf"
)

OUTPUT_DIR = Path(
    "data/dataset/pdfs"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FIND ALL JSON CLAIMS
# ============================================================

claim_files = sorted(
    GROUND_TRUTH_DIR.glob("claim_*.json")
)

print("==========================================")
print("BATCH PDF GENERATION")
print("==========================================")
print(
    f"JSON claims found: {len(claim_files)}"
)
print()


# ============================================================
# GENERATE PDF FOR EACH JSON
# ============================================================

successful = 0

for index, json_file in enumerate(
    claim_files,
    start=1
):

    print(
        f"[{index}/{len(claim_files)}] "
        f"Generating {json_file.name}"
    )

    try:

        # ----------------------------------------------------
        # Put this claim where the existing generator expects it
        # ----------------------------------------------------

        shutil.copyfile(
            json_file,
            WORKING_JSON
        )

        # ----------------------------------------------------
        # Run the EXISTING calibrated PDF generator
        # ----------------------------------------------------

        subprocess.run(
            [
                sys.executable,
                "generate_claim.py"
            ],
            check=True
        )

        # ----------------------------------------------------
        # Copy generated PDF to dataset folder
        # ----------------------------------------------------

        output_pdf = (
            OUTPUT_DIR
            / json_file.name.replace(
                ".json",
                ".pdf"
            )
        )

        shutil.copyfile(
            WORKING_PDF,
            output_pdf
        )

        successful += 1

    except Exception as error:

        print(
            f"FAILED: {json_file.name}"
        )

        print(
            f"Reason: {error}"
        )

        break


# ============================================================
# SUMMARY
# ============================================================

print()
print("==========================================")
print("BATCH PDF GENERATION COMPLETE")
print("==========================================")

print(
    f"Successful: "
    f"{successful}/{len(claim_files)}"
)

print(
    f"PDF location: "
    f"{OUTPUT_DIR}"
)

print("==========================================")