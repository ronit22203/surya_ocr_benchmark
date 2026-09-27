# Scripts

Run from the repo root, with the project venv active (`.venv` / `uv`).

```bash
uv sync
source .venv/bin/activate   # or: .venv/bin/python scripts/<name>.py
```

## `scripts/fetch_nightmare_data.py`

Downloads 10 open-access clinical PDFs from Europe PMC.

- Search: `OPEN_ACCESS:Y HAS_PDF:Y`
- Binary URL: `https://europepmc.org/api/getPdf?pmcid={PMCID}`
- Output: `corpus/nightmares/{PMCID}.pdf`

The REST path `/webservices/rest/{PMCID}/pdf` is not a download endpoint (JSON 404). The articles `?pdf=render` URL is Cloudflare-blocked.

## `scripts/slice_pages.py`

Cuts 1-indexed pages **2, 3, 4** from each nightmare PDF into single-page files.

- Input: `corpus/nightmares/*.pdf`
- Output: `corpus/nightmare_slices/{PMCID}_p{N}.pdf`

Short papers (correction, letter) may only produce `_p2`.

## `scripts/create_silver.py`

Renders each slice to PNG and transcribes it with OpenAI vision.

```bash
python scripts/create_silver.py
python scripts/create_silver.py --limit 1          # smoke test
python scripts/create_silver.py --overwrite         # re-bill every page
python scripts/create_silver.py --model gpt-4o
```

- Reads `OPENAI_API_KEY` from `.env` (never printed)
- Skips existing `{id}.md` unless `--overwrite`
- Writes `corpus/silver/{id}.md`, `{id}.json`, and `index.json`

Uses **Chat Completions** (`client.chat.completions.create`), not the Responses API.

## `scripts/audit_golden.py`

Stub. Next step: review silver pages into `corpus/gold/`.
