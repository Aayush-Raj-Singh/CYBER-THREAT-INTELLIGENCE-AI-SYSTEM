# Cyber Threat Intelligence (CTI) AI System - Indian Cyberspace Focus

Industry-grade, blue-team focused CTI pipeline that ingests OSINT, normalizes text, extracts IOCs, applies interpretable ML, correlates campaigns, scores severity, and produces reports. Includes a local-only API + UI dashboard.

## Features
- OSINT ingestion (RSS, HTML, JSON APIs, local exports)
- Preprocessing (noise removal, language detection, tokenization)
- IOC extraction (IP, domain, URL, email, hashes)
- ML analysis (TF-IDF + Logistic Regression with keyword fallback)
- Threat correlation (IOC reuse, temporal windows, campaign detection, MITRE mapping)
- Severity scoring and confidence
- SQLite storage + JSON reports
- Local API + UI dashboard (no paid services)

## Quick Start (Local, Free)
### 1) Install Python + dependencies
```powershell
py -m ensurepip --upgrade
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### 2) Configure OSINT sources
Edit `config/example.yaml` and replace placeholder URLs with real, policy-compliant public sources.

### 3) Run the pipeline
```powershell
py scripts/run_pipeline.py --config config/example.yaml
```

### 4) Start API + UI
```powershell
py scripts/run_api.py --config config/example.yaml
```
Open `http://127.0.0.1:8000/ui`

## Project Structure
```
config/            # YAML configs
src/cti/           # Pipeline modules
scripts/           # Run + training scripts
data/              # JSONL outputs + SQLite DB
reports/           # Report outputs
web-react/         # React + Tailwind UI
```

## Pipeline Stages
1. Ingestion
2. Preprocessing
3. IOC Extraction
4. ML Analysis
5. Correlation
6. Scoring
7. Storage
8. Reporting

## Notes on Ethics & Safety
- OSINT-only. No credential harvesting, no access control bypass.
- Use public sources and respect robots/rate limits and platform ToS.
- The system is analyst-assist, not autonomous decision-making.

## Frontend (React + Tailwind)
### 1) Install Node.js (LTS)
Use the official Node.js installer for your OS.

### 2) Install frontend dependencies
```powershell
cd web-react
npm install
```

### 3) Run the React UI in dev mode
```powershell
npm run dev
```
Open the URL shown in the terminal. The dev server proxies `/api` to `http://127.0.0.1:8000`.

### 4) Build the UI for FastAPI
```powershell
npm run build
```
Then run the API:
```powershell
py scripts/run_api.py --config config/example.yaml
```
Open `http://127.0.0.1:8000/ui`

## Training Models (Optional)
Use labeled data to train models, or rely on keyword fallback.
```powershell
py scripts/train_models.py --input data/incident_train.csv --text-field text --label-field label --model-type incident --output models/incident_classifier.joblib
```

## Create Labeled Data (Starter Workflow)
If you don't have labels yet, generate a CSV from your ingested data and label it.

1) Run the pipeline once to create `data/normalized_events.jsonl`:
```powershell
py scripts/run_pipeline.py --config config/example.yaml
```

2) Create a labeling CSV (optionally pre-filled with keyword hints):
```powershell
py scripts/prepare_labels.py --config config/example.yaml --auto
```

3) Open `data/labels/training_labels.csv` and fill `incident_label` and `sector_label`.

4) Train models:
```powershell
py scripts/train_models.py --input data/labels/training_labels.csv --text-field text --label-field incident_label --model-type incident --output models/incident_classifier.joblib
py scripts/train_models.py --input data/labels/training_labels.csv --text-field text --label-field sector_label --model-type sector --output models/sector_classifier.joblib
```

## Auto-Train (No Manual Labels)
If you don't want manual labeling, you can generate weak labels from keyword rules and auto-train models.
This is fast but less accurate, and should be treated as a baseline.

```powershell
py scripts/auto_train.py --config config/example.yaml
```

The models will be saved to the paths in `ml.incident_classifier.model_path` and
`ml.sector_classifier.model_path` if enough weak labels exist.

Weak labels are improved using:
- Keyword rules in `ml.weak_labeling.incident_keywords`
- Sector keywords in `ml.weak_labeling.sector_keywords`
- Source domain hints in `ml.weak_labeling.source_domain_map`

## API Endpoints
- `GET /api/health`
- `GET /api/summary`
- `GET /api/events`
- `GET /api/events/{event_id}`
- `GET /api/iocs`
- `GET /api/campaigns`
- `GET /api/reports/latest`

## License
Choose a license that fits your distribution goals (e.g., MIT) before public release.
