"""P22 Capability Forge Real — scaffold templates for 5 implementation types."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from src.capability_forge_lite.models import (
    CapabilityProposal,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_OFFLINE_PACKAGE,
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_EXTERNAL_FUTURE,
    IMPL_TYPE_APP_FACTORY_FUTURE,
)
from src.capability_forge_real.models import SkillTemplateConfig


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")


def _class_name(capability_name: str) -> str:
    """Converte snake_case para PascalCase."""
    return "".join(word.capitalize() for word in capability_name.split("_"))


# ── Base Skill Template ─────────────────────────────────────────────────────

SKILL_TEMPLATE = '''"""{{capability_name}} — {{description}}."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class {{class_name}}Input:
    """Input para {{capability_name}}."""
    request: str
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {"request": self.request, "dry_run": self.dry_run}


@dataclass
class {{class_name}}Output:
    """Output de {{capability_name}}."""
    result: dict
    status: str = "ok"
    generated_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "result": self.result,
            "status": self.status,
            "generated_at": self.generated_at,
        }


def run(input_data: dict) -> dict:
    """Executa {{capability_name}}."""
    inp = {{class_name}}Input(**input_data)
    # TODO: implementar logica real
    output = {{class_name}}Output(
        result={"message": f"{{capability_name}} stub: {inp.request}"},
        generated_at=_now_iso(),
    )
    return output.to_dict()
'''


# ── Offline Package Template ─────────────────────────────────────────────────

OFFLINE_PACKAGE_TEMPLATE = '''"""{{capability_name}} — offline package for {{sector}}."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class {{class_name}}Manifest:
    package_id: str
    template: str = "default"
    assets: list[str] | None = None
    metadata: dict | None = None

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "template": self.template,
            "assets": self.assets or [],
            "metadata": self.metadata or {},
        }


def generate_manifest(request_text: str, dry_run: bool = True) -> dict:
    """Gera manifest para {{capability_name}}."""
    manifest = {{class_name}}Manifest(
        package_id=f"pkg_{_now_iso()[:10]}",
        metadata={"request": request_text, "dry_run": dry_run},
    )
    return manifest.to_dict()
'''


# ── Manual Process Template ──────────────────────────────────────────────────

MANUAL_PROCESS_TEMPLATE = """# {{capability_name}}

> **Tipo:** Processo Manual
> **Setor:** {{sector}}
> **Status:** draft

## Passos

1. [ ] Passo 1 — receber solicitacao de {{capability_name}}
2. [ ] Passo 2 — executar acao manual
3. [ ] Passo 3 — registrar resultado em {{output_target}}

## Output Esperado

{{desired_output}}

## Notas

- Processo manual criado por P22 Capability Forge Real
- Substituir por automacao quando possivel
"""


# ── External Future Template ─────────────────────────────────────────────────

EXTERNAL_FUTURE_TEMPLATE = """# {{capability_name}}

> **Tipo:** Integracao Externa Futura
> **Setor:** {{sector}}
> **Status:** stub — integracao externa pendente

## Descricao

{{desired_output}}

## Dependencia Externa

Esta capability requer integracao com sistema externo ainda nao disponivel.

## Nota

Stub gerado por P22 Capability Forge Real.
Nao utilizar em producao ate que a integracao externa esteja disponivel.
"""


# ── App Factory Future Template ──────────────────────────────────────────────

APP_FACTORY_FUTURE_TEMPLATE = """# {{capability_name}}

> **Tipo:** App Factory Future
> **Setor:** {{sector}}
> **Status:** prd — product requirement doc

## Visao

{{desired_output}}

## Problema que Resolve

[TBD]

## Metricas de Sucesso

- [ ] Metrica 1
- [ ] Metrica 2

## Dependencias

- [ ] P22 Capability Forge Real (scaffold gerado)
- [ ] Implementacao pendente

## Nota

