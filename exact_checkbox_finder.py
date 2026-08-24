"""
Exact measurement of every checkbox on the CMS-1500 template.
"""
from pypdfium2 import PdfDocument
from PIL import Image
import numpy as np

doc = PdfDocument("data/raw/Sample 1500_2012_02.pdf")
img = np.array(doc[0].render(scale=4).to_pil())

# Target regions in PDF coords (x0, y0_bot, x1, y1_top)
regions = {
    "item1": (60, 705, 411, 735),
    "item3_sex": (340, 680, 411, 707),
    "item6": (267, 658, 411, 684),
    "item10a": (267, 563, 411, 588),
    "item10b": (267, 538, 411, 565),
    "item10c": (267, 514, 411, 540),
    "item11d": (411, 490, 550, 516),
    "item27": (320, 130, 411, 157),
}

def analyze_region(name, r):
    x0_pdf, y0_bot, x1_pdf, y1_top = r
    # px range
    px0 = int(x0_pdf * 4)
    py0 = int((864 - y1_top) * 4)
    px1 = int(x1_pdf * 4)
    py1 = int((864 - y0_bot) * 4)
    
    crop = img[py0:py1, px0:px1]
    # Red mask
    red = (crop[:,:,0] > 170) & (crop[:,:,1] < 110) & (crop[:,:,2] < 110)
    
    # Save image with 10pt grid
    vis = crop.copy()
    for x in range(0, vis.shape[1], 40):
        vis[:, x, :] = [0, 255, 0] # green vertical line every 10pt
    for y in range(0, vis.shape[0], 40):
        vis[y, :, :] = [0, 0, 255] # blue horizontal line every 10pt
    Image.fromarray(vis).save(f"data/raw/grid_{name}.png")

for name, r in regions.items():
    analyze_region(name, r)

print("Saved all grid images")
