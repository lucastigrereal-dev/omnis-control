---
name: skill-creator
description: |
  Cria novas skills Jarvis no padrão oficial. Recebe descrição de gap, setor,
  e exemplos, e gera SKILL.md + run.py + testes no diretório correto.
trigger:
  - "cria uma skill que..."
  - "preciso de uma skill para..."
  - gap identificado por jarvis-delegate
  - "skill nova"
sector: cross-cutting
risk: medium
model: sonnet
approval_required:
  - skill_creation
  - registry_update
status: active
version: 1.0
cost_estimate: "$0.01/run"
verification_criteria:
  - SKILL.md gerado no padrão oficial (YAML frontmatter + markdown)
  - run.py com função main executável
  - 3 testes de fumaça em tests/
  - Registry skills.yaml atualizado
  - Tudo em dry_run: true até aprovação
---

# Skill: skill-creator

Skills que criam skills. Automatiza a criação de novas skills Jarvis.

## Quando usar

- Gap identificado por jarvis-delegate ("sem skill para X")
- Lucas pede explicitamente "cria uma skill que..."
- "skill nova para [setor]"
- Refatoração de skill existente para o padrão oficial

## Processo

### 1. Verificar duplicata

Antes de criar, verifica se já existe skill similar no registry (por nome e descrição).

### 2. Criar SKILL.md

Gera YAML frontmatter com todos os 12+ campos obrigatórios.

### 3. Criar run.py

Gera Python script com função main, docstring, e argparse.

### 4. Criar testes

3 testes de fumaça em `tests/`.

### 5. Atualizar registry

Adiciona ao `skills.yaml` e ao `sectors.yaml`.

## Output

```
{
  "status": "created|duplicate|refatorada",
  "skill_id": "nova-skill",
  "files": ["SKILL.md", "run.py", "tests/test_1.py"],
  "registry_updated": true,
  "dry_run": true,
  "next_action": "Aprovar criacao? (sim/nao)"
}
```