PRD gerado por P22 Capability Forge Real.
Requer desenvolvimento futuro.
"""


# ── Template Registry ────────────────────────────────────────────────────────

TEMPLATES = {
    IMPL_TYPE_CLI_WRAPPER: SKILL_TEMPLATE,
    IMPL_TYPE_OFFLINE_PACKAGE: OFFLINE_PACKAGE_TEMPLATE,
    IMPL_TYPE_MANUAL_PROCESS: MANUAL_PROCESS_TEMPLATE,
    IMPL_TYPE_EXTERNAL_FUTURE: EXTERNAL_FUTURE_TEMPLATE,
    IMPL_TYPE_APP_FACTORY_FUTURE: APP_FACTORY_FUTURE_TEMPLATE,
}

TEMPLATE_CONFIGS = {
    IMPL_TYPE_CLI_WRAPPER: SkillTemplateConfig.new(
        implementation_type=IMPL_TYPE_CLI_WRAPPER,
        target_dir="skills",
        filename="run.py",
        class_prefix="Cli",
        test_dir="skills",
    ),
    IMPL_TYPE_OFFLINE_PACKAGE: SkillTemplateConfig.new(
        implementation_type=IMPL_TYPE_OFFLINE_PACKAGE,
        target_dir="offline_factory",
        filename="manifest.py",
        class_prefix="Offline",
        test_dir="offline_factory",
    ),
    IMPL_TYPE_MANUAL_PROCESS: SkillTemplateConfig.new(
        implementation_type=IMPL_TYPE_MANUAL_PROCESS,
        target_dir="processes",
        filename="README.md",
        class_prefix="",
        test_dir="",
        test_filename="",
        min_tests=0,
    ),
    IMPL_TYPE_EXTERNAL_FUTURE: SkillTemplateConfig.new(
        implementation_type=IMPL_TYPE_EXTERNAL_FUTURE,
        target_dir="integrations",
        filename="README.md",
        class_prefix="",
        test_dir="",
        test_filename="",
        min_tests=0,
    ),
    IMPL_TYPE_APP_FACTORY_FUTURE: SkillTemplateConfig.new(
        implementation_type=IMPL_TYPE_APP_FACTORY_FUTURE,
        target_dir="apps",
        filename="PRD.md",
        class_prefix="",
        test_dir="",
        test_filename="",
        min_tests=0,
    ),
}


def render_template(
    template: str,
    proposal: CapabilityProposal,
) -> str:
    """Renderiza template com variaveis da proposal.

    Args:
        template: String do template com placeholders {{var}}
        proposal: CapabilityProposal com dados

    Returns:
        Template renderizado
    """
    class_name = _class_name(proposal.capability_name)
    description = proposal.desired_output
    sector = proposal.sector

    result = template
    result = result.replace("{{capability_name}}", proposal.capability_name)
    result = result.replace("{{class_name}}", class_name)
    result = result.replace("{{description}}", description)
    result = result.replace("{{sector}}", sector)
    result = result.replace("{{desired_output}}", description)
    result = result.replace("{{output_target}}", f"logs/{proposal.capability_name}.jsonl")

    return result


def get_template_config(implementation_type: str) -> SkillTemplateConfig | None:
    """Retorna config de template para um implementation_type."""
    return TEMPLATE_CONFIGS.get(implementation_type)


def get_template(implementation_type: str) -> str | None:
    """Retorna template string para um implementation_type."""
    return TEMPLATES.get(implementation_type)


def get_file_paths(
    proposal: CapabilityProposal,
    base_dir: Optional[Path] = None,
) -> dict[str, Path]:
    """Calcula paths de arquivos a gerar para uma proposal.

    Args:
        proposal: CapabilityProposal
        base_dir: Diretorio base (default: repo root)

    Returns:
        dict com 'source' e 'test' paths
    """
    base = base_dir or Path(__file__).resolve().parent.parent.parent
    config = get_template_config(proposal.implementation_type)
    if not config:
        return {}

    slug = _slug(proposal.capability_name)
    paths: dict[str, Path] = {}

    source_dir = base / "src" / config.target_dir / slug
    paths["source"] = source_dir / config.filename

    if config.test_dir and config.test_filename:
        test_dir = base / "tests" / config.test_dir / slug
        paths["test"] = test_dir / config.test_filename

    return paths
