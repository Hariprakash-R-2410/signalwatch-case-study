from app.processing.validation import validate_and_normalize_records


def test_valid_record_is_normalized_and_accepted() -> None:
    record = {
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

    valid_records, rejected_records = validate_and_normalize_records([record])

    assert len(valid_records) == 1
    assert len(rejected_records) == 0
    assert valid_records[0]["company_name"] == "Cobalt Financial Group"
    assert valid_records[0]["category"] == "financial"
    assert valid_records[0]["severity"] == 4
    assert valid_records[0]["confidence"] == 0.85
    assert valid_records[0]["country"] == "United States"
    assert valid_records[0]["published_at"] == "2026-07-20T10:30:00Z"


def test_blank_company_name_is_rejected() -> None:
    record = {
        "event_id": "EVT-2",
        "company_name": "",
        "category": "cybersecurity",
        "severity": "3",
        "confidence": "0.6",
        "published_at": "2026-07-20T10:30:00Z",
    }

    valid_records, rejected_records = validate_and_normalize_records([record])

    assert valid_records == []
    assert len(rejected_records) == 1
    assert rejected_records[0]["reason"] == "missing company name"


def test_invalid_severity_is_rejected() -> None:
    record = {
        "event_id": "EVT-3",
        "company_name": "Example Corp",
        "category": "leadership",
        "severity": "7",
        "confidence": "0.4",
        "published_at": "2026-07-20T10:30:00Z",
    }

    valid_records, rejected_records = validate_and_normalize_records([record])

    assert valid_records == []
    assert len(rejected_records) == 1
    assert rejected_records[0]["reason"] == "invalid severity"


def test_invalid_confidence_is_rejected() -> None:
    record = {
        "event_id": "EVT-4",
        "company_name": "Example Corp",
        "category": "supply_chain",
        "severity": "2",
        "confidence": "1.4",
        "published_at": "2026-07-20T10:30:00Z",
    }

    valid_records, rejected_records = validate_and_normalize_records([record])

    assert valid_records == []
    assert len(rejected_records) == 1
    assert rejected_records[0]["reason"] == "invalid confidence"


def test_invalid_date_is_rejected() -> None:
    record = {
        "event_id": "EVT-5",
        "company_name": "Example Corp",
        "category": "financial",
        "severity": "3",
        "confidence": "0.3",
        "published_at": "not-a-date",
    }

    valid_records, rejected_records = validate_and_normalize_records([record])

    assert valid_records == []
    assert len(rejected_records) == 1
    assert rejected_records[0]["reason"] == "invalid published date"


def test_low_confidence_but_valid_record_is_accepted() -> None:
    record = {
        "event_id": "EVT-6",
        "company_name": "Example Corp",
        "category": "legal_regulatory",
        "severity": "2",
        "confidence": "0.05",
        "published_at": "03 Jul 2026",
    }

    valid_records, rejected_records = validate_and_normalize_records([record])

    assert len(valid_records) == 1
    assert len(rejected_records) == 0
    assert valid_records[0]["confidence"] == 0.05
    assert valid_records[0]["published_at"] == "2026-07-03T00:00:00Z"
