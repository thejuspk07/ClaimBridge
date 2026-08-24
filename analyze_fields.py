"""
Detailed field boundary extraction from the CMS-1500 template.

Uses pdfplumber to get all horizontal and vertical lines, then maps them
into the CMS-1500 field grid to determine exact writable regions.
"""

import json
from pathlib import Path

PAGE_H = 864

with open("data/raw/template_elements.json") as f:
    d = json.load(f)

# Build sorted line lists
horiz = sorted(
    [l for l in d["lines"] if abs(l["top"] - l["bottom"]) < 2 and (l["x1"] - l["x0"]) > 15],
    key=lambda l: -l["rl_y0"]
)
vert = sorted(
    [l for l in d["lines"] if abs(l["x0"] - l["x1"]) < 2 and abs(l["rl_y1"] - l["rl_y0"]) > 8],
    key=lambda l: l["x0"]
)

# Key horizontal lines (rl_y values, top-to-bottom of form)
print("=== KEY HORIZONTAL BOUNDARIES ===")
h_ys = sorted(set(round(h["rl_y0"]) for h in horiz), reverse=True)
for y in h_ys:
    matching = [h for h in horiz if abs(round(h["rl_y0"]) - y) < 2]
    spans = [(round(h["x0"]), round(h["x1"])) for h in matching]
    print(f"  rl_y={y:>4d}  spans={spans}")

# Key vertical lines
print("\n=== KEY VERTICAL BOUNDARIES ===")
v_xs = sorted(set(round(v["x0"]) for v in vert))
for x in v_xs:
    matching = [v for v in vert if abs(round(v["x0"]) - x) < 2]
    ranges = [(round(v["rl_y0"]), round(v["rl_y1"])) for v in matching]
    print(f"  x={x:>4d}  y_ranges={ranges}")

# From the grid image, determine field regions
# The form has these major horizontal row boundaries:
# rl_y=732 - top of form / Item 1 row top
# rl_y=707 - bottom of Item 1 / top of Item 2
# rl_y=684 - bottom of Item 2-3 / top of Item 5-6-7
# rl_y=660 - bottom of Item 5 street / ...
# rl_y=636 - bottom of Item 5 city / Item 8 
# rl_y=611 - bottom of Item 5 zip-phone / Item 9
# rl_y=588 - Item 9a
# rl_y=565 - Item 9b/10b 
# rl_y=540 - Item 9c/10c
# rl_y=516 - Item 9d/10d/11d
# rl_y=492 - Item 12/13
# rl_y=444 - Item 14/15/16/17/18
# rl_y=420 - Item 17
# rl_y=396 - Item 18/19
# rl_y=372 - Item 19
# rl_y=349 - Item 21 diagnosis area top
# rl_y=338 - 
# rl_y=325 -
# rl_y=324 - Bottom of diagnosis / top of Item 22/23
# rl_y=301 - Item 22/23 bottom / Item 24 header
# rl_y=277 - Service line 1 bottom
# rl_y=252 - Service line 2 bottom
# rl_y=229 - Service line 3 bottom
# rl_y=204 - Service line 4 bottom
# rl_y=181 - Service line 5 bottom
# rl_y=157 - Service line 6 bottom / Item 25-30 top
# rl_y=133 - Item 25-30 bottom / Item 31-33 top
# rl_y=86  - NPI line
# rl_y=72  - bottom of form

# x=411 is the major vertical divider (left half vs right half)
# x=267 is a divider in the left half 
# x=519 is the NPI column divider in service lines

# Service line column boundaries from vertical lines:
# x=60 left edge
# x=123 - date "To" divider
# x=187 - place of service left edge  
# x=210 - between POS columns
# x=232 - procedure code left edge
# x=284 - modifier divider
# x=375 - diagnosis pointer left edge
# x=411 - charges left edge
# x=475 - units/days left edge
# x=504 - 
# x=519 - rendering NPI left edge
# x=540 - 
# x=629 - right edge

print("\n=== DERIVED FIELD WRITABLE REGIONS ===")
print("(field, x_write, y_write, max_width, font_size)")

# Using the grid image and line data, the writable baselines
# should be a few points above the bottom border of each field.
# Standard: baseline = bottom_border + 3 to 5 points

