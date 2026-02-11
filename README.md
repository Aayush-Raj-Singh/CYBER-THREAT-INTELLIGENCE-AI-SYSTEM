# Cyber Threat Intelligence AI System (India Focus)

A production-style, blue-team Cyber Threat Intelligence system that ingests open-source sources, normalizes and analyzes text, extracts Indicators of Compromise, correlates campaigns, scores severity and confidence, and serves a professional analyst UI with a built-in theory/reference section.

This repository includes:
- End-to-end CTI pipeline (ingestion - reporting)
- Local FastAPI service with SQLite storage
- React + Tailwind dashboard and documentation UI
- Photographic SOC / data?center / threat-map imagery integrated into the documentation section

---

## Key Capabilities

Pipeline
- Multi-source ingestion (RSS, HTML, JSON APIs, text feeds)
- Preprocessing: noise removal, language detection, tokenization
- Indicators of Compromise extraction (IP, domain, URL, hashes, email)
- Analysis: incident type, sector, confidence, clustering
- Correlation: shared indicators, temporal proximity, campaign grouping
- Scoring: severity + confidence with transparent rationale
- Reporting: JSON report + summary artifacts
- Storage: SQLite (default) with deduped indicators

API + UI
- FastAPI endpoints for health, summary, events, indicators, campaigns, reports
- React dashboard with neon/glass SOC styling
- Dark and light themes
- Event Intelligence and Indicators of Compromise Explorer with pagination and sorting
- Latest report summary rendered as analyst-friendly bullet points
- Intelligence Docs route with structured theory and real photographic assets

---

## Tech Stack

Backend
- Python 3.10+ (recommended)
- FastAPI + Uvicorn
- SQLAlchemy
- scikit-learn, pandas, numpy

Frontend
- React 18 + React Router
- Vite
- Tailwind CSS

---

## Project Layout

```
config/                 # YAML configuration
src/cti/                # Pipeline + API source
scripts/                # CLI scripts
migrations/             # DB migrations
data/                   # JSONL outputs + SQLite DB
reports/                # JSON report outputs
web-react/              # React + Tailwind UI
web/                    # Legacy static UI (not used)
```

---

## Live Demo

UI: https://cti-portal.pages.dev

---

## Quick Start (Local)

### 1) Install Python dependencies
```powershell
py -m ensurepip --upgrade
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### 2) Configure sources
Edit `config/example.yaml` and replace placeholder URLs with policy-compliant sources.

### 3) Run the pipeline
```powershell
py scripts/run_pipeline.py --config config/example.yaml
```

### 4) Start the API
```powershell
py scripts/run_api.py --config config/example.yaml
```
Open `http://127.0.0.1:8000/ui` after building the UI (see Frontend section below).

---

## Frontend (React + Tailwind)

### Install Node dependencies
```powershell
cd web-react
npm install
```

### Run in dev mode
```powershell
npm run dev
```
Open the URL shown by Vite (default `http://127.0.0.1:5173`).

### Build for the API (`/ui`)
```powershell
npm run build
```
Then run the API and open `http://127.0.0.1:8000/ui`.

### Deploy to GitHub Pages
This is a static build (no backend). The UI will show `API offline` unless you
also run the API locally.

```powershell
cd web-react
npm run build:pages
```

Then in GitHub:
1. Go to repository **Settings → Pages**
2. Set Source to `main` branch, folder `/docs`
3. Save and wait for the Pages URL to go live

Notes:
- Routes like `/intelligence-docs` are supported via the generated `404.html`.
- Static builds use the base path `/CYBER-THREAT-INTELLIGENCE-AI-SYSTEM/`.

### API base path
- Dev mode: proxied to `http://127.0.0.1:8000`
- Production build: Vite base is `/ui/`
- Optional override: set `VITE_API_BASE` to point the UI to another API host
- Example template: `web-react/.env.example`
- Local production override: create `web-react/.env.production`

---

## Production Deployment (Cloud Run + Cloudflare Pages)

This setup serves live data from Cloud Run and a static UI from Cloudflare Pages.

### 1) Backend (Cloud Run)
1. Build and deploy:
   ```powershell
   cd C:\Users\aayus\OneDrive\Desktop\cyber-threat-intelligence
   gcloud builds submit --tag asia-south1-docker.pkg.dev/cti-ui2026/cti-api/cti-api:latest
   gcloud run deploy cti-api --image asia-south1-docker.pkg.dev/cti-ui2026/cti-api/cti-api:latest --region asia-south1 --allow-unauthenticated
   ```
2. Set env vars so the API reads the latest pipeline outputs:
   - `GCS_BUCKET=cti-ui2026-cti-data`
   - `GCS_PREFIX=latest`

### 2) Frontend (Cloudflare Pages)
1. Create `web-react/.env.production`:
   ```
   VITE_API_BASE=https://YOUR-CLOUD-RUN-URL
   ```
