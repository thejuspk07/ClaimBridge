import json
import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================
# WHERE ARE OUR 10 OCR RESULTS?
# ============================================================

OCR_DIR = Path(
    "data/dataset/ocr_10"
)


# ============================================================
# WHERE DOES OUR EXISTING EXTRACTOR EXPECT OCR JSON?
# ============================================================

WORKING_OCR = Path(
    "data/processed/ocr_output.json"
)


# ============================================================
# WHERE DOES OUR EXISTING EXTRACTOR SAVE ITS RESULT?
# ============================================================

WORKING_EXTRACTED = Path(
    "data/processed/extracted_claim.json"
)


# ============================================================
# WHERE SHOULD WE SAVE THE 10 FINAL RESULTS?
# ============================================================

OUTPUT_DIR = Path(
    "data/dataset/extracted_10"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FIND THE 10 OCR FILES
# ============================================================

ocr_files = sorted(
    OCR_DIR.glob("claim_*_ocr.json")
)

print("==========================================")
print("10-CLAIM FIELD EXTRACTION")
print("==========================================")
print(
    f"OCR files found: {len(ocr_files)}"
)
print()


# ============================================================
# PROCESS EACH OCR FILE
# ============================================================

successful = 0


for index, ocr_file in enumerate(
    ocr_files,
    start=1
):

    print(
        f"[{index}/{len(ocr_files)}] "
        f"{ocr_file.name}"
    )


    # --------------------------------------------------------
    # STEP 1
    #
    # Our existing extract_fields.py expects:
    #
    # data/processed/ocr_output.json
    #
    # So temporarily put this claim there.
    # --------------------------------------------------------

    shutil.copyfile(
        ocr_file,
        WORKING_OCR
    )


    # --------------------------------------------------------
    # STEP 2
    #
    # Run our already-tested field extractor.
    # --------------------------------------------------------

    subprocess.run(
        [
            sys.executable,
            "extract_fields.py"
        ],
        check=True
    )


    # --------------------------------------------------------
    # STEP 3
    #
    # Convert:
    #
    # claim_001_ocr.json
    #
    # into:
    #
    # claim_001_extracted.json
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        /
        ocr_file.name.replace(
            "_ocr.json",
            "_extracted.json"
        )
    )


    # --------------------------------------------------------
    # STEP 4
    #
    # Save the extracted claim.
    # --------------------------------------------------------

    shutil.copyfile(
        WORKING_EXTRACTED,
        output_file
    )


    successful += 1


# ============================================================
# SUMMARY
# ============================================================

print()
print("==========================================")
print("FIELD EXTRACTION COMPLETE")
print("==========================================")
print(
    f"Successful: "
    f"{successful}/{len(ocr_files)}"
)
print(
    f"Output: "
    f"{OUTPUT_DIR}"
)
print("==========================================")