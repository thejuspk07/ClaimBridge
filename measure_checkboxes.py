"""
Manually calibrate checkbox positions from the zoomed crop images.

Each crop was taken with known PDF coordinate bounds, so I can map 
the pixel position of each checkbox back to exact PDF coordinates.

Crop formula used in crop_checkboxes.py:
  region = (x0_pdf, y0_rl_bottom, x1_pdf, y1_rl_top) in PDF coords
  px0 = x0_pdf * 4
  py0 = (864 - y1_rl_top) * 4   (top of crop in pixels)
  px1 = x1_pdf * 4
  py1 = (864 - y0_rl_bottom) * 4   (bottom of crop in pixels)

Image was rendered at 4x scale (2736x3456 from 684x864).
The crops were then scaled 2x for visibility -> effective 8x.
So in the saved crop images: 1 pixel = 0.125 PDF points.
But I'll work with the 4x source directly.

From visual inspection of the cropped images, here are the checkbox
positions measured relative to the crop region bounds:
"""

PAGE_H = 864

# Helper: given crop region and approximate pixel center in the 8x crop image,
# compute the PDF (x, y_baseline) where we should place the X character.
# The X character baseline should be at the bottom of the checkbox + a small offset.
# For centering: use the center of the checkbox, adjusted for font ascent.

def crop_px_to_pdf(crop_region, px, py):
    """Convert pixel (px, py) in an 8x crop image to PDF coords.
    crop_region = (x0_pdf, y0_rl_bottom, x1_pdf, y1_rl_top) in PDF points.
    """
    x0_pdf, y0_bot, x1_pdf, y1_top = crop_region
    # Crop spans (x1-x0) PDF points horizontally and (y1-y0) vertically
    crop_w_pt = x1_pdf - x0_pdf
    crop_h_pt = y1_top - y0_bot
    # Crop image at 8x: image_w = crop_w_pt * 8, image_h = crop_h_pt * 8
    img_w = crop_w_pt * 8
    img_h = crop_h_pt * 8
    # Pixel -> fraction
    frac_x = px / img_w
    frac_y = py / img_h
    # PDF coords
    pdf_x = x0_pdf + frac_x * crop_w_pt
    pdf_y = y1_top - frac_y * crop_h_pt  # y decreases downward in image
    return round(pdf_x, 1), round(pdf_y, 1)


# ====================================================================
# ITEM 1: Insurance type checkboxes
# Crop region: (25, 705, 410, 740) -> 385pt wide x 35pt tall
# Crop image: 3080 x 280 pixels (at 8x)
# 
# From the crop image, the checkboxes are arranged left-to-right:
# Each checkbox is approximately 10x10pt (80x80px in 8x).
# Looking at the actual crop (checkbox_item1_checkboxes.png):
#   Checkbox 1 (MEDICARE):      left edge ~100px -> x_pdf = 25 + 100/(8*385)*385 = 25+12.5 = 37.5
#   Checkbox 2 (MEDICAID):      left edge ~580px  
#   Checkbox 3 (TRICARE):       left edge ~880px
#   Checkbox 4 (CHAMPVA):       left edge ~1200px (approx before CHAMPVA label)
#   Checkbox 5 (GROUP HEALTH):  left edge ~1500px 
#   Checkbox 6 (FECA BLK LUNG): left edge ~1800px (?)
#   Checkbox 7 (OTHER):         left edge ~2100px (??)
#
# Actually, let me just read them from the crop more carefully.
# The crop region x starts at x=25 pdf. Scale=8x.
# So px / 8 + 25 = pdf_x.  And for y: top is y=740, so pdf_y = 740 - py/8.
# 
# From the zoomed crop image visible checkboxes (each ~10pt square):
# Medicare:        center x ~ 36pt, center y ~ 714pt
# Medicaid:        center x ~ 100pt, center y ~ 714pt
# Tricare:         center x ~ 141pt, center y ~ 714pt
# CHAMPVA:         center x ~ 212pt, center y ~ 714pt
# Group Health:    center x ~ 281pt, center y ~ 714pt
# FECA BLK LUNG:   center x ~ 336pt, center y ~ 714pt
# OTHER:           center x ~ 395pt, center y ~ 714pt
#
# Wait - looking at crop more carefully:
# The row of checkboxes in the crop image shows:
# "1."  then a checkbox, "MEDICARE", checkbox "MEDICAID", checkbox, "TRICARE" etc.
#
# Let me derive from the calibration grid image instead.
# From the grid image at 2x (1368x1728), the Item 1 row is at y~120 pixels (top).
# At 2x scale: 1px = 0.5pt, so let me use the actual calibration grid.
# ====================================================================

