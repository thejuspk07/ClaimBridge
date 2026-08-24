import json
import os
from pathlib import Path

from paddleocr import PaddleOCR


# ============================================================
# 1. WHERE ARE THE CLAIM IMAGES?
# ============================================================

IMAGE_DIR = Path(
    "data/dataset/images"
)


# ============================================================
# 2. WHERE SHOULD OCR RESULTS BE SAVED?
# ============================================================

OUTPUT_DIR = Path(
    "data/dataset/ocr_10"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 3. CREATE OCR ENGINE
# ============================================================

# This is our "OCR worker".
#
# We create it ONCE.
# Then we give it 10 images one by one.
#
# We are deliberately using CPU because the current
# PaddleOCR GPU setup cannot run PP-OCRv6 on RTX 5050.

ocr = PaddleOCR(
    lang="en",
    device="cpu",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)


# ============================================================
# 4. TAKE ONLY FIRST 10 CLAIMS
# ============================================================

image_files = sorted(
    IMAGE_DIR.glob("claim_*.png")
)[:10]


print("==========================================")
print("10-CLAIM OCR TEST")
print("==========================================")
print(
    f"Claims selected: {len(image_files)}"
)
print()


# ============================================================
# 5. PROCESS CLAIMS ONE BY ONE
# ============================================================

successful = 0

for index, image_file in enumerate(
    image_files,
    start=1
):

    print(
        f"[{index}/{len(image_files)}] "
        f"{image_file.name}"
    )


    try:

        # ----------------------------------------------------
        # OCR READS THE IMAGE
        # ----------------------------------------------------

        result = ocr.predict(
            str(image_file)
        )


        # ----------------------------------------------------
        # CONVERT OCR RESULT TO NORMAL PYTHON DATA
        # ----------------------------------------------------

        ocr_output = []

        for page_number, page in enumerate(
            result,
            start=1
        ):

            texts = page["rec_texts"]
            scores = page["rec_scores"]
            boxes = page["rec_polys"]


            for text, score, box in zip(
                texts,
                scores,
                boxes
            ):

                # OCR box comes as a NumPy array.
                # Convert it to normal Python lists.
                points = box.tolist()


                xs = [
                    point[0]
                    for point in points
                ]

                ys = [
                    point[1]
                    for point in points
                ]


                # ------------------------------------------------
                # Save:
                # WHAT = text
                # HOW SURE = confidence
                # WHERE = bbox
                # ------------------------------------------------

                ocr_output.append(
                    {
                        "page": page_number,

                        "text": str(text),

                        "confidence": float(
                            score
                        ),

                        "polygon": points,

                        "bbox": {
                            "x1": float(
                                min(xs)
                            ),
                            "y1": float(
                                min(ys)
                            ),
                            "x2": float(
                                max(xs)
                            ),
                            "y2": float(
                                max(ys)
                            ),
                        },
                    }
                )


        # ----------------------------------------------------
        # SAVE THIS CLAIM'S OCR RESULT
        # ----------------------------------------------------

        output_file = (
            OUTPUT_DIR
            /
            image_file.name.replace(
                ".png",
                "_ocr.json"
            )
        )


        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                ocr_output,
                file,
                indent=4
            )


        successful += 1


        print(
            f"    Saved: {output_file}"
        )


    except Exception as error:

        print(
            f"    FAILED: {error}"
        )


# ============================================================
# 6. FINAL RESULT
# ============================================================

print()
print("==========================================")
print("10-CLAIM OCR COMPLETE")
print("==========================================")
print(
    f"Successful: "
    f"{successful}/{len(image_files)}"
)
print(
    f"Output: "
    f"{OUTPUT_DIR}"
)
print("==========================================")