fields = {
    # VERIFIED coordinates (user confirmed)
    "item2_patient_name": {"x": 64, "y": 691, "fs": 9, "note": "VERIFIED"},
    "item3_dob_mm": {"x": 271, "y": 687, "fs": 8, "note": "VERIFIED"},
    "item3_dob_dd": {"x": 299, "y": 687, "fs": 8, "note": "VERIFIED"},
    "item3_dob_yy": {"x": 321, "y": 687, "fs": 8, "note": "VERIFIED"},
    "item1a_insured_id": {"x": 416, "y": 713, "fs": 8, "note": "VERIFIED"},
    "item31_signature": {"x": 65, "y": 75, "fs": 9, "note": "VERIFIED"},
    
    # Service row 1 VERIFIED x positions
    "svc1_date": {"x": 63, "y": 280, "fs": 7, "note": "VERIFIED"},
    "svc1_procedure": {"x": 235, "y": 280, "fs": 7, "note": "VERIFIED"},
    "svc1_dx_ptr": {"x": 378, "y": 280, "fs": 7, "note": "VERIFIED"},
    "svc1_charges": {"x": 414, "y": 280, "fs": 7, "note": "VERIFIED"},
    "svc1_npi": {"x": 560, "y": 280, "fs": 7, "note": "VERIFIED"},
}

# From the grid image analysis:
# Row rl_y boundaries and writable baselines:
# 
# Item 1: top=732, bottom=707, baseline=713  (checkboxes row)
# Item 2: top=707, bottom=684, baseline=691  (patient name)  
# Item 3: inside Item 2 row, DOB at y=687
# Item 4: same row as Item 2, right half x=411+
# Item 5 street: top=684, bottom=660, baseline=666
# Item 5 city: top=660, bottom=636, baseline=642
# Item 5 state: same row as city, x=240
# Item 6: top=684, bottom=660 (checkboxes), y=666
# Item 5 zip: top=636, bottom=611, baseline=617
# Item 5 phone: same row, x=153
# Item 7 street: same as Item 5 street but x=411+
# Item 7 city: same as Item 5 city but x=411+
# Item 7 state: x=582 area
# Item 7 zip: same as Item 5 zip but x=411+
# Item 7 phone: same row, x=504
# Item 9: top=611, bottom=588, baseline=593  
# Item 9a: top=588, bottom=565, baseline=570
# Item 10a: same row as 9a, right side
# Item 10b: top=565, bottom=540, baseline=547
# Item 10c: top=540, bottom=516, baseline=521
# Item 11: same rows as 9-9c, right half
# Item 11 policy: top=611, bottom=588, baseline=593
# Item 11a DOB: top=588, bottom=565, baseline=570
# Item 11c plan: top=540, bottom=516, baseline=521 (actually at rl_y=447 area)
# Looking more carefully at the grid...
# 
# The left column has: Item 9, 9a, 9b, 9c, 9d
# The middle has: Item 10a, 10b, 10c, 10d
# The right column: Item 11, 11a, 11b, 11c, 11d
#
# Item 12/13 signature: rl_y 492 to 444
# Item 14: top=444, bottom=420, baseline=425
# Item 17: top=420, bottom=396, baseline=401
# Item 18: same as 17 row, right half
# Item 19: top=396, bottom=372, baseline=377
# Item 21 diagnosis: top=372, bottom=324 area
#   - The diagnosis code cells appear in 3 rows of 4
#   - Row A-D: baseline around 349
#   - Row E-H: baseline around 337
#   - Row I-L: baseline around 325
#   - Column positions from horiz lines at x=74, 124, 167, 218, 261, 312, 354, 406
# Item 22: top=324, bottom=301, baseline=306
# Item 23: same as 22, right portion or below
# 
# Service lines (Item 24): 
#   Row 1: top=301, bottom=277, baseline=280
#   Row 2: top=277, bottom=252, baseline=256
#   Row 3: top=252, bottom=229, baseline=232
#   Row 4: top=229, bottom=204, baseline=208
#   Row 5: top=204, bottom=181, baseline=184
#   Row 6: top=181, bottom=157, baseline=161
#
# Item 25-30 row: top=157, bottom=133
#   Item 25: x=60 to ~216, baseline=138
#   Item 26: x=217 to ~322, baseline=138
#   Item 27: x=322 to ~411, baseline=138
#   Item 28: x=411 to ~494, baseline=138
#   Item 29: x=494 to ~560, baseline=138
#   Item 30: x=560 to ~629, baseline=138
#
# Item 31-33 row: top=133, bottom=72
#   Item 31: x=60 to ~216
#   Item 32: x=217 to ~411
#   Item 33: x=411 to ~629

# Now derive the corrected baseline per field
corrected = {}

# Row: Item 1 (checkboxes) - top=732, bottom=707
# Checkbox Y baseline = 707 + 3 = 710 (inside the row)
corrected["item1_checkboxes_y"] = 712

