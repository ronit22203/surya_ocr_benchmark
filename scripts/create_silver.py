#!/usr/bin/env python3
"""
create_silver.py
Render nightmare-slice PDFs and transcribe them with an OpenAI vision model
to produce a silver (LLM) ground-truth set for OCR benchmarking.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pymupdf as fitz
from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "corpus" / "nightmare_slices"
OUTPUT_DIR = PROJECT_ROOT / "corpus" / "silver"

SYSTEM_PROMPT = """You are a document transcription engine used to build OCR evaluation ground truth.

Transcribe EVERY visible character on the page. Do not summarize, paraphrase, omit, or invent content.

Rules:
- Preserve natural reading order (complete the left column before the right column when the layout is multi-column).
- Keep headings, captions, footnotes, headers, and footers.
- Render tables as GitHub-flavored Markdown tables. Use HTML tables only if the layout is nested or has row/column spans that Markdown cannot represent.
- Render math as LaTeX ($inline$ or $$display$$).
- Mark text you cannot read as [ILLEGIBLE].
- Output only the transcription. No preamble, no markdown fences around the whole page.
"""

USER_PROMPT = (
    "Transcribe this journal page exactly for OCR benchmarking. "
    "Preserve layout semantics (columns, tables, equations) as specified."
)


def load_api_key() -> str:
    load_dotenv(PROJECT_ROOT / ".env")
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise SystemExit("[!] OPENAI_API_KEY is missing. Put it in the project .env file.")
    return key


def render_page_png(pdf_path: Path, dpi: int = 200, max_width: int = 2048) -> bytes:
    """Rasterize the first (and only) page of a slice PDF to PNG bytes."""
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        if pix.width > max_width:
            zoom *= max_width / pix.width
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def transcribe_image(client: OpenAI, model: str, png_bytes: bytes) -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": USER_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
            )
            text = (response.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("Empty transcription from model")
            return text
        except RateLimitError as exc:
            last_error = exc
            sleep_s = 2 ** attempt
            print(f"    -> Rate limited; retrying in {sleep_s}s")
            time.sleep(sleep_s)
        except APIError as exc:
            last_error = exc
            sleep_s = 2 ** attempt
            print(f"    -> API error ({exc}); retrying in {sleep_s}s")
            time.sleep(sleep_s)
    raise RuntimeError(f"Transcription failed after retries: {last_error}")


def write_record(out_dir: Path, stem: str, record: dict) -> None:
    md_path = out_dir / f"{stem}.md"
    json_path = out_dir / f"{stem}.json"
    md_path.write_text(record["text"] + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_index(out_dir: Path) -> None:
    records = []
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        records.append(json.loads(path.read_text(encoding="utf-8")))
    index = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "count": len(records),
        "records": [
            {
                "id": r["id"],
                "source_pdf": r["source_pdf"],
                "model": r["model"],
                "markdown": f"{r['id']}.md",
                "json": f"{r['id']}.json",
            }
            for r in records
        ],
    }
    (out_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def create_silver(
    input_dir: Path,
    output_dir: Path,
    model: str,
    limit: int | None,
    overwrite: bool,
) -> None:
    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"[!] No PDFs found in {input_dir}. Run scripts/slice_pages.py first.")

    if limit is not None:
        pdfs = pdfs[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=load_api_key())

    print(f"[+] Transcribing {len(pdfs)} slice(s) from {input_dir}")
    print(f"[+] Writing silver set to {output_dir} (model={model})")

    done = 0
    skipped = 0
    failed = 0

    for pdf_path in pdfs:
        stem = pdf_path.stem
        md_path = output_dir / f"{stem}.md"
        if md_path.exists() and not overwrite:
            print(f"    -> Skip existing {stem}")
            skipped += 1
            continue

        print(f"[{done + skipped + failed + 1}/{len(pdfs)}] {pdf_path.name}")
        try:
            png_bytes = render_page_png(pdf_path)
            text = transcribe_image(client, model, png_bytes)
            record = {
                "id": stem,
                "source_pdf": pdf_path.name,
                "source_path": str(pdf_path.relative_to(PROJECT_ROOT)),
                "model": model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "text": text,
            }
            write_record(output_dir, stem, record)
            print(f"    -> Wrote {stem}.md ({len(text)} chars)")
            done += 1
        except Exception as exc:
            failed += 1
            print(f"    -> Failed {pdf_path.name}: {exc}")
        time.sleep(0.4)

    write_index(output_dir)
    print(
        f"\n[+] Silver set complete: {done} new, {skipped} skipped, {failed} failed. "
        f"Index at {output_dir / 'index.json'}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a silver OCR benchmark set from nightmare slices.")
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o"),
        help="OpenAI vision model (override with OPENAI_MODEL).",
    )
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N PDFs.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing silver files.")
    return parser.parse_args()


if __name__ == "__main__":
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    create_silver(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model=args.model,
        limit=args.limit,
        overwrite=args.overwrite,
    )
