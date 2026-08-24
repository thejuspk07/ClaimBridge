"""
Extract checkbox rectangles from the CMS-1500 template.
Checkboxes are small rectangles (typically 8-12pt square).
"""
import json
import pdfplumber

PAGE_H = 864

with pdfplumber.open("data/raw/Sample 1500_2012_02.pdf") as pdf:
    page = pdf.pages[0]
    
    # Get all rectangles
    rects = page.rects or []
    lines = page.lines or []
    
    print(f"Total rects: {len(rects)}")
    print(f"Total lines: {len(lines)}")
    
    # Find small rectangles that could be checkboxes
    # Checkboxes are typically 8-12pt wide and tall
    print("\n=== RECTANGLES (potential checkboxes) ===")
    for r in rects:
        w = r["x1"] - r["x0"]
        h = r["bottom"] - r["top"]
        rl_y_bot = PAGE_H - r["bottom"]
        rl_y_top = PAGE_H - r["top"]
        print(f"  x0={r['x0']:>7.1f}  x1={r['x1']:>7.1f}  "
              f"top={r['top']:>7.1f}  bot={r['bottom']:>7.1f}  "
              f"w={w:>5.1f}  h={h:>5.1f}  "
              f"rl_y_bot={rl_y_bot:>7.1f}  rl_y_top={rl_y_top:>7.1f}")
    
    # Now find checkbox-like structures from lines
    # A checkbox is formed by 4 lines making a small square
    # Let's find all short horizontal lines (width 6-15pt) 
    # that could be top/bottom of checkboxes
    print("\n=== SHORT HORIZONTAL LINES (6-15pt span, potential checkbox borders) ===")
    short_h = [l for l in lines 
               if abs(l["top"] - l["bottom"]) < 1.5 
               and 5 <= (l["x1"] - l["x0"]) <= 16]
    short_h.sort(key=lambda l: (PAGE_H - l["bottom"]), reverse=True)
    for l in short_h:
        rl_y = PAGE_H - l["bottom"]
        span = l["x1"] - l["x0"]
        print(f"  x0={l['x0']:>7.1f}  x1={l['x1']:>7.1f}  rl_y={rl_y:>7.1f}  span={span:>5.1f}")
    
    # Short vertical lines (height 6-15pt) for checkbox sides
    print("\n=== SHORT VERTICAL LINES (6-15pt span, potential checkbox sides) ===")
    short_v = [l for l in lines 
               if abs(l["x0"] - l["x1"]) < 1.5 
               and 5 <= abs(l["bottom"] - l["top"]) <= 16]
    short_v.sort(key=lambda l: (l["x0"], -(PAGE_H - l["bottom"])))
    for l in short_v:
        rl_y_bot = PAGE_H - l["bottom"]
        rl_y_top = PAGE_H - l["top"]
        h = abs(l["bottom"] - l["top"])
        print(f"  x={l['x0']:>7.1f}  rl_y_bot={rl_y_bot:>7.1f}  rl_y_top={rl_y_top:>7.1f}  height={h:>5.1f}")
