from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple


def deduplicate_records(
    records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Remove duplicate events using normalized identity fields.

    The duplicate key is built from the normalized company name, category, and
    description. The first occurrence is preserved; later matches are returned as
    duplicates for reporting and debugging.
    """
    unique_records: List[Dict[str, Any]] = []
    duplicate_records: List[Dict[str, Any]] = []
    seen_keys: Set[Tuple[str, str, str]] = set()

    for record in records:
        key = build_duplicate_key(record)
        if key in seen_keys:
            duplicate_records.append(
                {
                    "record": record,
                    "duplicate_key": key,
                }
            )
            continue

        seen_keys.add(key)
        unique_records.append(record)

    return unique_records, duplicate_records


def build_duplicate_key(record: Dict[str, Any]) -> Tuple[str, str, str]:
    """Build a duplicate key from normalized identity fields."""
    company_name = str(record.get("company_name", "")).strip().lower()
    category = str(record.get("category", "")).strip().lower()
    description = str(record.get("description", "")).strip().lower()

    return company_name, category, description
