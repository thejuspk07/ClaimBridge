import json
import os

# Disable the PIR execution path that caused
# the oneDNN conversion error on this setup.
os.environ["FLAGS_enable_pir_api"] = "0"

from paddleocr import PaddleOCR


# ============================================================
# 1. CREATE OCR ENGINE
# ============================================================

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)


# ============================================================
# 2. INPUT IMAGE
# ============================================================

IMAGE_PATH = "data/raw/claim_001.png"


# ============================================================
# 3. RUN OCR
# ============================================================

result = ocr.predict(IMAGE_PATH)


# ============================================================
# 4. CONVERT OCR RESULT INTO CLEAN JSON
# ============================================================

ocr_output = []

for page_number, page in enumerate(result, start=1):

    texts = page["rec_texts"]
    scores = page["rec_scores"]
    boxes = page["rec_polys"]

    for text, score, box in zip(texts, scores, boxes):

        points = box.tolist()

        xs = [point[0] for point in points]
        ys = [point[1] for point in points]

        x1 = min(xs)
        y1 = min(ys)
        x2 = max(xs)
        y2 = max(ys)

        ocr_output.append(
            {
                "page": page_number,
                "text": str(text),
                "confidence": float(score),
                "polygon": points,
                "bbox": {
                    "x1": float(x1),
                    "y1": float(y1),
                    "x2": float(x2),
                    "y2": float(y2),
                },
            }
        )


# ============================================================
# 5. SAVE OCR OUTPUT
# ============================================================

OUTPUT_PATH = "data/processed/ocr_output.json"

os.makedirs(
    "data/processed",
    exist_ok=True,
)

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        ocr_output,
        file,
        indent=4,
    )


# ============================================================
# 6. SUMMARY
# ============================================================

print()
print("==========================================")
print("OCR COMPLETE")
print("==========================================")
print(f"Input image          : {IMAGE_PATH}")
print(f"Detected text regions: {len(ocr_output)}")
print(f"Saved OCR JSON       : {OUTPUT_PATH}")
print("==========================================")