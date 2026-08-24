"""
PDF Rendering Service using pypdfium2.
Renders CMS-1500 PDF pages to exact calibrated 1368 x 1728 PNG.
"""
from pathlib import Path
import pypdfium2 as pdfium


def render_pdf_to_png(pdf_path: Path, output_png_path: Path, scale: int = 2) -> Path:
    """
    Renders the first page of a PDF document to PNG at the specified scale.
    scale=2 on a 684x864 pt CMS-1500 PDF yields exactly 1368x1728 pixels.
    """
    pdf = pdfium.PdfDocument(str(pdf_path))
    page = pdf[0]
    image = page.render(scale=scale).to_pil()
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(output_png_path))
    return output_png_path
