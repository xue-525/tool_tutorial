"""Extract figures from a PDF paper using PyMuPDF and OCR fallback."""
import io
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import fitz  # PyMuPDF

from captions import parse_caption, sanitize_filename


@dataclass
class Caption:
    number: str
    title: str
    bbox: Tuple[float, float, float, float]
    page_index: int
    full_text: str


@dataclass
class FigureRecord:
    filename: str
    caption: str
    page: int
    number: Optional[str] = None


class PaperFigureExtractor:
    def __init__(self, pdf_path: str, output_dir: str, dpi: int = 200,
                 force_ocr: bool = False, ocr_lang: str = "eng+chi_sim"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.dpi = dpi
        self.force_ocr = force_ocr
        self.ocr_lang = ocr_lang
        self.records: List[FigureRecord] = []
        os.makedirs(output_dir, exist_ok=True)

    # ---------------- public ----------------
    def extract(self) -> List[FigureRecord]:
        doc = fitz.open(self.pdf_path)
        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                captions = self._find_captions(page, page_index)
                if not captions:
                    continue
                for cap in captions:
                    bbox = self._infer_figure_bbox(page, cap, captions)
                    if bbox is None or bbox.is_empty or bbox.height < 20:
                        continue
                    self._render_and_save(page, bbox, cap)
        finally:
            doc.close()
        self._write_index()
        return self.records

    # ---------------- caption detection ----------------
    def _find_captions(self, page, page_index: int) -> List[Caption]:
        captions: List[Caption] = []
        text_blocks = page.get_text("blocks") or []
        has_text = any((b[4] or "").strip() for b in text_blocks)

        if has_text and not self.force_ocr:
            for block in text_blocks:
                x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4]
                parsed = parse_caption(text or "")
                if parsed:
                    number, title = parsed
                    captions.append(Caption(
                        number=number, title=title,
                        bbox=(x0, y0, x1, y1),
                        page_index=page_index,
                        full_text=(text or "").strip().replace("\n", " "),
                    ))
        else:
            captions = self._ocr_captions(page, page_index)
        return captions

    def _ocr_captions(self, page, page_index: int) -> List[Caption]:
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return []

        pix = page.get_pixmap(dpi=self.dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        scale_x = page.rect.width / pix.width
        scale_y = page.rect.height / pix.height

        try:
            data = pytesseract.image_to_data(
                img, lang=self.ocr_lang,
                output_type=pytesseract.Output.DICT,
            )
        except pytesseract.TesseractError:
            return []

        # Group words by (block_num, par_num, line_num)
        lines = {}
        for i, word in enumerate(data["text"]):
            if not word.strip():
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            entry = lines.setdefault(key, {
                "words": [], "x0": 1e9, "y0": 1e9, "x1": 0, "y1": 0,
            })
            entry["words"].append(word)
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            entry["x0"] = min(entry["x0"], x)
            entry["y0"] = min(entry["y0"], y)
            entry["x1"] = max(entry["x1"], x + w)
            entry["y1"] = max(entry["y1"], y + h)

        captions: List[Caption] = []
        for entry in lines.values():
            text = " ".join(entry["words"])
            parsed = parse_caption(text)
            if parsed:
                number, title = parsed
                bbox = (
                    entry["x0"] * scale_x, entry["y0"] * scale_y,
                    entry["x1"] * scale_x, entry["y1"] * scale_y,
                )
                captions.append(Caption(
                    number=number, title=title, bbox=bbox,
                    page_index=page_index, full_text=text,
                ))
        return captions

    # ---------------- figure region inference ----------------
    def _infer_figure_bbox(self, page, caption: Caption, all_caps: List[Caption]):
        page_rect = page.rect
        cap_x0, cap_y0, cap_x1, cap_y1 = caption.bbox

        # Collect candidate visual rects: embedded images and vector drawings.
        rects = []
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                rects.extend(page.get_image_rects(xref))
            except Exception:
                pass
        try:
            for d in page.get_drawings():
                r = d.get("rect")
                if r is not None and r.width > 5 and r.height > 5:
                    rects.append(r)
        except Exception:
            pass

        # Keep rects above the caption and not overlapping other captions.
        def overlaps_other_caption(r):
            for other in all_caps:
                if other is caption:
                    continue
                ox0, oy0, ox1, oy1 = other.bbox
                if r.y0 < oy1 and r.y1 > oy0 and r.x0 < ox1 and r.x1 > ox0:
                    return True
            return False

        candidates = []
        for r in rects:
            if r.y1 <= cap_y0 + 4 and r.y1 >= cap_y0 - 600:
                if overlaps_other_caption(r):
                    continue
                candidates.append(r)

        if candidates:
            x0 = min(r.x0 for r in candidates)
            y0 = min(r.y0 for r in candidates)
            x1 = max(r.x1 for r in candidates)
            y1 = max(r.y1 for r in candidates)
            # Pad slightly
            pad = 2
            return fitz.Rect(
                max(page_rect.x0, x0 - pad),
                max(page_rect.y0, y0 - pad),
                min(page_rect.x1, x1 + pad),
                min(page_rect.y1, y1 + pad),
            )

        # Fallback: region above the caption up to the previous content edge.
        top = page_rect.y0
        for other in all_caps:
            if other is caption:
                continue
            _, _, _, oy1 = other.bbox
            if oy1 < cap_y0 and oy1 > top:
                top = oy1
        return fitz.Rect(page_rect.x0 + 4, top + 4, page_rect.x1 - 4, cap_y0 - 2)

    # ---------------- rendering ----------------
    def _render_and_save(self, page, bbox, caption: Caption):
        pix = page.get_pixmap(clip=bbox, dpi=self.dpi)
        num_safe = caption.number.replace(".", "_")
        title_safe = sanitize_filename(caption.title)
        filename = f"figure_{num_safe}_{title_safe}.png"

        # Avoid name collisions across pages.
        path = os.path.join(self.output_dir, filename)
        if os.path.exists(path):
            base, ext = os.path.splitext(filename)
            i = 2
            while os.path.exists(os.path.join(self.output_dir, f"{base}_{i}{ext}")):
                i += 1
            filename = f"{base}_{i}{ext}"
            path = os.path.join(self.output_dir, filename)

        pix.save(path)
        self.records.append(FigureRecord(
            filename=filename,
            caption=f"Figure {caption.number}. {caption.title}",
            page=caption.page_index + 1,
            number=caption.number,
        ))

    # ---------------- index ----------------
    def _write_index(self):
        out = os.path.join(self.output_dir, "figures.txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write("# Extracted Figures\n\n")
            for rec in self.records:
                f.write(f"- `{rec.filename}` (page {rec.page}): {rec.caption}\n")
