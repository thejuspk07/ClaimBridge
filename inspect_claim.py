import json

# Open claim 001 OCR result.
with open(
    "data/dataset/ocr_10/claim_001_ocr.json",
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)


# These are the important values we want to locate.
wanted = {
    "INS7539906",
    "Nair, David J",
    "07",
    "31",
    "55",
    "E11.9",
    "M54.5",
    "F41.1",
    "I10",
    "99213",
    "291.30",
    "0268310679",
}


print("==========================================")
print("IMPORTANT OCR COORDINATES")
print("==========================================")


# Look through every OCR detection.
for item in data:

    text = item["text"].strip()

    # Is this one of the values we care about?
    if text in wanted:

        print()
        print("TEXT       :", text)
        print("CONFIDENCE :", item["confidence"])
        print("BOX        :", item["bbox"])


print()
print("==========================================")