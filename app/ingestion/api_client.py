from __future__ import annotations

import json
import socket
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_events_from_api(
    base_url: str = "http://127.0.0.1:9000",
    timeout: float = 5.0,
    max_retries: int = 2,
) -> List[Dict[str, Any]]:
    """Fetch all pages of events from the mock REST API.

    The function keeps API access separate from validation and normalization.
    It returns any successfully fetched records and skips pages that fail due to
    timeouts, HTTP errors, or malformed JSON.
    """
    records: List[Dict[str, Any]] = []
    page = 1

    while True:
        params = urlencode({"page": page, "page_size": 50})
        url = f"{base_url.rstrip('/')}/api/v1/events?{params}"
        payload = _fetch_json_with_retries(url, timeout=timeout, max_retries=max_retries)

        if payload is None:
            break

        if not isinstance(payload, dict):
            break

        results = payload.get("results", [])
        if isinstance(results, list):
            records.extend(
                item for item in results if isinstance(item, dict)
            )

        has_more = payload.get("has_more", False)
        if not has_more:
            break

        page += 1

    return records


def _fetch_json_with_retries(
    url: str,
    timeout: float,
    max_retries: int,
) -> Optional[Dict[str, Any]]:
    for attempt in range(max_retries + 1):
        try:
            request = Request(url, headers={"Accept": "application/json"})
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except (socket.timeout, TimeoutError, URLError) as exc:
            if attempt >= max_retries:
                return None
            continue
        except HTTPError:
            return None
        except json.JSONDecodeError:
            return None

    return None