# Row: Items 2,3,4 - top=707, bottom=684
corrected["items_2_3_4_y_baseline"] = 691  # VERIFIED

# Row: Items 5(street), 6, 7(street) - top=684, bottom=660
corrected["row_5_street_y"] = 665

# Row: Items 5(city/state), 8, 7(city/state) - top=660, bottom=636
corrected["row_5_city_y"] = 641

# Row: Items 5(zip/phone), 7(zip/phone) - top=636, bottom=611
corrected["row_5_zip_y"] = 617

# Row: Items 9, 11(policy) - top=611, bottom=588
corrected["row_9_y"] = 594

# Row: Items 9a, 10a, 11a - top=588, bottom=565
corrected["row_9a_y"] = 571

# Row: Items 9b, 10b, 11b - top=565, bottom=540
corrected["row_9b_y"] = 546

# Row: Items 9c, 10c, 11c - top=540, bottom=516
# But from rl_y=540 line to rl_y=516 line
corrected["row_9c_y"] = 521

# Row: Items 9d/plan, 10d, 11d - top=516, bottom=492
corrected["row_9d_y"] = 498

# Row: Items 12, 13 (signatures) - top=492, bottom=444
corrected["row_12_13_y"] = 450

# Row: Items 14, 15, 16 - top=444, bottom=420
corrected["row_14_y"] = 426

# Row: Items 17, 17a, 18 - top=420, bottom=396
corrected["row_17_y"] = 402

# Row: Item 19, 20 - top=396, bottom=372
corrected["row_19_y"] = 378

# Diagnosis section (Item 21): top=372, bottom=324
# Cells have internal dividers
# A-D row: baseline ~352
# E-H row: baseline ~340  
# I-L row: baseline ~328
# Column x positions from the template:
# A/E/I: x=74
# B/F/J: x=167
# C/G/K: x=261
# D/H/L: x=355

# Items 22 (resubmission): between 323 and 301 
corrected["row_22_y"] = 308

# Item 23 (prior auth): same row area or below diag
corrected["row_23_y"] = 308

# Service line rows
corrected["svc_row_1_y"] = 282
corrected["svc_row_2_y"] = 258
corrected["svc_row_3_y"] = 234
corrected["svc_row_4_y"] = 210
corrected["svc_row_5_y"] = 186
corrected["svc_row_6_y"] = 162

# Item 25-30: top=157, bottom=133
corrected["row_25_y"] = 140

# Item 31-33: top=133, bottom=72
# Street line: baseline ~100 (midway)
# City line: baseline ~87
# NPI line (at rl_y=86): baseline ~76
corrected["row_32_street_y"] = 105
corrected["row_32_city_y"] = 90
corrected["row_32_npi_y"] = 76

print("\nCorrected field baselines:")
for k, v in corrected.items():
    print(f"  {k}: {v}")

# Now determine diagnosis cell positions more precisely
# From the horizontal lines in the diagnosis area:
# rl_y=349: top of A-D row
# rl_y=338: bottom of A-D / top of E-H
# rl_y=325: bottom of E-H / top of I-L
# rl_y=324: bottom of I-L

# So:
# A-D baseline = 338 + 3 = 341 (or ~349-5 = 344)
# Actually: row height = 349-338 = 11pt
# baseline = bottom + 2 = 340

# From horizontal line positions:
# x=74 to x=125 for A/E/I cells
# x=167 to x=218 for B/F/J cells  
# x=261 to x=312 for C/G/K cells
# x=355 to x=406 for D/H/L cells

print("\n=== DIAGNOSIS CELL POSITIONS ===")
diag_cols = {"A_E_I": 77, "B_F_J": 170, "C_G_K": 264, "D_H_L": 357}
diag_rows = {"A_D": 340, "E_H": 328, "I_L": 316}
# Wait, let me recalculate from the actual lines
# rl_y=349.2 (A-D top)
# rl_y=337.8 (A-D bottom / E-H top)  -> baseline A-D = 340
# rl_y=325.4 (E-H bottom / I-L top)  -> baseline E-H = 328
# rl_y=323.5 (I-L bottom)            -> baseline I-L = 315 (but this is only 2pt gap)

# The cells appear to be:
# Row 1 (A-D): rl_y 349 to 338, baseline = 340
# Row 2 (E-H): rl_y 338 to 325, baseline = 328
# Row 3 (I-L): rl_y 325 to 324, baseline = This row is very small, maybe skip

