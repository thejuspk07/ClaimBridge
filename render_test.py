from pypdfium2 import PdfDocument

# Open our generated synthetic claim PDF
pdf = PdfDocument("data/raw/claim_001.pdf")

# Get page 1
page = pdf[0]

# Convert the PDF page into an image
image = page.render(scale=2).to_pil()

# Save the image that ClaimBridge will read
image.save("data/raw/claim_001.png")

print("Created claim_001.png")