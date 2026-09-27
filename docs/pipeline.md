# Pipeline

Goal: score Surya OCR v1 vs v2 on dense, multi-column clinical pages—not on covers, affiliations, or reference lists.

```
Europe PMC OA PDFs
        │
        ▼
corpus/nightmares/          fetch_nightmare_data.py
        │
        ▼  pages 2–4 only
corpus/nightmare_slices/    slice_pages.py
        │
        ▼  gpt-4o vision transcription
corpus/silver/              create_silver.py
        │
        ▼  human (or audited) correction   [not built yet]
corpus/gold/                audit_golden.py (stub)
        │
        ▼
bench.py telemetry          RunPod RTX 4090   [not built yet]
```

## Why slice before OCR

Full 20-page PDFs burn cycles on pages where v1 and v2 will tie. High-entropy pages (methods, results, tables) are the eval subset.

## Silver vs gold

| Set | Who writes it | Role |
| --- | --- | --- |
| Silver | `gpt-4o` via `create_silver.py` | Cheap, revisable draft ground truth |
| Gold | Human pass over silver | Scoring source of truth |

Do not treat silver markdown as final labels. Tables, column order, and equations still need an audit before you publish a v1 vs v2 delta.
