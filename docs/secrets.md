# Secrets

The OpenAI key lives only in `.env` at the repo root:

```
OPENAI_API_KEY=...
```

Optional:

```
OPENAI_MODEL=gpt-4o
```

`.gitignore` contains `.env`. That file is **not** tracked. Do not `git add .env`.

`create_silver.py` loads the key via `python-dotenv` and never prints it. Silver JSON stores model name and transcription text only—no key.
