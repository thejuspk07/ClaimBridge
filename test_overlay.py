from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

# 1. Create a new PDF containing the patient name
overlay = canvas.Canvas("data/raw/overlay.pdf", pagesize=(684, 864))
overlay.setFont("Helvetica", 9)
overlay.setFillColorRGB(0, 0, 0)
overlay.drawString(64, 691, "Michael Thomas")  # Box 2: PATIENT'S NAME
overlay.save()

# 2. Open our original CMS-1500 PDF
original = PdfReader("data/raw/Sample 1500_2012_02.pdf")

# 3. Open the PDF containing the name
overlay_pdf = PdfReader("data/raw/overlay.pdf")

# 4. Put the name layer on top of page 1
page = original.pages[0]
page.merge_page(overlay_pdf.pages[0])

# 5. Save the result
writer = PdfWriter()
writer.add_page(page)
with open("data/raw/test_claim.pdf", "wb") as output:
    writer.write(output)

print("Created test_claim.pdf")