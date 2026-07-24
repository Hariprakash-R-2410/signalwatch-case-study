from app.processing.validation import validate_and_normalize_records


def test_validate_and_normalize_records_normalizes_valid_rows() -> None:
    records = [
        {
            "event_id": "EVT-1",
            "company_name": "  Cobalt  Financial  Group ",
            "category": "finance",
            "severity": "4",
            "confidence": "0.85",
            "published_at": "2026-07-20 10:30:00",
            "country": "USA",
            "source": "Test",
            "description": "Example",
        }
    ]

    valid_records, rejected_records = validate_and_normalize_records(records)

    assert len(valid_records) == 1
    assert len(rejected_records) == 0
    assert valid_records[0]["company_name"] == "Cobalt Financial Group"
    assert valid_records[0]["category"] == "financial"
    assert valid_records[0]["severity"] == 4
    assert valid_records[0]["confidence"] == 0.85
    assert valid_records[0]["country"] == "United States"
    assert valid_records[0]["published_at"] == "2026-07-20T10:30:00Z"


def test_validate_and_normalize_records_rejects_invalid_rows() -> None:
    records = [
        {
            "event_id": "EVT-2",
            "company_name": "",
            "category": "cybersecurity",
            "severity": "7",
            "confidence": "0.3",
            "published_at": "2026-07-20T10:30:00Z",
            "country": "UK",
            "source": "Test",
            "description": "Bad severity",
        }
    ]

    valid_records, rejected_records = validate_and_normalize_records(records)

    assert valid_records == []
    assert len(rejected_records) == 1
    assert rejected_records[0]["reason"] == "missing company name"
    assert rejected_records[0]["record"]["event_id"] == "EVT-2"
