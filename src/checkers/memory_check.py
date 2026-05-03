import subprocess
import json

QDRANT_URL = "http://localhost:6333"
AKASHA_CONTAINER = "akasha-postgres"


def _qdrant_collections() -> dict:
    try:
        import httpx
        resp = httpx.get(f"{QDRANT_URL}/collections", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            collections = data.get("result", {}).get("collections", [])
            return {
                "accessible": True,
                "collections_count": len(collections),
                "collections": [c.get("name", "unknown") for c in collections],
            }
        return {"accessible": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"accessible": False, "error": str(e)}


def _akasha_status() -> dict:
    try:
        output = subprocess.run(
            ["docker", "ps", "--filter", f"name={AKASHA_CONTAINER}", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if output.returncode != 0 or not output.stdout.strip():
            return {"container_found": False, "status": "not_running"}

        c = json.loads(output.stdout.strip().split("\n")[0])
        status = c.get("Status", "unknown")
        is_healthy = "healthy" in status.lower() if status else False
        return {
            "container_found": True,
            "status": status,
            "healthy": is_healthy,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        return {"container_found": False, "error": str(e)}


def check() -> dict:
    qdrant = _qdrant_collections()
    akasha = _akasha_status()

    overall = "ok"
    if not qdrant.get("accessible") and not akasha.get("container_found"):
        overall = "error"
    elif not qdrant.get("accessible") or not akasha.get("container_found"):
        overall = "warning"

    return {
        "overall": overall,
        "qdrant": qdrant,
        "akasha": akasha,
    }