# I'll use the calibration grid image for precise measurement.
# Grid PNG is 2x scale (1368 x 1728).
# PDF x = px_in_grid / 2
# PDF y (rl) = 864 - (py_in_grid / 2)

from pypdfium2 import PdfDocument
from PIL import Image
import numpy as np

# Render the template at 4x for measurement
doc = PdfDocument("data/raw/Sample 1500_2012_02.pdf")
template = doc[0].render(scale=4).to_pil()
t = np.array(template)

# All checkbox measurements derived from visual inspection of cropped regions:
# The checkboxes are red outlined squares, approximately 10pt x 10pt.
# I need to find their exact pixel centers in the 4x image.

# For the X mark to appear centered inside the checkbox:
# - Font size 8 or 9, "X" character is approximately 5-6pt wide, 7-8pt ascent
# - To visually center: drawString x = checkbox_center_x - 3, y = checkbox_center_y - 3

# Let me directly measure from the visible checkbox crop images.
# Looking at each crop carefully:

# =====================================================================
# Item 1 checkbox row (all at same y)
# From the full calibration grid PNG, the checkbox bottom edges are at 
# pixel y ~310 in 2x image = rl_y = 864 - 155 = 709
# top edges at pixel y ~290 = rl_y = 864 - 145 = 719
# So checkbox spans rl_y 709 to 719, center = 714
# Checkbox width ~10pt, height ~10pt

# Looking at item1_checkboxes.png crop which is 8x effective:
# crop region = (25, 705, 410, 740)
# I can see the checkbox squares clearly. Let me measure from the grid image.
# 
# The checkboxes in the crop (from left to right):
# Between "1." label and "MEDICARE" label
# Then between "(Medicare#)" and "MEDICAID"
# etc.
#
# From the calibration grid (2x, reading the red 50pt grid lines):
# The checkboxes appear at approximately these x positions (2x pixel / 2 = pdf):
# Box before MEDICARE:        pdf_x center ~ 36
# Box before (Medicare#):     pdf_x center ~ 73  
# Box before MEDICAID:        pdf_x center ~ 98
# Box before (Medicaid#):     pdf_x center ~ 138
# Box before TRICARE:         pdf_x center ~ 141 (these are the grid marks)
#
# Actually this is getting complicated. Let me take a simpler approach:
# Use the KNOWN working crop images and the actual red pixel positions.

