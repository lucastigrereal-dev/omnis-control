# OMNIS State — Apos P6.4 (Capability Forge Lite completo)

**Data:** 2026-05-09
**Branch:** master
**Fase concluida:** P6 Capability Forge Lite — d41d1ce
**Testes:** 1628 passed, 4 skipped, 0 failures

---

## Decisao estrategica

**OAuth Meta congelado. Fabrica offline e prioridade.**

Ver: `docs/decisions/DECISAO_OAUTH_CONGELADO_FABRICA_PRIMEIRO.md`

---

## Capability Forge Lite — pipeline completo

```
CapabilityGap (detectado pelo capability_gap detector)
  → forge-lite propose <gap_id>           → CapabilityProposal
  → forge-lite export-spec <proposal_id>  → 5 arquivos em exports/capability_specs/
  → forge-lite validate-spec <proposal_id>→ validacao de integridade
  → forge-lite request-approval <id>      → ApprovalRequest (pending)
  → forge-lite mark-approved <id>         → status = approved
  → forge-lite register <id>              → entrada em capabilities.yaml (planned)
  → match_capabilities(include_planned=True) → visivel no matcher
```

---

## Modulos P6

```
src/capability_forge_lite/
  models.py          — CapabilityProposal + status + impl_type constants
  proposal.py        — propose_from_gap() com sector→impl_type mapping
  store.py           — ProposalStore append-only JSONL
  spec_exporter.py   — export_spec() gera 5 arquivos de spec
  spec_validator.py  — validate_spec() verifica integridade dos arquivos
  approval_bridge.py — request/approve/reject via approval center
  registrar.py       — register_capability() escreve em capabilities.yaml
  errors.py          — GapNotFoundError, ProposalNotFoundError, etc.

src/skill_matcher/matcher.py  — include_planned flag adicionado
```

---

## Entregaveis offline funcionais

| Tipo | Comando | Status possivel |
|---|---|---|
| Carrossel | `offline package-carousel` | blocked / partial / ready |
| Reels Script | `offline package-reels` | blocked / ready |
| Post Simples | `offline package-post` | blocked / partial / ready |
| Validacao | `offline validate` | score 0-100 |
| ZIP Export | `offline zip` | ok |

---

## Testes P6

```
tests/capability_forge_lite/: 57 testes
  test_models.py        5
  test_store.py         5
  test_proposal.py      7
  test_cli.py           6
  test_spec_exporter.py 9
  test_spec_validator.py 7
  test_approval_bridge.py 8
  test_registrar.py     8
  test_cli (exporter/validator CLI) incluidos no test_cli.py

tests/e2e/test_p6_gap_to_planned_capability.py: 12 testes

TOTAL P6: 69 testes novos
TOTAL SUITE: 1628 passed, 4 skipped
```

---

## Bloqueios ativos

- **OAuth Meta** — congelado por decisao estrategica
- **Post real** — bloqueado ate OAuth + revisao humana

---

## Proximas fases possiveis

| Fase | Descricao | Prioridade |
|---|---|---|
| P2.0 | Render Engine HTML/PNG | Media |
| P2.1 | Video Edit Plan + FFmpeg | Media |
| P2.2 | Campaign Package 10 Posts | Media |
| P7.x | (a definir pelo operador) | — |
| P1.6 | Manual OAuth Gate | CONGELADO |
