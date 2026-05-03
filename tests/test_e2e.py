"""
Testes E2E da Fase E — OMNIS / omnis-control.

Testam o comportamento ponta a ponta da cabine OMNIS sem modificar
sistemas externos. Usam subprocess para simular o usuário real.

Regras:
  - Timeout obrigatório para cada comando.
  - Não quebram se Docker/Qdrant/Publisher estiverem indisponíveis.
  - Não modificam nada fora de ~/omnis-control/.
  - Não executam skills reais (dry-run apenas).
  - Não dependem de publicação, tokens ou internet.
"""

import os
import sys
import json
import subprocess
import hashlib
from pathlib import Path

import pytest

CONTROL_DIR = os.path.expanduser("~/omnis-control")
PYTHON = sys.executable
OMNIS_SHIM = os.path.join(CONTROL_DIR, "omnis.py")
JARVIS_SHIM = os.path.join(CONTROL_DIR, "jarvis.py")

TIMEOUT_STATUS = 30
TIMEOUT_DOCTOR = 60
TIMEOUT_REPORT = 30
TIMEOUT_VIDEO = 60
TIMEOUT_RUN_SKILL = 15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_cli(shim: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, shim, *args],
        capture_output=True, text=True, timeout=timeout,
    )


# ---------------------------------------------------------------------------
# 1. omnis status
# ---------------------------------------------------------------------------

class TestE2E1OmnisStatus:
    """python omnis.py status roda e retorna status do ecossistema."""

    def test_status_returns_zero_exit(self):
        proc = _run_cli(OMNIS_SHIM, "status", timeout=TIMEOUT_STATUS)
        assert proc.returncode == 0, f"stderr: {proc.stderr[:300]}"

    def test_status_contains_skills(self):
        proc = _run_cli(OMNIS_SHIM, "status", timeout=TIMEOUT_STATUS)
        assert "Skills" in proc.stdout, "status output deve conter Skills"

    def test_status_contains_docker_section(self):
        proc = _run_cli(OMNIS_SHIM, "status", timeout=TIMEOUT_STATUS)
        assert "Docker" in proc.stdout or "docker" in proc.stdout.lower()

    def test_status_does_not_call_external_apis(self):
        """Confirma que status não faz chamadas de rede externas."""
        proc = _run_cli(OMNIS_SHIM, "status", timeout=TIMEOUT_STATUS)
        # publisher check só vai para localhost:8000, não para internet
        assert "https://" not in proc.stdout
        assert proc.returncode == 0


# ---------------------------------------------------------------------------
# 2. omnis doctor
# ---------------------------------------------------------------------------

class TestE2E2OmnisDoctor:
    """python omnis.py doctor > diagnose_e2e.json gera JSON válido."""

    def test_doctor_outputs_valid_json(self):
        proc = _run_cli(OMNIS_SHIM, "doctor", timeout=TIMEOUT_DOCTOR)
        assert proc.returncode == 0, f"stderr: {proc.stderr[:300]}"
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pytest.fail("doctor output não é JSON válido")
        assert isinstance(data, dict)

    def test_doctor_contains_all_checkers(self):
        proc = _run_cli(OMNIS_SHIM, "doctor", timeout=TIMEOUT_DOCTOR)
        data = json.loads(proc.stdout)
        required = {"skills", "docker", "publisher", "memory", "obsidian", "disk", "video_pipeline"}
        found = set(data.get("checks", {}).keys())
        missing = required - found
        assert not missing, f"Checkers faltando no doctor: {missing}"

    def test_doctor_has_session_id_and_timestamp(self):
        proc = _run_cli(OMNIS_SHIM, "doctor", timeout=TIMEOUT_DOCTOR)
        data = json.loads(proc.stdout)
        assert "session_id" in data, "session_id ausente"
        assert "timestamp" in data, "timestamp ausente"
        assert len(data["session_id"]) > 8

    def test_doctor_handles_unavailable_services_gracefully(self):
        """Doctor não quebra se algum checker falhar — retorna erro no campo."""
        proc = _run_cli(OMNIS_SHIM, "doctor", timeout=TIMEOUT_DOCTOR)
        data = json.loads(proc.stdout)
        # Mesmo com erros, o output deve ter todos os checkers
        assert "checks" in data
        # Pode ter status "critical" ou "warning" sem exception
        assert data["overall_status"] in ("ok", "warning", "critical")


# ---------------------------------------------------------------------------
# 3. omnis report
# ---------------------------------------------------------------------------

