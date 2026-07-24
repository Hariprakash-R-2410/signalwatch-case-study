from app.processing.deduplication import deduplicate_records


def test_deduplicate_records_preserves_first_occurrence() -> None:
    records = [
        {
            "company_name": "Cobalt Financial Group",
            "category": "financial",
            "description": "Quarterly results fell short.",
        },
        {
            "company_name": "cobalt financial group",
            "category": "Financial",
            "description": "Quarterly results fell short.",
        },
        {
            "company_name": "Another Company",
            "category": "leadership",
            "description": "Leadership change announced.",
        },
    ]

    unique_records, duplicate_records = deduplicate_records(records)

    assert len(unique_records) == 2
    assert len(duplicate_records) == 1
    assert unique_records[0]["company_name"] == "Cobalt Financial Group"
    assert duplicate_records[0]["duplicate_key"] == (
        "cobalt financial group",
        "financial",
        "quarterly results fell short.",
    )
