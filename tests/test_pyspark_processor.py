from datetime import date

from app.processing.pyspark_processor import process_risk_scores


def test_process_risk_scores_calculates_event_and_company_scores() -> None:
    records = [
        {
            "company_name": "Example Corp",
            "category": "financial",
            "severity": 5,
            "confidence": 0.9,
            "published_at": "2026-07-20T10:30:00Z",
            "country": "United States",
            "source": "Test",
            "description": "First event",
        },
        {
            "company_name": "Example Corp",
            "category": "leadership",
            "severity": 3,
            "confidence": 0.8,
            "published_at": "2026-07-10T10:30:00Z",
            "country": "United States",
            "source": "Test",
            "description": "Second event",
        },
        {
            "company_name": "Example Corp",
            "category": "cybersecurity",
            "severity": 2,
            "confidence": 0.7,
            "published_at": "2026-06-10T10:30:00Z",
            "country": "United States",
            "source": "Test",
            "description": "Third event",
        },
        {
            "company_name": "Example Corp",
            "category": "legal_regulatory",
            "severity": 1,
            "confidence": 0.5,
            "published_at": "2026-05-10T10:30:00Z",
            "country": "United States",
            "source": "Test",
            "description": "Fourth event",
        },
        {
            "company_name": "Example Corp",
            "category": "supply_chain",
            "severity": 4,
            "confidence": 0.6,
            "published_at": "2026-04-10T10:30:00Z",
            "country": "United States",
            "source": "Test",
            "description": "Fifth event",
        },
        {
            "company_name": "Another Corp",
            "category": "fraud_reputation",
            "severity": 3,
            "confidence": 0.4,
            "published_at": "2026-07-20T10:30:00Z",
            "country": "United States",
            "source": "Test",
            "description": "Sixth event",
        },
    ]

    results = process_risk_scores(records, as_of_date=date(2026, 7, 25))

    assert len(results) == 2
    assert any(result["company_name"] == "Example Corp" for result in results)
    assert any(result["company_name"] == "Another Corp" for result in results)
    example_result = next(result for result in results if result["company_name"] == "Example Corp")
    assert example_result["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(example_result["company_risk_score"], float)
