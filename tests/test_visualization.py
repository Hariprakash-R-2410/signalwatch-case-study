from pathlib import Path

from app.visualization.risk_chart import create_risk_score_distribution_chart


def test_create_risk_score_distribution_chart_writes_png(tmp_path: Path) -> None:
    company_results = [
        {"company_name": "Acme Corp", "company_risk_score": 82.3, "risk_level": "HIGH"},
        {"company_name": "Globex Ltd", "company_risk_score": 35.2, "risk_level": "LOW"},
        {"company_name": "Northwind", "company_risk_score": 51.4, "risk_level": "MEDIUM"},
        {"company_name": "Example Corp", "company_risk_score": 75.8, "risk_level": "HIGH"},
    ]

    output_path = tmp_path / "risk_score_distribution.png"
    created_path = create_risk_score_distribution_chart(company_results, output_path=output_path)

    assert created_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0
