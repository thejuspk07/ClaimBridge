from pathlib import Path
import pypdfium2 as pdfium


# ============================================================
# 1. FOLDERS
# ============================================================

PDF_DIR = Path("data/dataset/pdfs")
IMAGE_DIR = Path("data/dataset/images")

IMAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. FIND ALL PDFs
# ============================================================

pdf_files = sorted(
    PDF_DIR.glob("claim_*.pdf")
)

print("==========================================")
print("BATCH PDF -> PNG RENDERING (1368 x 1728)")
print("==========================================")
print(f"PDF files found: {len(pdf_files)}")
print()


# ============================================================
# 3. CONVERT PDF → PNG (scale=2 -> 1368 x 1728)
# ============================================================

successful = 0

for index, pdf_file in enumerate(pdf_files, start=1):

    output_png = (
        IMAGE_DIR /
        pdf_file.name.replace(".pdf", ".png")
    )

    try:
        pdf = pdfium.PdfDocument(str(pdf_file))
        page = pdf[0]
        image = page.render(scale=2).to_pil()
        image.save(str(output_png))
        successful += 1

        if index <= 10 or index % 10 == 0 or index == len(pdf_files):
            print(f"[{index}/{len(pdf_files)}] {pdf_file.name} -> {output_png.name} ({image.size[0]}x{image.size[1]})")

    except Exception as error:
        print(f"FAILED: {pdf_file.name}")
        print(f"Reason: {error}")


# ============================================================
# 4. SUMMARY
# ============================================================

print()
print("==========================================")
print("BATCH RENDER COMPLETE")
print("==========================================")
print(
    f"Successful: "
    f"{successful}/{len(pdf_files)}"
)
print(
    f"Image folder: "
    f"{IMAGE_DIR}"
)
print("==========================================")