#!/usr/bin/env python3
"""skill-creator: Cria novas skills Jarvis no padrão oficial."""

import json
import os
import sys
from datetime import datetime
from typing import Optional
import yaml

SKILLS_DIR = os.path.expanduser("~/.claude/skills")
REGISTRY_DIR = os.path.expanduser("~/.claude/registry")
SKILLS_REGISTRY = os.path.join(REGISTRY_DIR, "skills.yaml")
SECTORS_REGISTRY = os.path.join(REGISTRY_DIR, "sectors.yaml")

SKILL_MD_TEMPLATE = """---
name: {skill_id}
description: |
  {description}
trigger:
  - "{trigger_1}"
  - "{trigger_2}"
sector: {sector}
risk: {risk}
model: {model}
approval_required: []
status: {status}
version: 1.0
cost_estimate: "{cost_estimate}"
---

# Skill: {skill_id}

{description}

## Quando usar

- "{trigger_1}"
- "{trigger_2}"

## Processo

### 1. [Primeiro passo]

Descrição do primeiro passo.

### 2. [Segundo passo]

Descrição do segundo passo.

### 3. Output

```json
{{
  "status": "ok",
  "resultado": "...",
  "next_action": "..."
}}
```

## Regras

- Regra 1
- Regra 2
- Toda skill termina com `next_action`
"""

RUN_PY_TEMPLATE = """#!/usr/bin/env python3
\"\"\"{skill_id}: {description}\"\"\"

import json
import sys


def main(args: list[str]) -> dict:
    \"\"\"Função principal da skill.\"\"\"
    resultado = {{
        "skill_id": "{skill_id}",
        "status": "executado",
        "next_action": "proximo passo concreto"
    }}
    return resultado


if __name__ == "__main__":
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    result = main(args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
"""

TEST_TEMPLATE = """#!/usr/bin/env python3
\"\"\"Teste de fumaça: {skill_id}\"\"\"

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run import main


def test_basico():
    \"\"\"Teste básico de execução.\"\"\"
    result = main([])
    assert isinstance(result, dict), "Resultado deve ser dict"
    assert "status" in result, "Resultado deve ter status"
    assert "next_action" in result, "Resultado deve ter next_action"
    print(f"  OK: {result.get('status')}")


def test_com_args():
    \"\"\"Teste com argumentos.\"\"\"
    result = main(["teste"])
    assert isinstance(result, dict)
    print(f"  OK: {result.get('status')}")


def test_json_serializavel():
    \"\"\"Teste se o resultado é JSON-serializável.\"\"\"
    result = main([])
    json_str = json.dumps(result, ensure_ascii=False)
    assert len(json_str) > 0
    print(f"  OK: JSON valido ({len(json_str)} chars)")


if __name__ == "__main__":
    test_basico()
    test_com_args()
    test_json_serializavel()
    print("\\nTodos os testes passaram.")
"""


def verificar_duplicata(skill_id: str) -> Optional[str]:
    """Verifica se skill já existe."""
    # Verifica diretório
    skill_dir = os.path.join(SKILLS_DIR, skill_id)
    if os.path.exists(skill_dir):
        return "diretorio_ja_existe"

    # Verifica registry
    if os.path.exists(SKILLS_REGISTRY):
        try:
            with open(SKILLS_REGISTRY) as f:
                data = yaml.safe_load(f)
            for section in ["jarvis_core", "custom"]:
                for s in data.get(section, []):
                    if s["id"] == skill_id:
                        return "registry_ja_existe"
        except Exception:
            pass

    return None


