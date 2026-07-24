from fastapi.testclient import TestClient

from app.api.main import app
from app.services import signalwatch_service

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_and_company_event_endpoints(monkeypatch) -> None:
    signalwatch_service.reset_state()

    sample_raw_records = [
        {
            "event_id": "EVT-1",
            "company_name": "Acme Corp",
            "category": "financial",
            "severity": "4",
            "confidence": "0.9",
            "published_at": "2026-07-20T10:30:00Z",
            "country": "USA",
            "source": "CSV",
            "description": "Quarterly results fell short.",
        },
        {
            "event_id": "EVT-2",
            "company_name": "Globex Ltd",
            "category": "leadership",
            "severity": "3",
            "confidence": "0.6",
            "published_at": "2026-07-10T10:30:00Z",
            "country": "UK",
            "source": "API",
            "description": "Leadership change announced.",
        },
    ]

    sample_valid_records = [
        {
            "company_name": "Acme Corp",
            "category": "financial",
            "severity": 4,
            "confidence": 0.9,
            "published_at": "2026-07-20T10:30:00Z",
            "country": "United States",
            "source": "CSV",
            "description": "Quarterly results fell short.",
        },
        {
            "company_name": "Globex Ltd",
            "category": "leadership",
            "severity": 3,
            "confidence": 0.6,
            "published_at": "2026-07-10T10:30:00Z",
            "country": "United Kingdom",
            "source": "API",
            "description": "Leadership change announced.",
        },
    ]

    sample_unique_records = sample_valid_records.copy()
    sample_company_results = [
        {
            "company_name": "Acme Corp",
            "company_risk_score": 83.5,
            "risk_level": "HIGH",
        },
        {
            "company_name": "Globex Ltd",
            "company_risk_score": 34.2,
            "risk_level": "LOW",
        },
    ]

    monkeypatch.setattr(signalwatch_service, "ingest_raw_records", lambda: (sample_raw_records, {"combined_records": 2}))
    monkeypatch.setattr(signalwatch_service, "validate_and_normalize_records", lambda records: (sample_valid_records, []))
    monkeypatch.setattr(signalwatch_service, "deduplicate_records", lambda records: (sample_unique_records, []))
    monkeypatch.setattr(signalwatch_service, "process_risk_scores", lambda records, as_of_date=None, output_path=None: sample_company_results)

    ingest_response = client.post("/ingest")
    assert ingest_response.status_code == 200
    assert ingest_response.json()["status"] == "completed"
    assert ingest_response.json()["received_records"] == 2
    assert ingest_response.json()["companies_processed"] == 2

    companies_response = client.get("/companies?risk_level=HIGH&country=United%20States&minimum_score=80&limit=1")
    assert companies_response.status_code == 200
    assert len(companies_response.json()) == 1
    assert companies_response.json()[0]["company_name"] == "Acme Corp"

    company_detail_response = client.get("/companies/Acme%20Corp")
    assert company_detail_response.status_code == 200
    assert company_detail_response.json()["company_name"] == "Acme Corp"
    assert company_detail_response.json()["risk_level"] == "HIGH"
    assert company_detail_response.json()["event_count"] == 1

    events_response = client.get("/events?country=United%20States&category=financial&limit=1")
    assert events_response.status_code == 200
    assert len(events_response.json()) == 1
    assert events_response.json()[0]["company_name"] == "Acme Corp"
