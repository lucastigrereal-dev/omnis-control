# OMNIS Release Candidate Checklist

## RC Local — Gates

- [ ] Working tree limpo no escopo
- [ ] Suite completa passou (ou falhas só pré-existentes)
- [ ] Wave registry atualizado
- [ ] Current state atualizado
- [ ] Nenhum segredo nos diffs
- [ ] Nenhum arquivo KRATOS tocado
- [ ] Nenhum deploy executado
- [ ] Nenhum push executado
- [ ] Handoff criado em `.claude/state/last-handoff.md`
- [ ] `python scripts/omnis_state_check.py` → ALL GOOD
- [ ] `python scripts/omnis_guard_check.py` → sem P0 reais

## GO / NO-GO

**GO:** Todos os items acima check.
**NO-GO:** Qualquer item falhou → reportar blocker específico.
**CONDITIONAL:** Falhas pré-existentes apenas → documentar e GO.

## Após RC
- Commit final da consolidação
- Reportar ao Lucas: pronto para revisão humana
- NÃO fazer push — Lucas decide quando
