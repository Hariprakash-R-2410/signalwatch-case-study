from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType
except ImportError:  # pragma: no cover - exercised in environments without PySpark
    SparkSession = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    StructField = StructType = DoubleType = IntegerType = StringType = None  # type: ignore[assignment]


def process_risk_scores(
    records: List[Dict[str, Any]],
    as_of_date: Optional[date] = None,
    output_path: Optional[str | Path] = None,
) -> List[Dict[str, Any]]:
    """Process normalized records into company-level risk scores.

    When PySpark is available, the function uses a local Spark session with an
    explicit schema. If PySpark is not installed, the same scoring logic runs in
    pure Python so the workflow remains testable in lightweight environments.
    """
    if as_of_date is None:
        as_of_date = date.today()

    if SparkSession is not None and F is not None:
        return _process_with_spark(records, as_of_date=as_of_date, output_path=output_path)

    return _process_without_spark(records, as_of_date=as_of_date, output_path=output_path)


def _process_with_spark(
    records: List[Dict[str, Any]],
    as_of_date: date,
    output_path: Optional[str | Path],
) -> List[Dict[str, Any]]:
    spark = SparkSession.builder.master("local[1]").appName("SignalWatch").getOrCreate()

    try:
        schema = StructType(
            [
                StructField("company_name", StringType(), True),
                StructField("category", StringType(), True),
                StructField("severity", IntegerType(), True),
                StructField("confidence", DoubleType(), True),
                StructField("published_at", StringType(), True),
                StructField("country", StringType(), True),
                StructField("source", StringType(), True),
                StructField("description", StringType(), True),
            ]
        )

        rows = [
            (
                record.get("company_name"),
                record.get("category"),
                int(record.get("severity", 0)),
                float(record.get("confidence", 0.0)),
                record.get("published_at"),
                record.get("country"),
                record.get("source"),
                record.get("description"),
            )
            for record in records
        ]

        df = spark.createDataFrame(rows, schema=schema)
        parsed_date = F.to_date(F.to_timestamp(df["published_at"], "yyyy-MM-dd'T'HH:mm:ss'Z'"))
        as_of = F.lit(as_of_date)
        days_old = F.datediff(as_of, parsed_date)

        recency_weight = (
            F.when(days_old <= 7, F.lit(1.0))
            .when(days_old <= 30, F.lit(0.8))
            .otherwise(F.lit(0.6))
        )

        df = df.withColumn("days_old", days_old)
        df = df.withColumn("recency_weight", recency_weight)
        df = df.withColumn(
            "event_risk_score",
            F.round(
                F.least(
                    F.lit(100.0),
                    F.col("severity") * F.lit(20) * F.col("confidence") * F.col("recency_weight"),
                ),
                2,
            ),
        )

        company_scores = (
            df.select("company_name", "event_risk_score")
            .groupBy("company_name")
            .agg(F.collect_list("event_risk_score").alias("scores"))
            .withColumn(
                "top_scores",
                F.when(F.size("scores") < 5, F.col("scores")).otherwise(F.slice(F.array_sort(F.col("scores")), -5, 5)),
            )
            .withColumn("company_risk_score", F.round(F.avg("top_scores"), 2))
            .withColumn(
                "risk_level",
                F.when(F.col("company_risk_score") <= 39.99, F.lit("LOW"))
                .when(F.col("company_risk_score") <= 69.99, F.lit("MEDIUM"))
                .otherwise(F.lit("HIGH")),
            )
            .select("company_name", "company_risk_score", "risk_level")
        )

        if output_path is not None:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            company_scores.write.mode("overwrite").csv(str(output_file), header=True)

        return [
            {
                "company_name": row.company_name,
                "company_risk_score": row.company_risk_score,
                "risk_level": row.risk_level,
            }
            for row in company_scores.collect()
        ]
    finally:
        spark.stop()


def _process_without_spark(
    records: List[Dict[str, Any]],
    as_of_date: date,
    output_path: Optional[str | Path],
) -> List[Dict[str, Any]]:
    grouped_scores: Dict[str, List[float]] = defaultdict(list)

    for record in records:
        severity = int(record.get("severity", 0))
        confidence = float(record.get("confidence", 0.0))
        published_at = record.get("published_at")
        days_old = _calculate_days_old(published_at, as_of_date)
        recency_weight = _calculate_recency_weight(days_old)
        event_score = round(min(100.0, severity * 20 * confidence * recency_weight), 2)
        grouped_scores[str(record.get("company_name", ""))].append(event_score)

    results: List[Dict[str, Any]] = []
    for company_name, scores in sorted(grouped_scores.items()):
        top_scores = sorted(scores, reverse=True)[:5] if len(scores) >= 5 else scores
        company_score = round(sum(top_scores) / len(top_scores), 2) if top_scores else 0.0
        risk_level = _classify_risk(company_score)
        results.append(
            {
                "company_name": company_name,
                "company_risk_score": company_score,
                "risk_level": risk_level,
            }
        )

    if output_path is not None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["company_name", "company_risk_score", "risk_level"])
            writer.writeheader()
            writer.writerows(results)

    return results


def _calculate_days_old(published_at: Optional[str], as_of_date: date) -> int:
    if not published_at:
        return 999

    try:
        parsed_date = datetime.strptime(str(published_at), "%Y-%m-%dT%H:%M:%SZ").date()
    except ValueError:
        return 999

    return (as_of_date - parsed_date).days


def _calculate_recency_weight(days_old: int) -> float:
    if days_old <= 7:
        return 1.0
    if days_old <= 30:
        return 0.8
    return 0.6


def _classify_risk(score: float) -> str:
    if score <= 39.99:
        return "LOW"
    if score <= 69.99:
        return "MEDIUM"
    return "HIGH"
