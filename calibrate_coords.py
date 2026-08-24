"""
CMS-1500 Coordinate Calibration Tool.

Renders the blank template with a point-grid overlay and extracts
all text elements (labels, borders) so we can determine exact field
boundaries for each CMS-1500 item.
"""

import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from pypdf import PdfReader, PdfWriter
from pypdfium2 import PdfDocument
import pdfplumber

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "data" / "raw" / "Sample 1500_2012_02.pdf"
GRID_OVERLAY = ROOT / "data" / "raw" / "calibration_grid.pdf"
GRID_OUTPUT = ROOT / "data" / "raw" / "calibration_grid_merged.pdf"
GRID_PNG = ROOT / "data" / "raw" / "calibration_grid.png"

PAGE_W = 684
PAGE_H = 864

def create_grid_overlay():
    """Create a grid overlay with tick marks every 10pt and labels every 50pt."""
    c = canvas.Canvas(str(GRID_OVERLAY), pagesize=(PAGE_W, PAGE_H))
    
    # Light grid every 10pt
    c.setStrokeColor(Color(0, 0.5, 1, alpha=0.15))
    c.setLineWidth(0.25)
    for x in range(0, PAGE_W + 1, 10):
        c.line(x, 0, x, PAGE_H)
    for y in range(0, PAGE_H + 1, 10):
        c.line(0, y, PAGE_W, y)
    
    # Darker grid every 50pt
    c.setStrokeColor(Color(1, 0, 0, alpha=0.3))
    c.setLineWidth(0.5)
    for x in range(0, PAGE_W + 1, 50):
        c.line(x, 0, x, PAGE_H)
    for y in range(0, PAGE_H + 1, 50):
        c.line(0, y, PAGE_W, y)
    
    # Labels every 50pt
    c.setFont("Helvetica", 5)
    c.setFillColor(Color(1, 0, 0, alpha=0.6))
    for x in range(0, PAGE_W + 1, 50):
        c.drawString(x + 1, 2, str(x))
        c.drawString(x + 1, PAGE_H - 8, str(x))
    for y in range(0, PAGE_H + 1, 50):
        c.drawString(2, y + 1, str(y))
        c.drawString(PAGE_W - 20, y + 1, str(y))
    
    c.save()

def merge_grid():
    """Merge grid overlay onto template."""
    template = PdfReader(str(TEMPLATE))
    grid = PdfReader(str(GRID_OVERLAY))
    page = template.pages[0]
    page.merge_page(grid.pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    with open(GRID_OUTPUT, "wb") as f:
        writer.write(f)

def render_png():
    """Render merged grid PDF to PNG at 2x scale."""
    doc = PdfDocument(str(GRID_OUTPUT))
    img = doc[0].render(scale=2).to_pil()
    img.save(str(GRID_PNG))
    print(f"Grid PNG saved: {GRID_PNG}")

def extract_template_elements():
    """Use pdfplumber to extract all text elements, lines, and rects from template."""
    elements = {"words": [], "lines": [], "rects": [], "chars": []}
    
    with pdfplumber.open(str(TEMPLATE)) as pdf:
        page = pdf.pages[0]
        
        # Extract words with bounding boxes
        words = page.extract_words(keep_blank_chars=True, x_tolerance=2, y_tolerance=2)
        for w in words:
            elements["words"].append({
                "text": w["text"],
                "x0": round(w["x0"], 1),
                "top": round(w["top"], 1),
                "x1": round(w["x1"], 1),
                "bottom": round(w["bottom"], 1),
                # Convert pdfplumber top-origin to ReportLab bottom-origin
                "rl_x": round(w["x0"], 1),
                "rl_y": round(PAGE_H - w["bottom"], 1),
            })
        
        # Extract lines (borders)
        if page.lines:
            for line in page.lines:
                elements["lines"].append({
                    "x0": round(line["x0"], 1),
                    "top": round(line["top"], 1),
                    "x1": round(line["x1"], 1),
                    "bottom": round(line["bottom"], 1),
                    "rl_y0": round(PAGE_H - line["bottom"], 1),
                    "rl_y1": round(PAGE_H - line["top"], 1),
                })
        
        # Extract rectangles
        if page.rects:
            for rect in page.rects:
                elements["rects"].append({
                    "x0": round(rect["x0"], 1),
                    "top": round(rect["top"], 1),
                    "x1": round(rect["x1"], 1),
                    "bottom": round(rect["bottom"], 1),
                    "rl_x0": round(rect["x0"], 1),
                    "rl_y0": round(PAGE_H - rect["bottom"], 1),
                    "rl_x1": round(rect["x1"], 1),
                    "rl_y1": round(PAGE_H - rect["top"], 1),
                })
    
    return elements

def main():
    print("=" * 60)
    print("CMS-1500 COORDINATE CALIBRATION")
    print("=" * 60)
    
    # Step 1: Create grid overlay
    create_grid_overlay()
    print("Grid overlay created")
    
    # Step 2: Merge onto template
    merge_grid()
    print("Grid merged with template")
    
    # Step 3: Render PNG
    render_png()
    
    # Step 4: Extract template elements
    print("\nExtracting template elements with pdfplumber...")
    elements = extract_template_elements()
    
    # Save elements for analysis
    output = ROOT / "data" / "raw" / "template_elements.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(elements, f, indent=2)
    print(f"Template elements saved: {output}")
    print(f"  Words: {len(elements['words'])}")
    print(f"  Lines: {len(elements['lines'])}")
    print(f"  Rects: {len(elements['rects'])}")
    
    # Print key labels and their positions for calibration
    print("\n" + "=" * 60)
    print("KEY TEMPLATE LABELS (sorted by Y descending = top to bottom)")
    print("=" * 60)
    
    # Sort by rl_y descending (top of form first)
    sorted_words = sorted(elements["words"], key=lambda w: -w["rl_y"])
    
    for w in sorted_words:
        text = w["text"].strip()
        if len(text) > 2:  # Skip single chars
            print(f"  rl_x={w['rl_x']:>6.1f}  rl_y={w['rl_y']:>6.1f}  "
                  f"x0={w['x0']:>6.1f}  x1={w['x1']:>6.1f}  "
                  f"top={w['top']:>6.1f}  bot={w['bottom']:>6.1f}  "
                  f"| {text}")


if __name__ == "__main__":
    main()
