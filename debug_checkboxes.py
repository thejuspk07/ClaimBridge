"""
Precisely find the exact pixel coordinates of the red checkbox boxes in the template.
"""
from pypdfium2 import PdfDocument
from PIL import Image
import numpy as np

doc = PdfDocument("data/raw/Sample 1500_2012_02.pdf")
img = np.array(doc[0].render(scale=4).to_pil())

# Let's inspect small crops around each checkbox group
# We will draw a green border on each detected box and save an image

# Form left edge is x=60.4 pt -> 241 px
# Form top edge is y=732 pt -> (864-732)*4 = 528 px
# Form bottom of Item 1 is y=707 pt -> (864-707)*4 = 628 px

# Let's extract the exact red pixels in Item 1: y in [528, 628], x in [240, 1640]
crop1 = img[528:628, 240:1640]
# Red mask
red1 = (crop1[:,:,0] > 180) & (crop1[:,:,1] < 100) & (crop1[:,:,2] < 100)

# Let's save a visualization with grid lines every 10 pt (40 px)
vis1 = crop1.copy()
for x in range(0, vis1.shape[1], 40):
    vis1[:, x, :] = [0, 255, 0] # green line every 10pt
Image.fromarray(vis1).save("data/raw/item1_grid_vis.png")
print("Saved item1_grid_vis.png")