2. Build and deploy:
   ```powershell
   cd web-react
   npm run build -- --base=/
   npx wrangler pages deploy dist --project-name "cti-portal" --commit-dirty=true
   ```

### 3) CORS
Allow the Pages domain (and previews) in `src/cti/api/app.py`:
```python
allow_origins=[
  "https://cti-portal.pages.dev",
  "https://cyber-threat-intelligence.pages.dev",
  "http://localhost:5173",
],
allow_origin_regex=r"https://.*\.cti-portal\.pages\.dev",
```

---

## Configuration Guide (`config/example.yaml`)

High-value keys to review:
- `project.name`, `project.country_focus`, `project.timezone`
- `ingestion.sources.*`: public advisories, blogs, and threat feeds
- `preprocessing`: text length thresholds, language allow?list
- `ioc_extraction`: minimum confidence threshold
- `ml`: model paths, fallback keywords, weak labeling rules
- `correlation`: temporal window, shared indicator thresholds
- `scoring`: weights and severity thresholds
- `storage.db_url`: SQLite by default
- `reporting.output_json_path`: report output used by the UI

---

## Pipeline Stages and Outputs

1) Ingestion
- Output: `data/raw_events.jsonl`

2) Preprocessing
- Output: `data/normalized_events.jsonl`

3) Indicators of Compromise Extraction
- Output: `data/iocs.jsonl`

4) Analysis
- Output: `data/analysis_results.jsonl`

5) Correlation
- Output: `data/correlation_results.jsonl`, `data/campaigns.jsonl`

6) Scoring
- Output: `data/scores.jsonl`

7) Storage
- SQLite DB: `data/cti.db`

8) Reporting
- JSON report: `reports/report.json`
- Summary text: `reports/summary.txt`

---

## Database and Migrations

A unique constraint prevents duplicate indicators per event.

Run migrations:
```powershell
py scripts/migrate_db.py --config config/example.yaml
```

Deduplicate indicators (SQLite only):
```powershell
py scripts/dedupe_iocs.py --config config/example.yaml
```

---

## API Reference

- `GET /api/health`
- `GET /api/summary`
- `GET /api/events`
  - Query: `severity`, `incident`, `sector`, `limit`, `offset`
- `GET /api/events/{event_id}`
- `GET /api/iocs`
  - Query: `limit`, `offset`
- `GET /api/campaigns`
- `GET /api/reports/latest`

Pagination
- `limit` and `offset` are supported for events and indicators.

---

## UI Reference

Dashboard (`/`)
- Hero: animated title and status
- Metrics: total events, campaigns, indicators
- Event Intelligence
  - Sortable columns
  - Pagination (10, 25, 50, 100)
- Indicators of Compromise Explorer
  - Sortable columns
  - Pagination (10, 25, 50, 100)
- Latest Report
  - Bullet?based summary built from report JSON

Intelligence Docs (`/intelligence-docs`)
- Structured theory content stored as data objects in `web-react/src/data/theory`
- Tabs for Overview, Cyber Threat Intelligence, Indicators of Compromise, Architecture, Artificial Intelligence, Use Cases, Limitations
- Photographic assets stored in `web-react/public/images/theory`

Theme
- Light/dark toggle
- Glass + neon SOC style

---

## Training Models

Train with labeled data:
```powershell
py scripts/train_models.py --input data/incident_train.csv --text-field text --label-field label --model-type incident --output models/incident_classifier.joblib
```

Create labels workflow:
1. Run pipeline to generate normalized data.
2. Generate CSV:
```powershell
py scripts/prepare_labels.py --config config/example.yaml --auto
```
3. Edit `data/labels/training_labels.csv`
4. Train incident and sector models:
```powershell
py scripts/train_models.py --input data/labels/training_labels.csv --text-field text --label-field incident_label --model-type incident --output models/incident_classifier.joblib
py scripts/train_models.py --input data/labels/training_labels.csv --text-field text --label-field sector_label --model-type sector --output models/sector_classifier.joblib
```

Auto-train with weak labels:
```powershell
py scripts/auto_train.py --config config/example.yaml
```

---

## Assets and Licensing

- Photographic assets are stored locally in `web-react/public/images/theory`.
- Images were pulled from public photo sources and should be reviewed for licensing and attribution requirements before public distribution.

---

## Troubleshooting

Common issues
- `ModuleNotFoundError: No module named 'sqlalchemy'`
  - Run `py -m pip install -r requirements.txt`
- UI shows 404 at `/ui`
  - Run `npm run build` inside `web-react/` and restart the API
- API offline in UI
  - Ensure `py scripts/run_api.py --config config/example.yaml` is running

---

## Ethics and Safety

- This system is defensive?only.
- Use public sources and respect rate limits and terms of service.
- Human validation is required before action.

---

## License

See `LICENSE`.
