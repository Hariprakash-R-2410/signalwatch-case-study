from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def create_risk_score_distribution_chart(
    company_results: List[Dict[str, Any]],
    output_path: Optional[str | Path] = None,
) -> Path:
    """Create a single PNG chart showing company risk scores grouped by risk level."""
    if output_path is None:
        output_path = Path(__file__).resolve().parents[2] / "outputs" / "risk_score_distribution.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    grouped_scores: Dict[str, List[float]] = {"LOW": [], "MEDIUM": [], "HIGH": []}
    for company in company_results:
        risk_level = str(company.get("risk_level", "")).upper()
        if risk_level not in grouped_scores:
            continue
        score = company.get("company_risk_score")
        if score is None:
            continue
        grouped_scores[risk_level].append(float(score))

    labels = ["LOW", "MEDIUM", "HIGH"]
    values = [grouped_scores[level] for level in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    positions = [1, 2, 3]
    for position, level, scores in zip(positions, labels, values):
        ax.bar(position, sum(scores) / len(scores) if scores else 0.0, color={"LOW": "#4C78A8", "MEDIUM": "#F58518", "HIGH": "#54A24B"}[level], width=0.6)
        ax.text(position, (sum(scores) / len(scores) if scores else 0.0) + 1.5, level, ha="center", va="bottom")

    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Average company risk score")
    ax.set_title("Distribution of company risk scores by risk level")
    ax.set_ylim(0, max(100.0, max((sum(scores) / len(scores) if scores else 0.0) for scores in values) + 10))
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path
