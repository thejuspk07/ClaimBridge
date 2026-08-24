"""
Zoom in on each checkbox in the generated claim_001.png to verify visual centering.
"""
from pypdfium2 import PdfDocument
from PIL import Image

doc = PdfDocument("data/raw/claim_001.pdf")
img = doc[0].render(scale=4).to_pil()
PAGE_H = 864
SCALE = 4

regions = {
    "item1_medicare": (50, 700, 85, 730),
    "item3_sex": (345, 680, 410, 705),
    "item6_spouse": (315, 655, 350, 680),
    "item10a_employment": (295, 560, 370, 585),
    "item10b_auto": (295, 535, 370, 560),
    "item10c_other": (295, 510, 370, 535),
    "item11d_plan": (415, 490, 485, 515),
    "item27_accept": (325, 130, 395, 155),
}

for name, (x0, y0, x1, y1) in regions.items():
    px0 = int(x0 * SCALE)
    py0 = int((PAGE_H - y1) * SCALE)
    px1 = int(x1 * SCALE)
    py1 = int((PAGE_H - y0) * SCALE)
    crop = img.crop((px0, py0, px1, py1))
    crop.save(f"data/raw/zoom_{name}.png")

print("Saved all zoomed checkbox crops from claim_001.pdf")
