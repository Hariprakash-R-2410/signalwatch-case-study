from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


def load_events_csv(csv_path: str | Path | None = None) -> List[Dict[str, str]]:
    """Load events from the provided CSV file as a list of dictionaries.

    The function intentionally performs no validation or normalization. It simply
    reads the file using Python's standard csv module and returns the parsed rows.
    """
    if csv_path is None:
        csv_path = (
            Path(__file__).resolve().parents[2]
            / "signalwatch-case-study"
            / "signalwatch-case-study"
            / "events.csv"
        )

    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
