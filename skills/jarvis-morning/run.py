#!/usr/bin/env python3
"""jarvis-morning: Briefing operacional matinal com diagnóstico de sistema."""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional
from urllib.request import urlopen

OBSIDIAN_BASE = os.path.expanduser("~/Desktop/OBSIDIAN/ComandoCentral")
PUBLISHER_OS_URL = os.getenv("PUBLISHER_OS_URL", "http://localhost:8000")
DISCO_ALERTA = 92


def diagnostico_sistema() -> dict:
    """Diagnóstico de sistema: Docker, disco, serviços."""
    estado = {"geral": "verde", "alertas": []}

    # Disco
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        linha = result.stdout.strip().split("\n")[1]
        partes = linha.split()
        uso_str = partes[4].replace("%", "")
        uso = int(uso_str)
        estado["disco"] = f"{uso}%"
        if uso > DISCO_ALERTA:
            estado["alertas"].append(f"DISCO CRITICO: {uso}%")
            estado["geral"] = "vermelho"
        elif uso > 80:
            estado["alertas"].append(f"Disco: {uso}%")
    except Exception:
        estado["disco"] = "indisponivel"

    # Docker
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        unhealthy = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            nome = parts[0]
            status = parts[1] if len(parts) > 1 else "unknown"
            containers.append({"nome": nome, "status": status})
            if "unhealthy" in status.lower():
                unhealthy.append(nome)

        estado["containers"] = containers
        estado["total_containers"] = len(containers)
        estado["unhealthy"] = unhealthy
        if unhealthy:
            estado["alertas"].append(f"UNHEALTHY: {', '.join(unhealthy)}")
            if estado["geral"] == "verde":
                estado["geral"] = "amarelo"
    except Exception as e:
        estado["containers_error"] = str(e)

    # Publisher OS
    try:
        resp = urlopen(f"{PUBLISHER_OS_URL}/health", timeout=5)
        estado["publisher_os"] = "UP" if resp.status == 200 else f"status_{resp.status}"
    except Exception:
        estado["publisher_os"] = "DOWN"

    return estado


def missao_do_dia() -> Optional[str]:
    """Lê a missão do dia do Obsidian."""
    try:
        path = os.path.join(OBSIDIAN_BASE, "MISSAO_DO_DIA.md")
        if os.path.exists(path):
            with open(path) as f:
                lines = f.readlines()
                return "".join(lines[:5]).strip() or None
    except Exception:
        pass
    return None


def pipeline_comercial() -> Optional[str]:
    """Lê pipeline comercial."""
    try:
        path = os.path.join(OBSIDIAN_BASE, "PIPELINE.csv")
        if os.path.exists(path):
            with open(path) as f:
                lines = f.readlines()
                return "".join(lines[:8]).strip() or None
    except Exception:
        pass
    return None


def morning() -> dict:
    """Gera briefing matinal completo."""
    sistema = diagnostico_sistema()
    missao = missao_do_dia()
    pipeline = pipeline_comercial()

    # Top 3 prioridades (baseadas no estado do sistema)
    prioridades = ["1. Revisar pipeline comercial e enviar DMs pendentes",
                   "2. Verificar fila de conteudo do dia",
                   "3. Checar containers unhealthy e diagnosticar"]

    if sistema["geral"] == "vermelho":
        prioridades.insert(0, f"⚠️ CRITICO: {sistema['alertas'][0]}")

    resultado = {
        "timestamp": datetime.now().isoformat(),
        "sistema": sistema,
        "missao_do_dia": missao,
        "pipeline_comercial": pipeline,
        "top_3_prioridades": prioridades[:3],
        "alertas": sistema.get("alertas", []),
        "mensagem": f"Bom dia, Tigrao. {datetime.now().strftime('%A, %d/%m/%Y')}",
        "next_action": "Qual das 3 missoes voce quer atacar primeiro?"
    }

    return resultado


if __name__ == "__main__":
    result = morning()
    print(json.dumps(result, indent=2, ensure_ascii=False))
