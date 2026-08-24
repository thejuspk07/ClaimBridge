"""
OCR Service wrapping PaddleOCR engine.
Extracts text bounding boxes and polygon coordinates on CPU.
"""
from pathlib import Path
from typing import Any, Dict, List
import threading
from paddleocr import PaddleOCR


class OCRService:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        print("Initializing PaddleOCR Engine (CPU)...")
        self.ocr = PaddleOCR(
            lang="en",
            device="cpu",
            enable_mkldnn=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        print("PaddleOCR Engine ready.")

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def process_image(self, image_path: Path) -> List[Dict[str, Any]]:
        """
        Runs OCR on the given image path and returns standardized OCR JSON records.
        """
        result = self.ocr.predict(str(image_path))
        ocr_output = []

        for page_number, page in enumerate(result, start=1):
            texts = page.get("rec_texts", [])
            scores = page.get("rec_scores", [])
            boxes = page.get("rec_polys", [])

            for text, score, box in zip(texts, scores, boxes):
                points = box.tolist()
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]

                ocr_output.append({
                    "page": page_number,
                    "text": str(text),
                    "confidence": float(score),
                    "polygon": points,
                    "bbox": {
                        "x1": float(min(xs)),
                        "y1": float(min(ys)),
                        "x2": float(max(xs)),
                        "y2": float(max(ys)),
                    },
                })

        return ocr_output
