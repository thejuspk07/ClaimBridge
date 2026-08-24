import json
import os
from pathlib import Path

from paddleocr import PaddleOCR


# ============================================================
# 1. FOLDERS
# ============================================================

IMAGE_DIR = Path(
    "data/dataset/images"
)

OUTPUT_DIR = Path(
    "data/dataset/ocr"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. CREATE OCR ENGINE ONCE
# ============================================================

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)


# ============================================================
# 3. FIND ALL CLAIM IMAGES
# ============================================================

image_files = sorted(
    IMAGE_DIR.glob("claim_*.png")
)

print("==========================================")
print("BATCH OCR")
print("==========================================")
print(
    f"Images found: {len(image_files)}"
)
print()


# ============================================================
# 4. PROCESS EVERY IMAGE
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
        # Run PaddleOCR
        # ----------------------------------------------------

        result = ocr.predict(
            str(image_file)
        )


        # ----------------------------------------------------
        # Convert OCR result into normal JSON
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

                points = box.tolist()

                xs = [
                    point[0]
                    for point in points
                ]

                ys = [
                    point[1]
                    for point in points
                ]

                ocr_output.append(
                    {
                        "page": page_number,
                        "text": str(text),
                        "confidence": float(score),
                        "polygon": points,
                        "bbox": {
                            "x1": float(min(xs)),
                            "y1": float(min(ys)),
                            "x2": float(max(xs)),
                            "y2": float(max(ys)),
                        },
                    }
                )


        # ----------------------------------------------------
        # Save OCR JSON
        #
        # claim_037.png
        #       ↓
        # claim_037_ocr.json
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


    except Exception as error:

        print(
            f"FAILED: {image_file.name}"
        )

        print(
            f"Reason: {error}"
        )


# ============================================================
# 5. SUMMARY
# ============================================================

print()
print("==========================================")
print("BATCH OCR COMPLETE")
print("==========================================")
print(
    f"Successful: "
    f"{successful}/{len(image_files)}"
)
print(
    f"OCR folder: "
    f"{OUTPUT_DIR}"
)
print("==========================================")