# OpenAI usage

`create_silver.py` bills **Chat Completions** with `gpt-4o` and `image_url` `detail: "high"`.

## Silver batch (2026-09-27)

Refreshed personal usage view:

| Metric | Dashboard |
| --- | --- |
| Total requests | 26 |
| Total tokens | 29,094 |
| September spend | $0.30 / $100.00 |
| Credit balance | $4.70 |
| Prompt cache hit rate | 0% |

That matches the local run: **26 Chat Completions**, one per nightmare slice. About **1.1k tokens and ~$0.012 per page**.

The first glance at the panel (1 request / 1,289 tokens / $0.01) was the `--limit 1` smoke test before usage logs caught up. After a refresh, counts aligned with `corpus/silver/index.json`.

## Re-runs

`--overwrite` re-sends every page and re-bills (~$0.30 for this 26-page set). Default behavior skips existing `.md` files.

Use `--limit` while iterating on prompts.

## Dashboard notes

- Window: **24h** can miss a batch until logs settle; **7d** is safer for a same-day check.
- API surface: **Chat Completions**, not Responses.
- Project: must match the `sk-proj-…` key in `.env`.
