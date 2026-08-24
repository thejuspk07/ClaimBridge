from pypdfium2 import PdfDocument

pdf = PdfDocument("data/raw/Sample 1500_2012_02.pdf")

for page_number, page in enumerate(pdf):
    image = page.render(scale=2).to_pil()
    image.save(f"data/raw/page_{page_number + 1}.png")

print("Finished converting PDF pages to images.")