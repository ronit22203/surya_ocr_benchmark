# Corpus layout

PDFs are local artifacts and are not required in git. Silver text is small and can be versioned.

```
corpus/
  nightmares/           full OA PDFs (10 files)
  nightmare_slices/     pages 2–4 as one-page PDFs (26 files)
  silver/               LLM transcriptions
    {id}.md             readable transcription
    {id}.json           id, source path, model, timestamp, text
    index.json          catalog
  gold/                 [not created yet]
```

`{id}` looks like `PMC13514518_p3` (PMCID + 1-indexed page).

Current silver set: **26 pages**, model `gpt-4o`, written 2026-09-27 (see `corpus/silver/index.json`).
