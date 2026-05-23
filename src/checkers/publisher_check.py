import httpx
import socket

PUBLISHER_URL = "http://localhost:8000"
TIMEOUT = 5.0


def _port_open(host: str = "localhost", port: int = 8000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def _try_get(client: httpx.Client, url: str) -> dict[str, object] | None:
    try:
        resp = client.get(url, timeout=TIMEOUT)
        return {
            "status_code": resp.status_code,
            "body_preview": resp.text[:300],
            "content_type": resp.headers.get("content-type", ""),
        }
    except (httpx.TimeoutException, httpx.RequestError):
        return None


def check() -> dict[str, object]:
    port_open = _port_open()

    if not port_open:
        return {
            "status": "port_closed",
            "port_open": False,
            "details": "Porta 8000 não está aberta. Publisher OS pode estar parado.",
        }

    result = {
        "status": "port_open_no_response",
        "port_open": True,
        "tried_endpoints": [],
        "identified": False,
        "identify_hint": None,
    }

    with httpx.Client(base_url=PUBLISHER_URL, verify=False) as client:
        for endpoint in ["/health", "/", "/docs", "/api/v1/argos/health"]:
            resp_data = _try_get(client, f"{PUBLISHER_URL}{endpoint}")
            if resp_data is None:
                continue
            result["tried_endpoints"].append({endpoint: resp_data})
            body = resp_data.get("body_preview", "").lower()
            if any(kw in body for kw in ["publisher", "fastapi", "argos", "ok"]):
                result["status"] = "ok"
                result["identified"] = True
                result["identify_hint"] = f"Publisher OS identificado via {endpoint}"
                break
            if resp_data["status_code"] == 200:
                result["status"] = "running_unknown"

    return result
