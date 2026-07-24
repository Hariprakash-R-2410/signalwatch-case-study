from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ingestion.ingest import ingest_raw_records
from app.processing.deduplication import deduplicate_records
from app.processing.pyspark_processor import process_risk_scores
from app.processing.validation import validate_and_normalize_records


@dataclass
class SignalWatchService:
    latest_summary: Optional[Dict[str, Any]] = None
    latest_events: List[Dict[str, Any]] = field(default_factory=list)
    latest_companies: List[Dict[str, Any]] = field(default_factory=list)

    def run_pipeline(self) -> Dict[str, Any]:
        raw_records, counts = ingest_raw_records()
        valid_records, rejected_records = validate_and_normalize_records(raw_records)
        unique_records, duplicate_records = deduplicate_records(valid_records)
        company_results = process_risk_scores(unique_records)

        self.latest_events = unique_records
        self.latest_companies = self._build_company_summaries(unique_records, company_results)

        summary = {
            "status": "completed",
            "received_records": counts.get("combined_records", 0),
            "valid_records": len(valid_records),
            "rejected_records": len(rejected_records),
            "duplicate_records": len(duplicate_records),
            "companies_processed": len(self.latest_companies),
        }
        self.latest_summary = summary
        return summary

    def get_companies(
        self,
        risk_level: Optional[str] = None,
        country: Optional[str] = None,
        minimum_score: Optional[float] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if not self.latest_companies:
            self.run_pipeline()

        filtered = self.latest_companies
        if risk_level:
            filtered = [company for company in filtered if company.get("risk_level") == risk_level.upper()]
        if country:
            filtered = [company for company in filtered if str(company.get("country") or "").lower() == country.lower()]
        if minimum_score is not None:
            filtered = [company for company in filtered if company.get("company_risk_score", 0.0) >= minimum_score]

        if not filtered:
            return []

        filtered = sorted(
            filtered,
            key=lambda item: item.get("company_risk_score", 0.0),
            reverse=True,
        )[:limit]
        return filtered

    def get_company_detail(self, company_name: str) -> Dict[str, Any]:
        if not self.latest_companies:
            self.run_pipeline()

        matching = next((company for company in self.latest_companies if str(company.get("company_name", "")).lower() == company_name.lower()), None)
        if matching is None:
            raise KeyError(company_name)

        return {
            "company_name": matching.get("company_name"),
            "risk_score": matching.get("company_risk_score"),
            "risk_level": matching.get("risk_level"),
            "event_count": matching.get("event_count", 0),
            "top_categories": matching.get("top_categories", []),
        }

    def get_events(self, country: Optional[str] = None, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.latest_events:
            self.run_pipeline()

        filtered = self.latest_events
        if country:
            filtered = [event for event in filtered if str(event.get("country", "")).lower() == country.lower()]
        if category:
            filtered = [event for event in filtered if str(event.get("category", "")).lower() == category.lower()]

        filtered = filtered[:limit]
        return filtered

    def _build_company_summaries(self, events: List[Dict[str, Any]], company_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        company_buckets: Dict[str, Dict[str, Any]] = {}

        for event in events:
            company_name = str(event.get("company_name", "")).strip()
            if not company_name:
                continue

            bucket = company_buckets.setdefault(
                company_name,
                {
                    "company_name": company_name,
                    "country": None,
                    "event_count": 0,
                    "categories": Counter(),
                },
            )
            bucket["event_count"] += 1

            country = str(event.get("country") or "").strip()
            if country and bucket["country"] is None:
                bucket["country"] = country

            category = str(event.get("category") or "").strip()
            if category:
                bucket["categories"][category] += 1

        summaries: List[Dict[str, Any]] = []
        for company in company_results:
            company_name = str(company.get("company_name", "")).strip()
            if not company_name:
                continue

            bucket = company_buckets.get(company_name, {})
            top_categories = [
                {"category": category, "count": count}
                for category, count in bucket.get("categories", Counter()).most_common(3)
            ]
            summaries.append(
                {
                    "company_name": company_name,
                    "company_risk_score": company.get("company_risk_score"),
                    "risk_level": company.get("risk_level"),
                    "country": bucket.get("country"),
                    "event_count": bucket.get("event_count", 0),
                    "top_categories": top_categories,
                }
            )

        return sorted(summaries, key=lambda item: str(item.get("company_name", "")).lower())

    def reset_state(self) -> None:
        self.latest_summary = None
        self.latest_events = []
        self.latest_companies = []


service = SignalWatchService()


def reset_state() -> None:
    service.reset_state()