# Actually looking at the grid image more carefully:
# The diagnosis section has underline-style cells, not boxes
# The ICD indicator and cells are between rl_y=372 and rl_y=323
# Looking at the horizontal lines in that region:
# x=74 to 125 (51pt wide) at rl_y=349, 338, 325
# x=167 to 218 (51pt wide) at same y values
# x=261 to 312 (51pt wide) at same y values  
# x=355 to 406 (52pt wide) at same y values

# These are diagnosis code entry lines (not boxes)
# The lines at rl_y 349, 338, 325 are writing baselines
# So diagnosis codes should be written ON the line, meaning baseline = line_y
# Actually, text goes ABOVE the line, so baseline = line_y + 1 or 2

diag_positions = {
    "A": (77, 351),   # Row 1, col 1
    "B": (170, 351),  # Row 1, col 2
    "C": (264, 351),  # Row 1, col 3
    "D": (357, 351),  # Row 1, col 4
    "E": (77, 339),   # Row 2, col 1
    "F": (170, 339),  # Row 2, col 2
    "G": (264, 339),  # Row 2, col 3
    "H": (357, 339),  # Row 2, col 4
    "I": (77, 327),   # Row 3, col 1
    "J": (170, 327),  # Row 3, col 2
    "K": (264, 327),  # Row 3, col 3
    "L": (357, 327),  # Row 3, col 4
}

for cell, (x, y) in diag_positions.items():
    print(f"  Diag {cell}: x={x}, y={y}")

# Items 22-23 region
# Between rl_y=323 and rl_y=301
# Item 22 RESUBMISSION CODE: left part of right half, x ~415
# Item 22 ORIGINAL REF NO: x ~500 area 
# Item 23: full width below, same row or at rl_y about 308
# Looking at the grid: rl_y=323 to 301 is the 22/23 region
# Left half (x=60 to 411): Item 22 resubmission code on left, original ref on right
# Actually from the image:
# "22. RESUBMISSION CODE" label is at upper-left of right section (x~411)
# "ORIGINAL REF. NO." label is at upper-right
# "23. PRIOR AUTHORIZATION NUMBER" is below that

# The divider at rl_y=323 separates diagnosis from 22/23
# rl_y=301 separates 22/23 from service lines
# Baseline for 22: 323-301 = 22pt, baseline = 301+6 = 307
# But there may be a horizontal divider splitting 22 and 23
# From the lines: rl_y=348 at x=412-629 spans, and rl_y=323 at x=411-629
# So Item 22 is at top=348, bottom=323? No...
# Looking again: the horizontal line at rl_y=348.2 (x=412 to 629) separates 
# the diagnosis pointer area from Item 22
# And rl_y=323.4 (x=411 to 629) is below Item 22

# So right-half region: 
# Item 22: top=348, bottom=323, baseline=328
# Item 23: is labeled "23. PRIOR AUTHORIZATION NUMBER" 
# From the image it's between the item 22 area and item 24

# Actually looking more carefully at the image:
# On the RIGHT side:
# rl_y ~372 to ~348: "21. DIAGNOSIS OR NATURE OF ILLNESS..." label area  
# rl_y ~348 to ~323: TWO sub-rows
#   Upper: "22. RESUBMISSION CODE" and "ORIGINAL REF. NO."
#   Lower: "23. PRIOR AUTHORIZATION NUMBER"  
# There appears to be a line at ~rl_y=336 dividing them

# Let me check if there's a line at ~336 for x>411
divider_336 = [h for h in horiz if 330 < h["rl_y0"] < 345 and h["x0"] > 400]
print(f"\nLines near rl_y=336 (right side): {len(divider_336)}")
for h in divider_336:
    print(f"  x0={h['x0']:.1f} x1={h['x1']:.1f} rl_y={h['rl_y0']:.1f}")

# Check for more detail in the 22/23 and bottom sections
print("\n=== ALL LINES IN BOTTOM SECTION (rl_y < 160) ===")
bottom_lines = [h for h in horiz if h["rl_y0"] < 160]
for h in sorted(bottom_lines, key=lambda l: -l["rl_y0"]):
    print(f"  x0={h['x0']:>7.1f}  x1={h['x1']:>7.1f}  rl_y={h['rl_y0']:>7.1f}")

# Vertical lines in bottom section
bottom_vert = [v for v in vert if v["rl_y0"] < 160]
print(f"\nVertical lines in bottom section:")
for v in sorted(bottom_vert, key=lambda l: l["x0"]):
    print(f"  x={v['x0']:>7.1f}  rl_y_bot={v['rl_y0']:>7.1f}  rl_y_top={v['rl_y1']:>7.1f}")
