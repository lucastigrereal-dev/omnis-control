import subprocess
import json


def check() -> dict[str, object]:
    result = {
        "containers_running": 0,
        "containers_unhealthy": 0,
        "containers": [],
        "error": None,
    }

    try:
        output = subprocess.run(
            ["docker", "ps", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if output.returncode != 0:
            result["error"] = f"docker ps falhou: {output.stderr.strip()}"
            return _try_docker_sdk(result)

        lines = [l for l in output.stdout.strip().split("\n") if l.strip()]
        for line in lines:
            try:
                c = json.loads(line)
                name = c.get("Names", "unknown")
                status = c.get("Status", "unknown")
                image = c.get("Image", "unknown")
                ports = c.get("Ports", "")
                is_unhealthy = "unhealthy" in status.lower()
                result["containers"].append({
                    "name": name,
                    "status": status,
                    "image": image,
                    "ports": ports,
                    "unhealthy": is_unhealthy,
                })
                result["containers_running"] += 1
                if is_unhealthy:
                    result["containers_unhealthy"] += 1
            except (json.JSONDecodeError, KeyError):
                continue

    except FileNotFoundError:
        result["error"] = "Docker CLI não encontrado no PATH"
        return _try_docker_sdk(result)
    except subprocess.TimeoutExpired:
        result["error"] = "docker ps timed out (10s)"
    except OSError as e:
        result["error"] = str(e)

    return result


def _try_docker_sdk(result: dict[str, object]) -> dict[str, object]:
    try:
        import docker  # type: ignore
        client = docker.from_env()
        containers = client.containers.list(all=False)
        for c in containers:
            name = c.name
            status = c.status
            image = c.image.tags[0] if c.image.tags else "none"
            ports = str(c.ports) if c.ports else ""
            is_unhealthy = status != "running"
            result["containers"].append({
                "name": name,
                "status": status,
                "image": image,
                "ports": ports,
                "unhealthy": is_unhealthy,
            })
            result["containers_running"] += 1
            if is_unhealthy:
                result["containers_unhealthy"] += 1
    except Exception as e:
        if not result["error"]:
            result["error"] = f"Docker SDK falhou: {e}"
    return result
