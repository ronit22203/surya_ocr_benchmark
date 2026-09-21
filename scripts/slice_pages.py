#!/usr/bin/env python3
"""
slice_pages.py
Isolates high-entropy pages (dense multi-column text and tables)
from the 10 nightmare PDFs into a dedicated evaluation slice.
"""

from pathlib import Path
import pymupdf as fitz

# Project root paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "corpus" / "nightmares"
OUTPUT_DIR = PROJECT_ROOT / "corpus" / "nightmare_slices"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1-indexed pages: typically methods, results, and data tables
# (skip cover / affiliations on page 1).
TARGET_PAGES = [2, 3, 4]


def slice_target_pages():
    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[!] No PDFs found in {INPUT_DIR}. Run fetch_nightmare_data.py first.")
        return

    print(f"[+] Slicing high-entropy pages from {len(pdf_files)} nightmare PDFs...")

    sliced_count = 0
    skipped_short = 0

    for pdf_path in pdf_files:
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            extracted_from_doc = 0

            for page_num in TARGET_PAGES:
                page_idx = page_num - 1
                if page_idx >= page_count:
                    continue

                out_pdf_path = OUTPUT_DIR / f"{pdf_path.stem}_p{page_num}.pdf"

                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
                new_doc.save(out_pdf_path)
                new_doc.close()

                sliced_count += 1
                extracted_from_doc += 1
                print(f"    -> Secured slice: {out_pdf_path.name}")

            if extracted_from_doc == 0:
                skipped_short += 1
                print(
                    f"    -> Skipped {pdf_path.name}: only {page_count} page(s); "
                    f"need at least page {TARGET_PAGES[0]}."
                )
            doc.close()
        except Exception as e:
            print(f"    -> Error slicing {pdf_path.name}: {e}")

    print(
        f"\n[+] Slicing complete. Locked in {sliced_count} high-entropy pages "
        f"under {OUTPUT_DIR}/."
    )
    if skipped_short:
        print(f"[!] {skipped_short} PDF(s) were shorter than page {TARGET_PAGES[0]}.")


if __name__ == "__main__":
    slice_target_pages()
