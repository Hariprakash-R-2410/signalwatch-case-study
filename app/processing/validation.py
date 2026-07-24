from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple


CATEGORY_MAP = {
    "cybersecurity": "cybersecurity",
    "cyber security": "cybersecurity",
    "cyber-security": "cybersecurity",
    "cyber": "cybersecurity",
    "cyber_security": "cybersecurity",
    "legal_regulatory": "legal_regulatory",
    "legal regulatory": "legal_regulatory",
    "legal-regulatory": "legal_regulatory",
    "regulatory": "legal_regulatory",
    "legal": "legal_regulatory",
    "financial": "financial",
    "financial distress": "financial",
    "financial_distress": "financial",
    "finance": "financial",
    "supply_chain": "supply_chain",
    "supply chain": "supply_chain",
    "supply-chain": "supply_chain",
    "supplychain": "supply_chain",
    "leadership": "leadership",
    "leadership_change": "leadership",
    "leadership change": "leadership",
    "management": "leadership",
    "fraud_reputation": "fraud_reputation",
    "fraud reputation": "fraud_reputation",
    "fraud": "fraud_reputation",
    "reputation": "fraud_reputation",
}

COUNTRY_MAP = {
    "usa": "United States",
    "u.s.a.": "United States",
    "us": "United States",
    "united states": "United States",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "aus": "Australia",
    "australia": "Australia",
    "india": "India",
    "germany": "Germany",
    "singapore": "Singapore",
    "japan": "Japan",
    "china": "China",
    "france": "France",
    "italy": "Italy",
    "spain": "Spain",
    "netherlands": "Netherlands",
}


def validate_and_normalize_records(
    records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Normalize valid records and return them separately from rejected ones."""
    valid_records: List[Dict[str, Any]] = []
    rejected_records: List[Dict[str, Any]] = []

    for record in records:
        try:
            normalized = normalize_record(record)
        except ValueError as exc:
            rejected_records.append({"record": record, "reason": str(exc)})
            continue

        valid_records.append(normalized)

    return valid_records, rejected_records


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single record into a consistent dictionary structure."""
    normalized = dict(record)

    company_name = normalize_company_name(record.get("company_name"))
    if not company_name:
        raise ValueError("missing company name")
    normalized["company_name"] = company_name

    category = normalize_category(record.get("category"))
    if not category:
        raise ValueError("invalid category")
    normalized["category"] = category

    severity = normalize_severity(record.get("severity"))
    if severity is None:
        raise ValueError("invalid severity")
    normalized["severity"] = severity

    confidence = normalize_confidence(record.get("confidence"))
    if confidence is None:
        raise ValueError("invalid confidence")
    normalized["confidence"] = confidence

    published_at = normalize_date(record.get("published_at"))
    if not published_at:
        raise ValueError("invalid published date")
    normalized["published_at"] = published_at

    normalized["country"] = normalize_country(record.get("country"))

    return normalized


def normalize_company_name(value: Any) -> str:
    """Trim and standardize company names."""
    if value is None:
        return ""

    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    text = text.rstrip(",")
    text = re.sub(r"\s+Ltd\.", " Ltd.", text)
    text = re.sub(r"\s+Pvt Ltd", " Pvt Ltd", text)
    return text.title() if text else ""


def normalize_country(value: Any) -> str | None:
    """Normalize country values to canonical names where possible."""
    if value is None:
        return None

    text = str(value).strip().lower()
    if not text:
        return None

    return COUNTRY_MAP.get(text, text.title())


def normalize_category(value: Any) -> str | None:
    """Map category variants to the canonical categories."""
    if value is None:
        return None

    text = str(value).strip().lower()
    if not text:
        return None

    return CATEGORY_MAP.get(text)


def normalize_severity(value: Any) -> int | None:
    """Convert severity to an integer between 1 and 5 when valid."""
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        numeric_value = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            numeric_value = int(float(text))
        except ValueError:
            return None

    return numeric_value if 1 <= numeric_value <= 5 else None


def normalize_confidence(value: Any) -> float | None:
    """Convert confidence to a float between 0 and 1 when valid."""
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        numeric_value = float(value)
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            numeric_value = float(text)
        except ValueError:
            return None

    return numeric_value if 0 <= numeric_value <= 1 else None


def normalize_date(value: Any) -> str | None:
    """Parse supported date formats to a consistent ISO-like string."""
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    for date_format in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%d %b %Y",
    ):
        try:
            parsed = datetime.strptime(text, date_format)
            return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    return None
