import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
from paddleocr import PaddleOCR


# ============================================================
# INPUT IMAGE
# ============================================================

IMAGE_PATH = Path(
    "data/dataset/images/claim_001.png"
)


# ============================================================
# OUTPUT
# ============================================================

CROP_PATH = Path(
    "data/dataset/diagnosis_crop.png"
)


# ============================================================
# LOAD IMAGE
# ============================================================

image = Image.open(
    IMAGE_PATH
)


print(
    "Original image size:",
    image.size
)


# ============================================================
# CROP ITEM 21
#
# We know the diagnosis codes are around y = 1010.
#
# Give OCR a little extra space around the cells.
# ============================================================

crop = image.crop(
    (
        90,      # left
        975,     # top
        800,     # right
        1060     # bottom
    )
)


# ============================================================
# UPSCALE
#
# Small text becomes easier for OCR to see.
# ============================================================

crop = crop.resize(
    (
        crop.width * 3,
        crop.height * 3
    )
)


# ============================================================
# ENHANCE CONTRAST
# ============================================================

crop = ImageEnhance.Contrast(
    crop
).enhance(1.8)


# ============================================================
# SHARPEN
# ============================================================

crop = crop.filter(
    ImageFilter.SHARPEN
)


# ============================================================
# SAVE CROP
# ============================================================

crop.save(
    CROP_PATH
)


print(
    "Saved diagnosis crop:",
    CROP_PATH
)


# ============================================================
# OCR
# ============================================================

ocr = PaddleOCR(
    lang="en",
    device="cpu",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)


result = ocr.predict(
    str(CROP_PATH)
)


# ============================================================
# PRINT OCR RESULTS
# ============================================================

print()
print(
    "=========================================="
)

print(
    "DIAGNOSIS OCR TEST"
)

print(
    "=========================================="
)


for page in result:

    texts = page["rec_texts"]
    scores = page["rec_scores"]

    for text, score in zip(
        texts,
        scores
    ):

        print(
            f"TEXT: {text} | "
            f"CONFIDENCE: {score:.3f}"
        )


print(
    "=========================================="
)