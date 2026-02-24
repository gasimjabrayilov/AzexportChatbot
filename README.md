# AykhanGroupChatBot (FastAPI)

Minimal FastAPI web chat UI that:

- Uses OpenAI to extract a short search query from the user message
- Queries Supabase for matching businesses
- Returns formatted results in Azerbaijani

## Requirements

- Python 3.11+
- A Supabase project with a table/view named `members_with_keywords`

## Configuration (env vars)

This app reads secrets from environment variables (recommended via a local `.env` file).

Required:

- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

Use `.env` as a template:

```bash
cp .env
```

Security note: `SUPABASE_SERVICE_KEY` is highly privileged. Prefer using an anon key + Row Level Security (RLS) if you plan to expose this publicly.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000/`

## API

- `GET /` – serves `templates/chat.html`
- `POST /api/chat` – expects JSON:

```json
{ "session_id": "optional", "message": "..." }
```

Example:

```bash
curl -s http://127.0.0.1:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"session_id":"test","message":"logistika"}'
```

## How business selection works (Supabase)

- The model extracts keywords from the user message.
- The app searches `members_with_keywords` where either `services_text` or `company_name` matches the extracted tokens (`ilike`).
- Returned rows are formatted using these fields (if present): `company_name`, `full_name`, `position`, `phone`, `services_text`.

## Deploying

You don’t need Docker to deploy.

Run command on most platforms:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Set environment variables in your hosting provider (do not upload your `.env`).

