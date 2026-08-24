from pypdfium2 import PdfDocument

pdf = PdfDocument("data/raw/Sample 1500_2012_02.pdf")

print("Number of pages:", len(pdf))