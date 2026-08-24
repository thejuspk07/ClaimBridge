"""Analyze template horizontal and vertical lines to find field boundaries."""
import json

with open("data/raw/template_elements.json") as f:
    d = json.load(f)

PAGE_H = 864

print(f"Lines: {len(d['lines'])}")
print(f"Rects: {len(d['rects'])}")
print(f"Words: {len(d['words'])}")

# Horizontal lines (field top/bottom borders)
horiz = [l for l in d["lines"] if abs(l["top"] - l["bottom"]) < 2]
horiz.sort(key=lambda l: l["rl_y0"], reverse=True)
print(f"\n=== HORIZONTAL LINES ({len(horiz)}) sorted by rl_y (top to bottom) ===")
for h in horiz:
    span = h["x1"] - h["x0"]
    if span > 20:  # skip tiny marks
        print(f"  x0={h['x0']:>7.1f}  x1={h['x1']:>7.1f}  span={span:>6.1f}  rl_y={h['rl_y0']:>7.1f}")

# Vertical lines (field left/right borders)
vert = [l for l in d["lines"] if abs(l["x0"] - l["x1"]) < 2]
vert.sort(key=lambda l: (l["x0"], -l["rl_y1"]))
print(f"\n=== VERTICAL LINES ({len(vert)}) sorted by x ===")
for v in vert:
    span = abs(v["rl_y1"] - v["rl_y0"])
    if span > 10:
        print(f"  x={v['x0']:>7.1f}  rl_y_bot={v['rl_y0']:>7.1f}  rl_y_top={v['rl_y1']:>7.1f}  span={span:>6.1f}")