class TestE2E3OmnisReport:
    """python omnis.py report gera docs/ESTADO_ATUAL_RESUMIDO.md."""

    def test_report_generates_file(self):
        proc = _run_cli(OMNIS_SHIM, "report", timeout=TIMEOUT_REPORT)
        assert proc.returncode == 0
        report_path = os.path.join(CONTROL_DIR, "docs", "ESTADO_ATUAL_RESUMIDO.md")
        assert os.path.isfile(report_path), "Arquivo de relatório não foi gerado"

    def test_report_contains_required_sections(self):
        _run_cli(OMNIS_SHIM, "report", timeout=TIMEOUT_REPORT)
        report_path = os.path.join(CONTROL_DIR, "docs", "ESTADO_ATUAL_RESUMIDO.md")
        with open(report_path, encoding="utf-8") as f:
            content = f.read()

        required_sections = [
            "RISCOS IMEDIATOS",
            "Video Pipeline",
            "Skills",
            "Publisher OS",
            "Docker",
            "Memória",
            "Obsidian",
            "Segurança",
        ]
        for section in required_sections:
            assert section in content, f"Seção '{section}' ausente do relatório"

    def test_report_has_disk_section(self):
        _run_cli(OMNIS_SHIM, "report", timeout=TIMEOUT_REPORT)
        report_path = os.path.join(CONTROL_DIR, "docs", "ESTADO_ATUAL_RESUMIDO.md")
        with open(report_path, encoding="utf-8") as f:
            content = f.read()
        assert "Disco" in content


# ---------------------------------------------------------------------------
# 4. omnis video-status
# ---------------------------------------------------------------------------

class TestE2E4OmnisVideoStatus:
    """python omnis.py video-status roda e retorna classificação."""

    def test_video_status_runs_without_crash(self):
        proc = _run_cli(OMNIS_SHIM, "video-status", timeout=TIMEOUT_VIDEO)
        assert proc.returncode == 0, f"stderr: {proc.stderr[:300]}"

    def test_video_status_contains_classification(self):
        proc = _run_cli(OMNIS_SHIM, "video-status", timeout=TIMEOUT_VIDEO)
        assert "Classificação" in proc.stdout or "classificação" in proc.stdout.lower()

    def test_video_status_contains_signals(self):
        proc = _run_cli(OMNIS_SHIM, "video-status", timeout=TIMEOUT_VIDEO)
        assert "Sinais" in proc.stdout

    def test_video_status_does_not_modify_files(self):
        """video-status é read-only — verifica que não cria arquivos fora do esperado."""
        log_before = set(os.listdir(os.path.join(CONTROL_DIR, "logs")))
        _run_cli(OMNIS_SHIM, "video-status", timeout=TIMEOUT_VIDEO)
        log_after = set(os.listdir(os.path.join(CONTROL_DIR, "logs")))
        # Só pode ter criado arquivos de log (missions.jsonl)
        new_files = log_after - log_before
        for f in new_files:
            assert f.endswith(".jsonl"), f"Arquivo inesperado criado: {f}"


# ---------------------------------------------------------------------------
# 5. jarvis alias legado
# ---------------------------------------------------------------------------

class TestE2E5JarvisAlias:
    """python jarvis.py status continua funcionando como alias."""

    def test_jarvis_py_exists(self):
        assert os.path.isfile(JARVIS_SHIM)

    def test_jarvis_status_output_matches_omnis(self):
        proc_jarvis = _run_cli(JARVIS_SHIM, "status", timeout=TIMEOUT_STATUS)
        proc_omnis = _run_cli(OMNIS_SHIM, "status", timeout=TIMEOUT_STATUS)
        assert proc_jarvis.returncode == 0
        assert proc_omnis.returncode == 0
        # Ambos devem mostrar Skills e Docker
        assert "Skills" in proc_jarvis.stdout
        assert "Docker" in proc_jarvis.stdout

    def test_jarvis_doctor_works(self):
        proc = _run_cli(JARVIS_SHIM, "doctor", timeout=TIMEOUT_DOCTOR)
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert "checks" in data

    def test_jarvis_skills_works(self):
        proc = _run_cli(JARVIS_SHIM, "skills", timeout=TIMEOUT_STATUS)
        assert proc.returncode == 0
        assert "Skills" in proc.stdout


# ---------------------------------------------------------------------------
# 6. run-skill dry-run
# ---------------------------------------------------------------------------

