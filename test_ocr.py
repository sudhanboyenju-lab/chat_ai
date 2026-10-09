"""
Test OCR without the browser. Put a photo of any document (or a screenshot of text) in
the project folder, then run:

    python test_ocr.py my_photo.jpg
"""
import sys

from ai_engine.ocr import extract_text, identify_document
from localgov_config import config, engine

path = sys.argv[1]
mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"

with open(path, "rb") as f:
    text = extract_text(f.read(), mime, config)

print("---- extracted text ----")
print(text)
print("---- identified as ----")
print(identify_document(text, engine.entities, config))
