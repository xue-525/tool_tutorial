"""CLI entry: extract figures from a paper PDF, name by caption, write index."""
import argparse
import os
import sys

from extractor import PaperFigureExtractor


def main():
    parser = argparse.ArgumentParser(
        description="Extract figures from a paper PDF and name them by their captions.",
    )
    parser.add_argument("pdf", help="Path to the input PDF")
    parser.add_argument("-o", "--output", default="figures",
                        help="Output directory (default: ./figures)")
    parser.add_argument("--dpi", type=int, default=200,
                        help="Rendering DPI for extracted figures (default: 200)")
    parser.add_argument("--ocr", action="store_true",
                        help="Force OCR even if the PDF contains text")
    parser.add_argument("--lang", default="eng+chi_sim",
                        help="Tesseract language(s), default eng+chi_sim")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"error: file not found: {args.pdf}", file=sys.stderr)
        return 1

    extractor = PaperFigureExtractor(
        pdf_path=args.pdf,
        output_dir=args.output,
        dpi=args.dpi,
        force_ocr=args.ocr,
        ocr_lang=args.lang,
    )
    records = extractor.extract()

    if not records:
        print("No figures detected. The PDF may be scanned without OCR — "
              "try re-running with --ocr.")
        return 0

    print(f"Extracted {len(records)} figure(s) to: {args.output}")
    for rec in records:
        print(f"  page {rec.page}: {rec.filename}  <-  {rec.caption}")
    print(f"Index written to: {os.path.join(args.output, 'figures.txt')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
