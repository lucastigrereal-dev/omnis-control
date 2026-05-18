# OMNIS Decision Tree

## Fluxo de Decisão por Sessão

```
INÍCIO
  │
  ├─ Estou no repo OMNIS? (pwd == C:\Users\lucas\omnis-control)
  │   └─ NÃO → cd C:\Users\lucas\omnis-control e recomeçar
  │
  ├─ Branch correta? (git branch --show-current)
  │   └─ NÃO → Identificar branch esperada no CURRENT_STATE.md
  │
  ├─ Working tree limpo no escopo?
  │   └─ NÃO → Classificar arquivos (P0? fora do escopo? wave anterior?)
  │       ├─ P0 (segredo) → PARAR, reportar
  │       ├─ Fora do escopo → Documentar, não commitar
  │       └─ Wave anterior → Avaliar se precisa commit
  │
  ├─ Roadmap ativo claro?
  │   ├─ G14 App Factory → Ver WAVE_REGISTRY.md, próxima wave G14
  │   ├─ CCOS RuntimeBridge → Ver WAVE_REGISTRY.md, próxima wave CCOS
  │   └─ Ambos ou nenhum → PARAR, pedir Lucas
  │
  ├─ Próxima wave clara?
  │   └─ SIM → Pode executar sozinho?
  │       ├─ SIM → Executar wave (RUNBOOK.md)
  │       └─ NÃO → Por quê?
  │           ├─ Falta autorização → Pedir Lucas
  │           ├─ Bloqueador P0 → Resolver ou reportar
  │           └─ Depende de outra wave → Aguardar
  │
  └─ Nada claro → /omnis-next ou pedir Lucas
```

## Decisões Rápidas

| Situação | Decisão |
|---|---|
| Teste pré-existente falhou | Documentar, prosseguir |
| Teste novo falhou | Parar, corrigir |
| Working tree tem 1-2 arquivos fora do escopo | Documentar, não commitar |
| Working tree tem muitos arquivos estranhos | Parar, classificar |
| Segredo encontrado | NÃO ler, registrar P0, parar |
| Wave duplicada detectada | Parar, reportar |
| Commit trivial (typo, doc) | Fazer (seletivo) |
| Commit de feature | Testes primeiro, depois commit |