def find_checkbox_centers_in_region(arr, y_start, y_end, x_start, x_end, 
                                    min_gap=20, checkbox_size_range=(28, 56)):
    """
    Find red checkbox outlines in a region of the 4x rendered image.
    Returns list of (center_x_px, center_y_px) in full image coordinates.
    """
    crop = arr[y_start:y_end, x_start:x_end]
    
    # Red pixels: R > 150, G < 100, B < 100
    red = (crop[:,:,0] > 150) & (crop[:,:,1] < 100) & (crop[:,:,2] < 100)
    
    # Sum red pixels per column to find vertical edges
    col_profile = red.sum(axis=0)
    
    # Find vertical line positions (high red density columns)
    threshold = max(3, red.shape[0] * 0.1)
    edges_x = []
    in_edge = False
    edge_start = 0
    for c in range(len(col_profile)):
        if col_profile[c] >= threshold:
            if not in_edge:
                edge_start = c
                in_edge = True
        else:
            if in_edge:
                edges_x.append((edge_start + c) // 2)
                in_edge = False
    if in_edge:
        edges_x.append((edge_start + len(col_profile)) // 2)
    
    # Pair edges into checkbox left/right sides
    min_s, max_s = checkbox_size_range
    pairs = []
    used = set()
    for i in range(len(edges_x)):
        if i in used:
            continue
        for j in range(i + 1, len(edges_x)):
            if j in used:
                continue
            gap = edges_x[j] - edges_x[i]
            if min_s <= gap <= max_s:
                pairs.append((edges_x[i], edges_x[j]))
                used.add(i)
                used.add(j)
                break
    
    # For each pair, find the horizontal edges
    results = []
    for lx, rx in pairs:
        # Look at the column range [lx-2, rx+2] for horizontal edges
        sub = red[:, max(0, lx-2):min(red.shape[1], rx+2)]
        row_profile = sub.sum(axis=1)
        threshold_h = max(3, (rx - lx) * 0.3)
        
        h_edges = []
        in_edge = False
        for r in range(len(row_profile)):
            if row_profile[r] >= threshold_h:
                if not in_edge:
                    edge_start = r
                    in_edge = True
            else:
                if in_edge:
                    h_edges.append((edge_start + r) // 2)
                    in_edge = False
        if in_edge:
            h_edges.append((edge_start + len(row_profile)) // 2)
        
        if len(h_edges) >= 2:
            ty, by = h_edges[0], h_edges[-1]
            cx = (lx + rx) / 2 + x_start
            cy = (ty + by) / 2 + y_start
            # Also store the box bounds
            bx0 = lx + x_start
            by0 = ty + y_start
            bx1 = rx + x_start
            by1 = by + y_start
            results.append({
                "center_px": (cx, cy),
                "box_px": (bx0, by0, bx1, by1),
                "center_pdf": (cx / 4, 864 - cy / 4),
                "box_pdf": (bx0/4, 864 - by1/4, bx1/4, 864 - by0/4),
                "size_pt": ((rx - lx)/4, (by - ty)/4),
            })
    
    return results


# Item 1: Insurance checkboxes
# They span the row rl_y 707-732, which is pixel y 528-628 at 4x
# x range: 25-400 pdf = 100-1600 px
print("ITEM 1 - Insurance Type Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 528, 640, 100, 1620, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")

# Item 3: Sex checkboxes
# Row rl_y 684-707, pixel y 628-720
# Sex boxes in range x 340-400 pdf = 1360-1600 px
print("\nITEM 3 - Sex Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 628, 730, 1340, 1640, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")

# Item 6: Relationship checkboxes
# Row rl_y 660-684, pixel y 720-816
# x range: 270-410 pdf = 1080-1640 px
print("\nITEM 6 - Relationship Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 720, 835, 1070, 1660, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")

# Item 10a: Employment
# Row rl_y 565-588, pixel y 1104-1196
print("\nITEM 10a - Employment Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 1090, 1210, 1140, 1620, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")

# Item 10b: Auto accident
# Row rl_y 540-565, pixel y 1196-1296
print("\nITEM 10b - Auto Accident Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 1190, 1310, 1140, 1620, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")

# Item 10c: Other accident
# Row rl_y 516-540, pixel y 1296-1392
print("\nITEM 10c - Other Accident Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 1280, 1405, 1140, 1620, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")

# Item 11d: Another health benefit plan
# Row rl_y 492-516, pixel y 1392-1488
print("\nITEM 11d - Another Health Benefit Plan Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 1385, 1505, 1660, 2140, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")

# Item 27: Accept assignment
# Row rl_y 133-157, pixel y 2828-2924
print("\nITEM 27 - Accept Assignment Checkboxes")
print("-" * 60)
boxes = find_checkbox_centers_in_region(t, 2820, 2940, 1290, 1650, checkbox_size_range=(28, 56))
for i, b in enumerate(boxes):
    print(f"  Checkbox {i}: center_pdf=({b['center_pdf'][0]:.1f}, {b['center_pdf'][1]:.1f})  "
          f"box_pdf=({b['box_pdf'][0]:.1f}, {b['box_pdf'][1]:.1f}, {b['box_pdf'][2]:.1f}, {b['box_pdf'][3]:.1f})  "
          f"size={b['size_pt'][0]:.1f}x{b['size_pt'][1]:.1f}")