def criar_skill(skill_id: str, description: str, sector: str,
                trigger_1: str = "", trigger_2: str = "",
                model: str = "haiku", risk: str = "low",
                cost_estimate: str = "$0.001/run",
                dry_run: bool = True) -> dict:
    """Cria uma nova skill no padrão oficial."""
    # Verificar duplicata
    dup = verificar_duplicata(skill_id)
    if dup:
        return {"status": "duplicate", "motivo": dup, "skill_id": skill_id}

    skill_dir = os.path.join(SKILLS_DIR, skill_id)
    tests_dir = os.path.join(skill_dir, "tests")

    if dry_run:
        return {
            "status": "dry_run",
            "skill_id": skill_id,
            "files": [f"~/.claude/skills/{skill_id}/SKILL.md",
                      f"~/.claude/skills/{skill_id}/run.py",
                      f"~/.claude/skills/{skill_id}/tests/test_1.py",
                      f"~/.claude/skills/{skill_id}/tests/test_2.py",
                      f"~/.claude/skills/{skill_id}/tests/test_3.py"],
            "registry_updates": [f"skills.yaml -> custom adicionado",
                                 f"sectors.yaml -> setor {sector}"],
            "dry_run": True,
            "next_action": "Aprovar criacao? (sim/nao)"
        }

    # Criar diretórios
    os.makedirs(tests_dir, exist_ok=True)

    # Gerar SKILL.md
    skill_md = SKILL_MD_TEMPLATE.format(
        skill_id=skill_id, description=description, sector=sector,
        risk=risk, model=model, status="draft",
        trigger_1=trigger_1 or f"executa {skill_id}",
        trigger_2=trigger_2 or f"roda {skill_id}",
        cost_estimate=cost_estimate
    )

    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(skill_md)

    # Gerar run.py
    run_py = RUN_PY_TEMPLATE.format(skill_id=skill_id, description=description)
    with open(os.path.join(skill_dir, "run.py"), "w") as f:
        f.write(run_py)
    os.chmod(os.path.join(skill_dir, "run.py"), 0o755)

    # Gerar 3 testes
    for i in range(1, 4):
        test_py = TEST_TEMPLATE.format(skill_id=skill_id)
        with open(os.path.join(tests_dir, f"test_{i}.py"), "w") as f:
            f.write(test_py)

    # Atualizar registry skills.yaml
    if os.path.exists(SKILLS_REGISTRY):
        try:
            with open(SKILLS_REGISTRY) as f:
                skills_data = yaml.safe_load(f) or {}
        except Exception:
            skills_data = {"version": "1.1", "jarvis_core": [], "custom": []}

        if "custom" not in skills_data:
            skills_data["custom"] = []

        skills_data["custom"].append({
            "id": skill_id,
            "status": "draft",
            "file": f"~/.claude/skills/{skill_id}/SKILL.md",
            "sector": sector,
            "yaml_frontmatter": True,
            "model": model,
            "cost_estimate": cost_estimate,
        })

        with open(SKILLS_REGISTRY, "w") as f:
            yaml.dump(skills_data, f, default_flow_style=False, allow_unicode=True)

    return {
        "status": "created",
        "skill_id": skill_id,
        "files": [f"~/.claude/skills/{skill_id}/SKILL.md",
                  f"~/.claude/skills/{skill_id}/run.py",
                  f"~/.claude/skills/{skill_id}/tests/test_1.py",
                  f"~/.claude/skills/{skill_id}/tests/test_2.py",
                  f"~/.claude/skills/{skill_id}/tests/test_3.py"],
        "registry_updated": True,
        "dry_run": False,
        "next_action": f"Skill {skill_id} criada. Rodar testes?"
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cria nova skill Jarvis")
    parser.add_argument("skill_id", help="ID da skill (ex: lead-qualifier)")
    parser.add_argument("--description", default="Nova skill", help="Descrição")
    parser.add_argument("--sector", default="operacoes_organizacao", help="Setor")
    parser.add_argument("--model", default="haiku", help="Modelo")
    parser.add_argument("--risk", default="low", help="Risco")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simular")
    args = parser.parse_args()

    result = criar_skill(
        skill_id=args.skill_id,
        description=args.description,
        sector=args.sector,
        model=args.model,
        risk=args.risk,
        dry_run=args.dry_run
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
