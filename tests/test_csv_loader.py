from pathlib import Path

from app.ingestion.csv_loader import load_events_csv


def test_load_events_csv_returns_expected_rows() -> None:
    csv_path = (
        Path(__file__).resolve().parents[1]
        / "signalwatch-case-study"
        / "signalwatch-case-study"
        / "events.csv"
    )

    rows = load_events_csv(csv_path)

    assert rows is not None
    assert isinstance(rows, list)
    assert len(rows) == 60
    assert all(isinstance(row, dict) for row in rows)