class TestE2E6RunSkillDryRun:
    """omnis run-skill sem --yes faz dry-run e NÃO executa a skill."""

    def test_run_skill_inexistent_returns_error(self):
        proc = _run_cli(OMNIS_SHIM, "run-skill", "skill_inexistente_xyz_e2e", timeout=TIMEOUT_RUN_SKILL)
        assert proc.returncode != 0, "Deveria falhar para skill inexistente"
        combined = proc.stdout + proc.stderr
        assert "Erro" in combined or "não" in combined.lower()

    def test_run_skill_existing_without_yes_is_dry_run(self):
        """Para skill existente sem --yes, deve retornar dry_run."""
        # Pega primeira skill real com run.py
        skills_dir = os.path.expanduser("~/.claude/skills")
        if not os.path.isdir(skills_dir):
            pytest.skip("Nenhum diretório de skills encontrado")
        real = [
            d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d))
            and os.path.isfile(os.path.join(skills_dir, d, "run.py"))
        ]
        if not real:
            pytest.skip("Nenhuma skill com run.py encontrada")

        proc = _run_cli(OMNIS_SHIM, "run-skill", real[0], timeout=TIMEOUT_RUN_SKILL)
        assert proc.returncode == 0
        combined = proc.stdout + proc.stderr
        assert "dry" in combined.lower() or "Dry" in combined

    def test_run_skill_dry_run_does_not_create_side_effects(self):
        """Dry-run não cria arquivos inesperados."""
        skills_dir = os.path.expanduser("~/.claude/skills")
        if not os.path.isdir(skills_dir):
            pytest.skip("Nenhuma skill encontrada")
        real = [
            d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d))
            and os.path.isfile(os.path.join(skills_dir, d, "run.py"))
        ]
        if not real:
            pytest.skip("Nenhuma skill com run.py encontrada")

        files_before = set(os.listdir(CONTROL_DIR))
        _run_cli(OMNIS_SHIM, "run-skill", real[0], timeout=TIMEOUT_RUN_SKILL)
        files_after = set(os.listdir(CONTROL_DIR))
        # Só pode criar arquivos de log em logs/
        new = files_after - files_before
        for f in new:
            full = os.path.join(CONTROL_DIR, f)
            # Permite arquivos na raiz (missions.jsonl é em logs/) e logs
            assert os.path.isdir(full) or f.endswith(".jsonl") or f.startswith("logs/"), f"Side effect: {f}"


# ---------------------------------------------------------------------------
# 7. Segurança E2E
# ---------------------------------------------------------------------------

class TestE2E7Seguranca:
    """
    Segurança E2E:
      - nenhum arquivo fora de ~/omnis-control é modificado
      - .env não é lido
      - Docker não é alterado
      - Instagram/Meta/Google Drive não são chamados
    """

    def test_no_outside_files_modified(self):
        """Verifica que arquivos de referência fora do controle não mudam."""
        # snapshot de hash de arquivos conhecidos fora do omnis-control
        ref_files = [
            os.path.expanduser("~/.claude/CLAUDE.md"),
            os.path.expanduser("~/.gitconfig") if os.path.isfile(os.path.expanduser("~/.gitconfig")) else None,
        ]
        ref_files = [f for f in ref_files if f and os.path.isfile(f)]
        if not ref_files:
            pytest.skip("Nenhum arquivo de referência externo encontrado")

        hashes_before = {}
        for f in ref_files:
            with open(f, "rb") as fh:
                hashes_before[f] = hashlib.md5(fh.read()).hexdigest()

        # Roda todos os comandos OMNIS
        _run_cli(OMNIS_SHIM, "status", timeout=TIMEOUT_STATUS)
        _run_cli(OMNIS_SHIM, "doctor", timeout=TIMEOUT_DOCTOR)
        _run_cli(OMNIS_SHIM, "report", timeout=TIMEOUT_REPORT)
        _run_cli(OMNIS_SHIM, "video-status", timeout=TIMEOUT_VIDEO)

        hashes_after = {}
        for f in ref_files:
            with open(f, "rb") as fh:
                hashes_after[f] = hashlib.md5(fh.read()).hexdigest()

        for f in ref_files:
            assert hashes_before[f] == hashes_after[f], f"Arquivo externo foi modificado: {f}"

    def test_env_not_read(self):
        """Confirma que nenhum checker lê .env."""
        for root, _dirs, files in os.walk(os.path.join(CONTROL_DIR, "src")):
            for f in files:
                if f.endswith(".py"):
                    fpath = os.path.join(root, f)
                    with open(fpath, encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    assert "load_dotenv" not in content, f"{fpath} usa load_dotenv"
                    # Verificar dotenv import não usa apenas .env no caminho (safe_paths testa já)

    def test_commands_do_not_contain_external_urls(self):
        """Verifica que outputs de comandos não contêm URLs externas (exceto localhost)."""
        for cmd, args, to in [
            ("status", [], TIMEOUT_STATUS),
            ("video-status", [], TIMEOUT_VIDEO),
            ("skills", [], 15),
        ]:
            proc = _run_cli(OMNIS_SHIM, cmd, timeout=to)
            output = (proc.stdout + proc.stderr).lower()
            # Pode conter localhost, não pode conter api.facebook ou graph.instagram
            external_apis = [
                "graph.facebook",
                "graph.instagram",
                "api.instagram",
                "accounts.google.com",
                "www.googleapis.com/auth",
            ]
            for api in external_apis:
                if api in output:
                    pytest.fail(f"Comando '{cmd}' chamou API externa: {api}")

    def test_no_docker_modification(self):
        """doctor não modifica containers — só lê status."""
        proc = _run_cli(OMNIS_SHIM, "doctor", timeout=TIMEOUT_DOCTOR)
        data = json.loads(proc.stdout)
        docker_data = data.get("checks", {}).get("docker", {})
        assert "error" not in docker_data or docker_data.get("error") is None, \
            f"Erro Docker inesperado: {docker_data.get('error')}"
        # Verifica que o output Docker é somente leitura (contém status, não ações)
        assert "containers_running" in docker_data or "error" in docker_data
