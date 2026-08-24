import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

NUMBER_OF_CLAIMS = 100

SOURCE_JSON = Path(
    "data/processed/claim_001.json"
)

OUTPUT_DIR = Path(
    "data/dataset/ground_truth"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# GENERATE CLAIMS
# ============================================================

successful = 0


for claim_number in range(
    1,
    NUMBER_OF_CLAIMS + 1
):

    seed = claim_number

    print(
        f"Generating claim "
        f"{claim_number}/{NUMBER_OF_CLAIMS}..."
    )

    env = os.environ.copy()

    env["CLAIM_SEED"] = str(seed)

    try:

        subprocess.run(
            [
                sys.executable,
                "create_synthetic_data.py"
            ],
            env=env,
            check=True,
        )

        # ----------------------------------------
        # Read generated JSON
        # ----------------------------------------

        with open(
            SOURCE_JSON,
            "r",
            encoding="utf-8"
        ) as file:

            claim = json.load(file)


        # ----------------------------------------
        # Add claim ID
        # ----------------------------------------

        claim["claim_id"] = (
            f"CLM{claim_number:04d}"
        )


        # ----------------------------------------
        # Save separate ground-truth JSON
        # ----------------------------------------

        output_file = (
            OUTPUT_DIR
            / f"claim_{claim_number:03d}.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                claim,
                file,
                indent=4
            )


        successful += 1


    except subprocess.CalledProcessError:

        print(
            f"❌ FAILED: claim "
            f"{claim_number}"
        )

        break


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("==========================================")
print("DATASET GENERATION COMPLETE")
print("==========================================")

print(
    f"Successful claims: "
    f"{successful}/{NUMBER_OF_CLAIMS}"
)

print(
    f"Location: "
    f"{OUTPUT_DIR}"
)

print("==========================================")