# P6 Final Report — Capability Forge Lite

**Data:** 2026-05-09
**Fase:** P6.0 → P6.4 completa
**Commits:** fb8a6d6 → d41d1ce (5 commits)

---

## Blocos entregues

### P6.0 — Capability Proposal Generator (fb8a6d6)
- `src/capability_forge_lite/models.py` — CapabilityProposal dataclass + 5 status + 5 impl types
- `src/capability_forge_lite/proposal.py` — propose_from_gap() com mapeamento setor→impl_type
- `src/capability_forge_lite/store.py` — ProposalStore append-only JSONL
- `src/capability_forge_lite/errors.py` — GapNotFoundError, ProposalNotFoundError, etc.
- CLI: `forge-lite propose`, `forge-lite list`, `forge-lite show`
- 28 testes

### P6.1 — Capability Spec Exporter (d4ddf12)
- `src/capability_forge_lite/spec_exporter.py` — export_spec() gera 5 arquivos por proposta
- `src/capability_forge_lite/spec_validator.py` — validate_spec() verifica todos os arquivos + manifesto
- CLI: `forge-lite export-spec`, `forge-lite validate-spec`
- `.gitignore` atualizado: `exports/capability_specs/`
- 41 testes acumulados

### P6.2 — Capability Approval Bridge (25906eb)
- `src/capability_forge_lite/approval_bridge.py` — request_proposal_approval(), mark_proposal_approved(), mark_proposal_rejected(), get_approval_status()
- CLI: `forge-lite request-approval`, `forge-lite mark-approved`, `forge-lite mark-rejected`
- Status da proposta sincroniza com outcome do approval center
- 8 testes novos

### P6.3 — Register Approved Capability (f97d9d5)
- `src/capability_forge_lite/registrar.py` — register_capability() escreve em capabilities.yaml com status=planned
- `src/skill_matcher/matcher.py` — flag include_planned=True para surfacear planned caps no matching
- CLI: `forge-lite register`
- 8 testes novos

### P6.4 — Gap → Planned Capability E2E (d41d1ce)
- `tests/e2e/test_p6_gap_to_planned_capability.py` — 12 testes cobrindo pipeline completo
- Fluxos validados: gap→proposal, spec export+validate, approval loop, reject blocks registration, full gap→registered, planned visible in matcher, duplicate raises, network blocked
- 12 testes novos

---

## Pipeline completo

```
CapabilityGap (detectado)
  → propose_from_gap()         → CapabilityProposal (needs_approval ou draft)
  → export_spec()              → 5 arquivos em exports/capability_specs/<proposal_id>/
  → validate_spec()            → report de validacao
  → request_proposal_approval() → ApprovalRequest (pending) linkado a proposta
  → mark_proposal_approved()   → proposta.status = approved
  → register_capability()      → entrada em capabilities.yaml (status: planned)
  → match_capabilities(include_planned=True) → visivel no matcher
```

---

## CLI forge-lite — comandos completos

| Comando | Descricao |
|---|---|
| `forge-lite propose <gap_id>` | Cria proposta a partir de gap |
| `forge-lite list` | Lista proposals |
| `forge-lite show <proposal_id>` | Mostra detalhes |
| `forge-lite export-spec <proposal_id>` | Exporta 5 arquivos de spec |
| `forge-lite validate-spec <proposal_id>` | Valida arquivos exportados |
| `forge-lite request-approval <proposal_id>` | Cria pedido no Approval Center |
| `forge-lite mark-approved <proposal_id>` | Aprova proposta |
| `forge-lite mark-rejected <proposal_id>` | Rejeita proposta |
| `forge-lite register <proposal_id>` | Registra em capabilities.yaml como planned |

---

## Invariantes de seguranca

- Nenhum arquivo de spec contem chaves com prefixo secret/token/password/meta_/instagram_
- Registration requer status=approved (nao apenas approval_id preenchido)
- Duplicata levanta DuplicateCapabilityError (nao sobrescreve silenciosamente)
- Planned caps sao opaque para o matcher por default (require include_planned=True)
- Zero chamadas de rede em qualquer etapa (test_no_network_calls PASS)
