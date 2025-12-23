# app/ai/pdf_render.py
from __future__ import annotations
from typing import List, Tuple
import fitz  # pymupdf
import io
from PIL import Image

def pdf_to_jpegs(
    pdf_path: str,
    dpi: int = 180,
    max_pages: int = 5,
) -> List[Tuple[int, bytes]]:
    """
    Returns list of (page_number_1_based, jpeg_bytes)
    """
    doc = fitz.open(pdf_path)
    out: List[Tuple[int, bytes]] = []

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    page_count = doc.page_count
    pages = list(range(min(page_count, max_pages)))  # 0-based

    for i in pages:
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        out.append((i + 1, buf.getvalue()))

    doc.close()
    return out
