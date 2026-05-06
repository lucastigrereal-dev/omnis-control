# Conflictos — Creative Production Recovery (2026-05-04)

## Stash Original
- `stash@{0}` — `wip-fase1-claude-code-travou-2026-05-04` (consumido)

## Conflictos Detectados

### 1. `config/paths.yaml` — Path skills desatualizado
- **Stash version**: referencia `~/.claude/skills`
- **Fix**: alterado para `~/omnis-control/skills` em `claude_skills_path` e `local_search_roots`

### 2. `src/runners/skill_runner.py` — Path skills hardcoded
- **Stash version**: `SKILLS_PATH = Path.home() / ".claude" / "skills"`
- **Fix**: `SKILLS_PATH = Path(os.getenv("OMNIS_SKILLS_PATH") or str(PROJECT_ROOT / "skills"))`

### 3. `src/utils/safe_paths.py` — `resolve_skill_path` hardcoded
- **Stash version**: apontava para `~/.claude/skills`
- **Fix**: usa `CONTROL_DIR / "skills"` com env override

### 4. `tests/test_safe_paths.py` — `test_resolve_skill_real`
- **Stash version**: listava skills de `~/.claude/skills`
- **Fix**: lista de `CONTROL_DIR / "skills"` (17 skills do projeto)

## Arquivos Backup
- `_temp_merge_backup/` — versões conflitantes originais (removido pós-recovery)

## Decisões
| Decisão | Justificativa |
|---------|--------------|
| NÃO merge/push | Operador explicitou: só commit local |
| NÃO feature creep | Recovery é estabilização, não expansão |
| 17 skills incluidas | run.py + SKILL.md + manifest.json — todas COMPLETO |
