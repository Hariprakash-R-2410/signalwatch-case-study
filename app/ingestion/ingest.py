from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.ingestion.api_client import fetch_events_from_api
from app.ingestion.csv_loader import load_events_csv


def ingest_raw_records() -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Load raw records from the CSV and the mock API and combine them.

    This function is intentionally limited to orchestration. It does not perform
    validation, normalization, deduplication, or scoring.
    """
    csv_records = load_events_csv()
    api_records = fetch_events_from_api()

    combined_records = [*csv_records, *api_records]

    counts = {
        "csv_records": len(csv_records),
        "api_records": len(api_records),
        "combined_records": len(combined_records),
    }

    return combined_records, counts
