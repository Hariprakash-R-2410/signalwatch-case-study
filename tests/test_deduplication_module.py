from app.processing.deduplication import deduplicate_records


def test_identical_normalized_records_create_one_unique_and_one_duplicate() -> None:
    records = [
        {
            "company_name": "Cobalt Financial Group",
            "category": "financial",
            "description": "Quarterly results fell short.",
        },
        {
            "company_name": "Cobalt Financial Group",
            "category": "financial",
            "description": "Quarterly results fell short.",
        },
    ]

    unique_records, duplicate_records = deduplicate_records(records)

    assert len(unique_records) == 1
    assert len(duplicate_records) == 1
    assert unique_records[0]["company_name"] == "Cobalt Financial Group"
    assert duplicate_records[0]["duplicate_key"] == (
        "cobalt financial group",
        "financial",
        "quarterly results fell short.",
    )


def test_normalized_formatting_differences_are_treated_as_duplicates() -> None:
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
    ]

    unique_records, duplicate_records = deduplicate_records(records)

    assert len(unique_records) == 1
    assert len(duplicate_records) == 1


def test_different_company_category_or_description_are_not_duplicates() -> None:
    records = [
        {
            "company_name": "Cobalt Financial Group",
            "category": "financial",
            "description": "Quarterly results fell short.",
        },
        {
            "company_name": "Another Company",
            "category": "financial",
            "description": "Quarterly results fell short.",
        },
        {
            "company_name": "Cobalt Financial Group",
            "category": "leadership",
            "description": "Quarterly results fell short.",
        },
        {
            "company_name": "Cobalt Financial Group",
            "category": "financial",
            "description": "Different description.",
        },
    ]

    unique_records, duplicate_records = deduplicate_records(records)

    assert len(unique_records) == 4
    assert len(duplicate_records) == 0


def test_first_occurrence_is_preserved() -> None:
    records = [
        {
            "company_name": "Cobalt Financial Group",
            "category": "financial",
            "description": "Quarterly results fell short.",
            "severity": 3,
        },
        {
            "company_name": "Cobalt Financial Group",
            "category": "financial",
            "description": "Quarterly results fell short.",
            "severity": 5,
        },
    ]

    unique_records, duplicate_records = deduplicate_records(records)

    assert len(unique_records) == 1
    assert len(duplicate_records) == 1
    assert unique_records[0]["severity"] == 3
