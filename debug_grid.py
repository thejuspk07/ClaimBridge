from pathlib import Path
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent; TEMPLATE = ROOT / "data/raw/Sample 1500_2012_02.pdf"; OUTPUT = ROOT / "data/raw/template_grid.pdf"
PAGE_WIDTH, PAGE_HEIGHT = 684, 864
c = canvas.Canvas(str(ROOT / "data/raw/grid_overlay.pdf"), pagesize=(PAGE_WIDTH, PAGE_HEIGHT)); c.setFont("Helvetica", 5); c.setFillColorRGB(0, .4, .8)
for x in range(0, PAGE_WIDTH + 1, 20): c.line(x, 0, x, PAGE_HEIGHT); c.drawString(x + 1, 3, str(x))
for y in range(0, PAGE_HEIGHT + 1, 20): c.line(0, y, PAGE_WIDTH, y); c.drawString(2, y + 1, str(y))
c.save(); source = PdfReader(str(TEMPLATE)); overlay = PdfReader(str(ROOT / "data/raw/grid_overlay.pdf")); source.pages[0].merge_page(overlay.pages[0]); writer = PdfWriter(); writer.add_page(source.pages[0]);
with OUTPUT.open("wb") as stream: writer.write(stream)
print(f"Created {OUTPUT}")
