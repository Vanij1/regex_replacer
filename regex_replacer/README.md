# Regex Pattern Matching and Replacement

A small full-stack app for uploading CSV or Excel files, describing a match pattern in natural language, converting that description into regex with an LLM, and applying replacements to text columns.

## What it does

- Upload CSV or Excel files
- Preview the parsed dataset
- Describe a pattern in plain language, such as `find email addresses`
- Ask for a replacement or masking action
- Review the processed table and download the transformed file

## Tech stack

- Backend: Django
- API style: JSON over HTTP
- Frontend: React + Vite
- Data handling: pandas, openpyxl, xlrd
- LLM integration: OpenAI-compatible HTTP call with a local fallback rule engine

## Project layout

```text
regex_replacer/
  backend/
  frontend/
```

## Backend setup

```bash
cd regex_replacer/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

### Environment variables

- `DJANGO_SECRET_KEY` - Django secret
- `DJANGO_DEBUG` - `1` for local development
- `OPENAI_API_KEY` - enables live LLM regex generation
- `OPENAI_MODEL` - optional model name, defaults to `gpt-4.1-mini`
- `FRONTEND_ORIGIN` - optional allowed origin for the React dev server

If `OPENAI_API_KEY` is not set, the backend falls back to a deterministic regex catalog so the app still works locally.

## Frontend setup

```bash
cd regex_replacer/frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://127.0.0.1:8000`.

## API

- `POST /api/upload/`
- `POST /api/process/`
- `GET /api/uploads/<id>/`
- `GET /api/uploads/<id>/download/`

## Notes

- The app auto-detects likely text columns, but you can override the target columns in the UI.
- The backend stores uploads and processed files on disk for repeatable processing.
- A second transformation mode, `mask`, is included as a small creative extension alongside standard replacement.

## Demo video

Embed your demo video URL here after recording:

```md
[Watch the demo](https://your-video-link.example)
```

## Deployment

The repo now includes a `render.yaml` blueprint for a single Render web service that serves the built React app from Django.

### Render setup

1. Create a new web service on Render and connect this GitHub repo.
2. Use the included `render.yaml` blueprint or the equivalent manual settings.
3. Deploy the `main` branch.
4. After the first deploy, Render will give you a permanent public URL.

The app is configured to build the frontend into `backend/frontend_build`, run Django behind Gunicorn, and serve the UI and API from one permanent origin.
