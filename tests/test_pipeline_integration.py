from pathlib import Path
from unittest.mock import patch

from app.ingestion.ingest import ingest_raw_records
from app.processing.deduplication import deduplicate_records
from app.processing.pyspark_processor import process_risk_scores
from app.processing.validation import validate_and_normalize_records


def test_pipeline_integration_combines_sources_and_produces_company_results() -> None:
    csv_records = [
        {
            "event_id": "CSV-1",
            "company_name": "  Cobalt  Financial  Group ",
            "category": "finance",
            "severity": "4",
            "confidence": "0.85",
            "published_at": "2026-07-20 10:30:00",
            "country": "USA",
            "source": "CSV",
            "description": "Quarterly results fell short.",
        }
    ]
    api_records = [
        {
            "event_id": "API-1",
            "company_name": "COBALT FINANCIAL GROUP",
            "category": "Financial Distress",
            "severity": "4",
            "confidence": "0.9",
            "published_at": "2026-07-20T10:30:00Z",
            "country": "uk",
            "source": "API",
            "description": "Quarterly results fell short.",
        },
        {
            "event_id": "API-2",
            "company_name": "Example Corp",
            "category": "leadership",
            "severity": "3",
            "confidence": "0.6",
            "published_at": "2026-07-20T10:30:00Z",
            "country": "Singapore",
            "source": "API",
            "description": "Leadership change announced.",
        },
    ]

    with patch("app.ingestion.ingest.load_events_csv", return_value=csv_records), patch(
        "app.ingestion.ingest.fetch_events_from_api", return_value=api_records
    ):
        raw_records, counts = ingest_raw_records()

    valid_records, rejected_records = validate_and_normalize_records(raw_records)
    unique_records, duplicate_records = deduplicate_records(valid_records)
    company_results = process_risk_scores(unique_records)

    assert counts["combined_records"] == 3
    assert len(rejected_records) == 0
    assert len(unique_records) == 2
    assert len(duplicate_records) == 1
    assert any(result["company_name"] == "Cobalt Financial Group" for result in company_results)
    assert any(result["company_name"] == "Example Corp" for result in company_results)
