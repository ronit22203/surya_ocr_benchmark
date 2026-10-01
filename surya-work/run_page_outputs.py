#!/usr/bin/env python3
"""Run Surya OCR on a single PDF page and write JSON, markdown, and debug images."""

from __future__ import annotations

import importlib.metadata
import json
import os
import re
import sys
from html import unescape
from pathlib import Path

from PIL import Image, ImageDraw
from surya.input.load import load_from_file
from surya.scripts.config import CLILoader


TAG_RE = re.compile(r"<[^>]+>")


def html_to_text(html: str) -> str:
    text = unescape(html or "")
    text = re.sub(r"(?i)</(p|div|h[1-6]|li|tr|br)\s*>", "\n", text)
    text = TAG_RE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def package_version() -> str:
    return importlib.metadata.version("surya-ocr")


def run_v1(images, highres_images):
    from surya.common.surya.schema import TaskNames
    from surya.debug.draw import draw_bboxes_on_image
    from surya.debug.text import draw_text_on_image
    from surya.detection import DetectionPredictor
    from surya.foundation import FoundationPredictor
    from surya.recognition import RecognitionPredictor

    rec = RecognitionPredictor(FoundationPredictor())
    preds = rec(
        images,
        task_names=[TaskNames.ocr_with_boxes] * len(images),
        det_predictor=DetectionPredictor(),
        highres_images=highres_images,
        math_mode=True,
    )
    pred = preds[0]
    image = images[0]
    dumped = pred.model_dump()

    bboxes = []
    md_lines = []
    for i, line in enumerate(pred.text_lines):
        bboxes.append(
            {
                "id": i,
                "type": "text_line",
                "text": line.text,
                "bbox": line.bbox,
                "polygon": line.polygon,
                "confidence": line.confidence,
            }
        )
        md_lines.append(line.text)

    overlay = draw_bboxes_on_image([b["bbox"] for b in bboxes], image.copy())
    recon = draw_text_on_image(
        [b["bbox"] for b in bboxes],
        [b["text"] for b in bboxes],
        image.size,
    )
    return dumped, bboxes, "\n".join(md_lines).strip() + "\n", overlay, recon


def run_v2(images, highres_images):
    from surya.debug.draw import draw_bboxes_on_image
    from surya.inference import SuryaInferenceManager
    from surya.recognition import RecognitionPredictor

    rec = RecognitionPredictor(SuryaInferenceManager())
    pages = rec(highres_images, full_page=True)
    page = pages[0]
    image = highres_images[0]
    dumped = page.model_dump()

    bboxes = []
    md_parts = []
    for i, blk in enumerate(page.blocks):
        bboxes.append(
            {
                "id": i,
                "type": "block",
                "label": blk.label,
                "raw_label": blk.raw_label,
                "reading_order": blk.reading_order,
                "skipped": blk.skipped,
                "error": blk.error,
                "bbox": blk.bbox,
                "polygon": blk.polygon,
                "html": blk.html,
            }
        )
        if blk.skipped:
            continue
        body = html_to_text(blk.html)
        if body:
            md_parts.append(f"## {blk.label}\n\n{body}")

    labels = [f"{b['reading_order']}:{b['label']}" for b in bboxes]
    overlay = draw_bboxes_on_image(
        [b["bbox"] for b in bboxes], image.copy(), labels=labels
    )
    recon = Image.new("RGB", image.size, "white")
    draw = ImageDraw.Draw(recon)
    for b in bboxes:
        x0, y0, x1, y1 = (int(v) for v in b["bbox"])
        draw.rectangle([x0, y0, x1, y1], outline="black", width=1)
        snippet = html_to_text(b["html"])[:180]
        if snippet:
            draw.text((x0 + 2, y0 + 2), snippet, fill="black")
    return dumped, bboxes, "\n\n".join(md_parts).strip() + "\n", overlay, recon


def main() -> None:
    input_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    page_range = CLILoader.parse_range_str(sys.argv[3]) if len(sys.argv) > 3 else [0]

    from surya.settings import settings

    images, names = load_from_file(str(input_path), page_range)
    highres_images, _ = load_from_file(
        str(input_path), page_range, settings.IMAGE_DPI_HIGHRES
    )

    folder = output_dir / Path(input_path).stem
    folder.mkdir(parents=True, exist_ok=True)

    version = package_version()
    major_minor = tuple(int(p) for p in version.split(".")[:2])
    if major_minor >= (0, 18):
        dumped, bboxes, markdown, overlay, recon = run_v2(images, highres_images)
        engine = "v2"
    else:
        dumped, bboxes, markdown, overlay, recon = run_v1(images, highres_images)
        engine = "v1"

    name = names[0]
    results = {name: [{**dumped, "page": 1}]}
    save_json(folder / "results.json", results)
    save_json(folder / "bboxes.json", {"engine": engine, "surya_ocr": version, "boxes": bboxes})
    (folder / "page.md").write_text(markdown, encoding="utf-8")
    overlay.save(folder / f"{name}_0_bboxes.png")
    recon.save(folder / f"{name}_0_ocr_debug.png")
    print(f"Wrote {engine} ({version}) outputs to {folder}")


if __name__ == "__main__":
    main()
