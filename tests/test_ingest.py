from unittest.mock import patch

from app.ingestion.ingest import ingest_raw_records


def test_ingest_raw_records_combines_csv_and_api_records() -> None:
    csv_records = [{"event_id": "CSV-1"}, {"event_id": "CSV-2"}]
    api_records = [{"event_id": "API-1"}, {"event_id": "API-2"}, {"event_id": "API-3"}]

    with patch("app.ingestion.ingest.load_events_csv", return_value=csv_records), patch(
        "app.ingestion.ingest.fetch_events_from_api", return_value=api_records
    ):
        combined_records, counts = ingest_raw_records()

    assert combined_records == [*csv_records, *api_records]
    assert counts == {
        "csv_records": 2,
        "api_records": 3,
        "combined_records": 5,
    }
