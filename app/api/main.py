from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query

from app.services.signalwatch_service import SignalWatchService

app = FastAPI(title="SignalWatch API")
service = SignalWatchService()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest() -> Dict[str, Any]:
    return service.run_pipeline()


@app.get("/companies", response_model=List[Dict[str, Any]])
def list_companies(
    risk_level: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    minimum_score: Optional[float] = Query(default=None),
    limit: int = Query(default=10, ge=1),
) -> List[Dict[str, Any]]:
    return service.get_companies(
        risk_level=risk_level,
        country=country,
        minimum_score=minimum_score,
        limit=limit,
    )


@app.get("/companies/{company_name}", response_model=Dict[str, Any])
def get_company(company_name: str) -> Dict[str, Any]:
    try:
        return service.get_company_detail(company_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="company not found") from exc


@app.get("/events", response_model=List[Dict[str, Any]])
def list_events(
    country: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1),
) -> List[Dict[str, Any]]:
    return service.get_events(country=country, category=category, limit=limit)
