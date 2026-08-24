"""
Locate checkbox centers from the CMS-1500 template using pdfplumber chars/words
and the calibration grid image.

CMS-1500 checkboxes are typically small squares (~8-10pt) drawn as form graphics.
We locate them by finding the label text next to each checkbox area and using
known CMS-1500 layout conventions.

Strategy: Render small crops of the template at high resolution around each 
checkbox region to identify exact boundaries.
"""
from pypdfium2 import PdfDocument
from PIL import Image

PAGE_H = 864

# Render at 4x for precise checkbox measurement
doc = PdfDocument("data/raw/Sample 1500_2012_02.pdf")
img = doc[0].render(scale=4).to_pil()
W, H = img.size
print(f"Image size: {W} x {H}")
print(f"Scale: {W/684:.1f}x horizontal, {H/864:.1f}x vertical")
scale = W / 684  # should be ~4.0

# For each checkbox region, crop and save a zoomed view
# PDF coords → pixel coords: px = x * scale, py = (PAGE_H - y) * scale

regions = {
    # Item 1 checkbox row: rl_y ~714, checkboxes from x~30 to x~400
    "item1_checkboxes": (25, 705, 410, 740),
    # Item 3 sex: rl_y ~686, x ~340-400
    "item3_sex": (330, 678, 410, 700),
    # Item 6 relationship: rl_y ~666, x ~267-411
    "item6_relationship": (265, 656, 415, 686),
    # Item 10a employment: rl_y ~571, x ~267-411
    "item10a_employment": (265, 555, 415, 590),
    # Item 10b auto accident: rl_y ~546, x ~267-411
    "item10b_auto_accident": (265, 530, 415, 568),
    # Item 10c other accident: rl_y ~522, x ~267-411
    "item10c_other_accident": (265, 505, 415, 545),
    # Item 11d another plan: rl_y ~498, x ~411-629
    "item11d_another_plan": (410, 485, 540, 518),
    # Item 27 accept assignment: rl_y ~140, x ~322-411
    "item27_accept_assignment": (318, 125, 415, 160),
}

for name, (x0, y0, x1, y1) in regions.items():
    # Convert rl_y to pixel: py = (PAGE_H - rl_y) * scale
    px0 = int(x0 * scale)
    py0 = int((PAGE_H - y1) * scale)  # y1 is top in RL, so top of crop
    px1 = int(x1 * scale)
    py1 = int((PAGE_H - y0) * scale)  # y0 is bottom in RL, so bottom of crop
    
    crop = img.crop((px0, py0, px1, py1))
    # Scale up 2x more for visibility
    crop = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
    crop.save(f"data/raw/checkbox_{name}.png")
    print(f"Saved checkbox_{name}.png  (crop: px={px0},{py0} to {px1},{py1})")
