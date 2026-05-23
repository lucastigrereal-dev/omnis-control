from src.reports import status_report


def test_generate_status_report_with_mocked_checks(monkeypatch):
    monkeypatch.setattr(
        status_report.skills_check,
        "check",
        lambda: {
            "total": 3,
            "executable": 2,
            "doc_folder": 1,
            "doc_file": 0,
            "orphan_skills": ["missing_skill"],
        },
    )
    monkeypatch.setattr(
        status_report.docker_check,
        "check",
        lambda: {
            "containers_running": 2,
            "containers_unhealthy": 1,
            "containers": [
                {"name": "ok", "status": "running", "ports": "80", "unhealthy": False},
                {"name": "bad", "status": "unhealthy", "ports": "", "unhealthy": True},
            ],
        },
    )
    monkeypatch.setattr(
        status_report.publisher_check,
        "check",
        lambda: {"status": "ok", "identified": True, "port_open": True},
    )
    monkeypatch.setattr(
        status_report.memory_check,
        "check",
        lambda: {
            "qdrant": {"accessible": True, "collections_count": 1, "collections": ["main"]},
            "akasha": {"container_found": True, "status": "running"},
        },
    )
    monkeypatch.setattr(
        status_report.obsidian_check,
        "check",
        lambda: {
            "vault_found": True,
            "vault_path": "C:/vault",
            "md_file_count": 7,
            "top_folders": ["C:/vault/A"],
        },
    )
    monkeypatch.setattr(
        status_report.disk_check,
        "check",
        lambda: {"severity": "ok", "disks": []},
    )
    monkeypatch.setattr(
        status_report.video_pipeline_check,
        "check",
        lambda: {
            "classification": "ready",
            "confidence": "high",
            "signals": {"assets": True},
            "counts": {"videos": 2},
            "risks": [],
        },
    )

    report = status_report.generate("sess_test")

    assert "# ESTADO ATUAL RESUMIDO" in report
    assert "**Session ID:** `sess_test`" in report
    assert "## 1. RISCOS IMEDIATOS" in report
    assert "**Containers unhealthy:** bad" in report
    assert "## 9. Video Pipeline" in report
    assert "## 16. Comandos úteis" in report
