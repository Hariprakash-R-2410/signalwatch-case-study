# SignalWatch

SignalWatch is a small Python data pipeline for ingesting event records from a CSV file and a mock REST API, validating and normalizing them, deduplicating them, scoring company risk, and exposing the results through a FastAPI service.

## 1. Architecture overview and data flow

The implementation is split into three layers:

- Ingestion layer: reads the CSV and calls the mock API.
- Processing layer: validates/normalizes records, removes duplicates, and computes company-level risk scores.
- API layer: exposes the processed results over HTTP.

The main data flow is:

1. Ingest raw events from the CSV and API.
2. Validate and normalize each record.
3. Deduplicate the normalized records.
4. Calculate per-company risk scores.
5. Store the latest run in memory for subsequent GET requests.

### Key modules

- [app/ingestion/csv_loader.py](app/ingestion/csv_loader.py): loads the CSV file using Python's standard library CSV reader.
- [app/ingestion/api_client.py](app/ingestion/api_client.py): fetches paginated results from the mock API and skips failed pages.
- [app/ingestion/ingest.py](app/ingestion/ingest.py): orchestrates the ingestion step.
- [app/processing/validation.py](app/processing/validation.py): validates and normalizes the raw records.
- [app/processing/deduplication.py](app/processing/deduplication.py): removes duplicates using normalized identity fields.
- [app/processing/pyspark_processor.py](app/processing/pyspark_processor.py): computes company-level risk scores using Spark when available and a pure-Python fallback otherwise.
- [app/services/signalwatch_service.py](app/services/signalwatch_service.py): keeps the latest pipeline results in memory and serves the API layer.
- [app/api/main.py](app/api/main.py): defines the FastAPI routes.

## 2. Validation and normalization rules

The validation layer is implemented in [app/processing/validation.py](app/processing/validation.py).

### Normalization behavior

- Company names are trimmed, collapsed to single spaces, trailing commas are removed, and some common suffix variants are normalized.
- Categories are mapped to the canonical values used by the assignment:
  - cybersecurity
  - legal_regulatory
  - financial
  - supply_chain
  - leadership
  - fraud_reputation
- Countries are mapped to canonical country names where possible.
- Dates are parsed from several supported formats and normalized to an ISO-like string.
- Severity values are converted to integers between 1 and 5.
- Confidence values are converted to floats between 0 and 1.

### Validation rules

A record is rejected if any of the following fail:

- company name is missing or empty
- category is unknown after normalization
- severity is not a valid integer between 1 and 5
- confidence is not a valid float between 0 and 1
- published date cannot be parsed

Rejected records are not silently dropped; they are collected separately and reported in the ingest summary.

## 3. Deduplication strategy

Deduplication is implemented in [app/processing/deduplication.py](app/processing/deduplication.py).

The duplicate key is built from:

- normalized company name
- normalized category
- normalized description

The first occurrence is preserved and later matches are treated as duplicates. This matches the case-study requirement to avoid relying on event_id as the sole deduplication signal.

## 4. Risk scoring formula and aggregation logic

Risk scoring is implemented in [app/processing/pyspark_processor.py](app/processing/pyspark_processor.py).

### Event score formula

For each valid event, the implementation calculates:

- severity $\times 20 \times confidence \times recency\_weight$
- the result is capped at 100
- the value is rounded to two decimals

### Recency weighting

The recency weight is based on the age of the event:

- 7 days or fewer: $1.0$
- between 8 and 30 days: $0.8$
- older than 30 days: $0.6$

### Company aggregation

Company risk is computed by taking the top five event scores for that company (or all scores if fewer than five are present), averaging them, rounding to two decimals, and assigning a risk level:

- $\leq 39.99$: LOW
- $\leq 69.99$: MEDIUM
- otherwise: HIGH

The processor supports Spark when available and falls back to pure Python when PySpark is not installed.

## 5. API endpoints with example requests

The HTTP layer is implemented in [app/api/main.py](app/api/main.py).

### Endpoints

- GET /health
- POST /ingest
- GET /companies
- GET /companies/{company_name}
- GET /events

### Example requests

#### GET /health

```bash
curl http://127.0.0.1:8000/health
```

#### POST /ingest

```bash
curl -X POST http://127.0.0.1:8000/ingest
```

