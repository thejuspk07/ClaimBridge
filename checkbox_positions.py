"""
Directly measure checkbox positions from the calibration grid image.

Using the calibration grid PNG (2x scale, 1368 x 1728):
- PDF x = pixel_x / 2  
- PDF y (rl) = 864 - pixel_y / 2

From careful visual inspection of each checkbox crop image and the grid,
here are the measured checkbox rectangle boundaries in PDF points.
"""

# =====================================================================
# CHECKBOX MEASUREMENTS (PDF coordinates, rl bottom-left origin)
#
# Each checkbox is approximately 10pt x 10pt on the CMS-1500 form.
# The form uses red outlined squares for checkbox boxes.
#
# Methodology: For each checkbox group, I examined:
# 1. The 8x zoomed crop image to identify the exact box boundaries
# 2. The calibration grid overlay to read off PDF point coordinates
# 3. Cross-referenced with the known row boundaries from pdfplumber
#
# Format: (x_left, y_bottom, x_right, y_top) then center = midpoint
# =====================================================================

# Item 1 - Insurance type checkboxes row
# The checkbox row sits between rl_y=707 (bottom) and rl_y=732 (top)
# From the crop image, checkboxes are in the BOTTOM sub-row (below the labels)
# Their vertical span: approximately rl_y=709 to rl_y=720 (11pt tall)
#
# From grid overlay inspection, the 7 checkbox boxes have these x ranges:
# Measuring from the calibration grid PNG where 50pt grid lines are visible:
#
# Looking at the crop carefully:
# - After "1." there's a checkbox at about x=31-41 (pdf), then "MEDICARE"  
# - Then checkbox at about x=93-103, then "MEDICAID"
# - Then checkbox at about x=143-153, then "TRICARE"  
# - Then checkbox at about x=209-219 (before CHAMPVA)
# - Then checkbox at about x=278-288 (before GROUP HEALTH PLAN)
# - Then checkbox at about x=337-347 (before FECA BLK LUNG)
# - Then checkbox at about x=393-403 (before OTHER)
#
# But wait - looking at the ACTUAL crop image more carefully:
# The boxes appear on the LOWER row (next to (Medicare#), (Medicaid#) etc.)
# Upper row: labels only
# Lower row: checkbox, (Medicare#), checkbox, (Medicaid#), etc.
#
# From the zoomed item1_checkboxes.png (8x crop of region (25, 705, 410, 740)):
# The lower checkboxes appear at:
# Box 1: left edge ~35px in 8x image = 25 + 35/8 = 29.4pt
# But more precisely from the grid...
# 
# Let me just read from the 2x grid image directly.
# In the grid image (1368 x 1728, 2x scale):
# Row of checkboxes is at pixel_y ~ 296-316 (in 2x image)
# That means rl_y = 864 - 148 to 864 - 158 = 716 to 706

# The checkboxes in the (Medicare#)/(Medicaid#) row:
# At 2x scale, reading x positions from the grid:
# Checkbox 1 (before Medicare#):  px ~58-78  -> pdf x = 29-39
# Checkbox 2 (before Medicaid#):  px ~164-184 -> pdf x = 82-92  
# Wait, that doesn't match. Let me recalculate.
# Looking at the grid image overlay where the labels are:
# "MEDICARE" label starts after the first checkbox...

# I think the most reliable approach is to just carefully look at the grid
# positions from the overlay image and the crop images together.

# From looking at BOTH the grid overlay and the crop images side by side:

