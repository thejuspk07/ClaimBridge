from pypdfium2 import PdfDocument

pdf = PdfDocument("data/raw/Sample 1500_2012_02.pdf")

page = pdf[0]

width, height = page.get_size()

print("Page width:", width)
print("Page height:", height)