Example response shape:

```json
{
  "status": "completed",
  "received_records": 150,
  "valid_records": 132,
  "rejected_records": 8,
  "duplicate_records": 10,
  "companies_processed": 24
}
```

The actual values depend on the current data sources and any API fetch failures.

#### GET /companies

```bash
curl "http://127.0.0.1:8000/companies?risk_level=HIGH&country=United%20States&minimum_score=80&limit=10"
```

#### GET /companies/{company_name}

```bash
curl "http://127.0.0.1:8000/companies/Acme%20Corp"
```

#### GET /events

```bash
curl "http://127.0.0.1:8000/events?country=United%20States&category=financial&limit=10"
```

## 6. Testing strategy and how to run tests

The project uses pytest for unit and integration coverage.

### Current tests

- ingestion and CSV loading tests
- validation tests
- deduplication tests
- processor tests
- pipeline integration tests
- API endpoint tests

### Run the test suite

```bash
python -m pytest -q
```

### Run the API tests only

```bash
python -m pytest -q tests/test_api.py
```

## 7. How to run the project locally

### Prerequisites

- Python 3.10+
- A local copy of the project repository

### Install dependencies

```bash
pip install fastapi uvicorn pytest httpx
```

### Start the API locally

```bash
uvicorn app.api.main:app --reload
```

The API will be available at:

- http://127.0.0.1:8000/health

### Run the mock API (optional)

The case-study package includes a mock API that can be used for the ingestion step:

```bash
python signalwatch-case-study/signalwatch-case-study/mock_api.py
```

If the mock API is not running, the ingestion step will still read the CSV file, but the API source will be empty for that run.

## 8. Limitations and optional features not implemented

The current implementation intentionally keeps the scope focused on the required assignment behavior.

### Current limitations

- The API keeps the latest run in memory only; it does not persist results to disk or a database.
- The API does not implement authentication or user management.
- The output is not written to disk by default; CSV export happens only when an explicit output path is passed to the processor.
- No NumPy or Matplotlib has been added.
- The project does not yet include a formal README-based deployment or container setup.

### Optional features not implemented here

- persistent storage for pipeline results
- background job execution for ingest runs
- dashboards or charts
- richer error reporting or reject-file export

## 9. AI tools used and how they were used

The project was implemented with AI assistance in VS Code using GitHub Copilot.

The AI assistance was used for:

- scaffolding the package structure and module layout
- implementing the ingestion, validation, deduplication, and scoring functions
- drafting the FastAPI routes and service layer
- writing pytest coverage for the pipeline and API endpoints

## Project structure

```text
SignalWatch/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   ├── csv_loader.py
│   │   └── ingest.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── deduplication.py
│   │   ├── pyspark_processor.py
│   │   └── validation.py
│   └── services/
│       ├── __init__.py
│       └── signalwatch_service.py
├── outputs/
├── signalwatch-case-study/
│   └── signalwatch-case-study/
│       ├── DATA_DICTIONARY.md
│       ├── events.csv
│       ├── events_api.json
│       └── mock_api.py
├── tests/
│   ├── test_api.py
│   ├── test_csv_loader.py
│   ├── test_deduplication.py
│   ├── test_deduplication_module.py
│   ├── test_ingest.py
│   ├── test_pipeline_integration.py
│   ├── test_pyspark_processor.py
│   ├── test_validation.py
│   └── test_validation_module.py
└── README.md
```

## Required dependencies

The implementation uses:

- Python standard library modules
- FastAPI
- Uvicorn
- pytest
- httpx

PySpark is optional. If it is installed, the scoring module uses it; otherwise the same logic runs in pure Python.

## Output files generated

By default, the current API flow does not write any files to the repository. The processor only writes a CSV output when an explicit output path is supplied to the risk-scoring function.

If an output path is provided, the generated CSV includes:

- company_name
- company_risk_score
- risk_level

## Assumptions

- The API uses an in-memory cache for the latest successful pipeline run.
- The pipeline uses the current date as the scoring as-of date unless an explicit date is provided.
- If the mock API is unavailable, the ingestion run continues using the CSV data and any successfully fetched API pages.
- The service layer is intended to be simple and follows the assignment requirements rather than adding extra infrastructure.