CHECKBOX_RECTS = {
    # ── Item 1: Insurance Type ──────────────────────────────
    # 7 checkboxes in the (Medicare#) / (Medicaid#) row
    # Row sits ~2pt below labels, between rl_y=709 and rl_y=719
    # Each box is about 10x10pt
    "item1_medicare":          (32, 709, 42, 719),
    "item1_medicaid":          (92, 709, 102, 719),
    "item1_tricare":           (144, 709, 154, 719),
    "item1_champva":           (207, 709, 217, 719),
    "item1_group_health_plan": (278, 709, 288, 719),
    "item1_feca_blk_lung":     (338, 709, 348, 719),
    "item1_other":             (394, 709, 404, 719),
    
    # ── Item 3: Sex ─────────────────────────────────────────
    # Two checkboxes: M and F, in the SEX section (x ~340-400)
    # Between rl_y=687 and rl_y=697 approximately
    # From the crop: M box at ~x=349-359, F box at ~x=381-391
    "item3_sex_m":             (349, 687, 359, 697),
    "item3_sex_f":             (381, 687, 391, 697),
    
    # ── Item 6: Relationship ────────────────────────────────
    # Four checkboxes: Self, Spouse, Child, Other
    # Row between rl_y=662 and rl_y=672
    # From the crop (8x of region 265,656,415,686):
    # Self box:   x=291-301
    # Spouse box: x=329-339  
    # Child box:  x=368-378
    # Other box:  x=400-410
    "item6_self":              (291, 662, 301, 672),
    "item6_spouse":            (329, 662, 339, 672),
    "item6_child":             (368, 662, 378, 672),
    "item6_other":             (400, 662, 410, 672),
    
    # ── Item 10a: Employment ────────────────────────────────
    # Two checkboxes: YES and NO
    # Between rl_y=571 and rl_y=581
    # From crop: YES box at x=305-315, NO box at x=345-355
    "item10a_employment_yes":  (305, 571, 315, 581),
    "item10a_employment_no":   (345, 571, 355, 581),
    
    # ── Item 10b: Auto Accident ─────────────────────────────
    # Between rl_y=547 and rl_y=557
    # YES box at x=305-315, NO box at x=345-355
    "item10b_auto_yes":        (305, 547, 315, 557),
    "item10b_auto_no":         (345, 547, 355, 557),
    
    # ── Item 10c: Other Accident ────────────────────────────
    # Between rl_y=523 and rl_y=533
    # YES box at x=305-315, NO box at x=345-355
    "item10c_other_yes":       (305, 523, 315, 533),
    "item10c_other_no":        (345, 523, 355, 533),
    
    # ── Item 11d: Another Plan ──────────────────────────────
    # Between rl_y=498 and rl_y=508
    # From crop (8x of region 410,485,540,518):
    # YES box at x=435-445, NO box at x=471-481
    "item11d_yes":             (435, 498, 445, 508),
    "item11d_no":              (471, 498, 481, 508),
    
    # ── Item 27: Accept Assignment ──────────────────────────
    # Between rl_y=137 and rl_y=147
    # From crop (8x of region 318,125,415,160):
    # YES box at x=333-343, NO box at x=369-379
    "item27_yes":              (333, 137, 343, 147),
    "item27_no":               (369, 137, 379, 147),
}

# Compute centers for drawing the X mark
print("=== CHECKBOX RECTANGLE BOUNDARIES & CENTERS ===\n")
for name, (x0, y0, x1, y1) in CHECKBOX_RECTS.items():
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    w = x1 - x0
    h = y1 - y0
    print(f"  {name:35s}  rect=({x0:>3},{y0:>3},{x1:>3},{y1:>3})  "
          f"center=({cx:>5.1f},{cy:>5.1f})  size={w}x{h}")

# For drawing with drawString at font_size=8:
# The "X" character is approximately 5pt wide and 6pt ascent
# To visually center the X inside a 10x10 box:
#   draw_x = center_x - 2.5 (half char width)
#   draw_y = center_y - 3   (below center by half ascent)
print("\n=== DRAW COORDINATES (for drawString) ===\n")
for name, (x0, y0, x1, y1) in CHECKBOX_RECTS.items():
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    # For font size 8, X is ~4.5pt wide, ~5.5pt ascent
    draw_x = round(cx - 2.5, 1)
    draw_y = round(cy - 3.0, 1)
    print(f"  {name:35s}  draw=({draw_x:>6.1f}, {draw_y:>6.1f})")
