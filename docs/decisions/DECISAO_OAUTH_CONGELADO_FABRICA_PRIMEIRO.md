# Decisao Arquitetural: OAuth Congelado — Fabrica Primeiro

**Data:** 2026-05-09
**Operador:** Lucas Tigre
**Status:** ATIVA

---

## Decisao

OAuth Meta esta **congelado** temporariamente.

A prioridade agora e a fabrica offline de entregaveis.
Postar e transporte. Primeiro a fabrica precisa gerar pacotes uteis, validaveis, exportaveis e postáveis manualmente.

---

## Motivo

```text
ANTES (eixo antigo):
OAuth -> Post real -> Validar sistema

AGORA (eixo novo):
Entregaveis offline -> Testes de fabrica -> Qualidade -> Export -> So depois OAuth
```

A maior parte dos entregaveis do OMNIS nao precisa de OAuth:
- carrossel
- reels package
- post simples
- campanha
- calendario
- legenda
- briefing visual
- manifest
- export/zip
- checklist de publicacao manual
- relatorio de entrega

Nada disso precisa de token Meta.

---

## Principio

> **OMNIS primeiro vira fabrica completa de entregaveis. Postar e so transporte.**
>
> **Nao precisamos da chave da Meta para fabricar o produto.
> A Meta e so o caminhao. Primeiro a fabrica tem que produzir mercadoria boa.**

---

## Condicao para voltar ao OAuth

- 5 pacotes offline uteis/validados com status READY; OU
- Decisao humana explicita de Lucas.

Nenhuma sessao automatica pode reverter esta decisao sem a condicao acima.

---

## Impacto no Roadmap

| Fase | Descricao | Status |
|---|---|---|
| P1.8 | Offline Factory Stabilization | ATUAL |
| P1.9 | Asset Assignment Center | Proximo |
| P2.0 | Render Engine HTML/PNG | Futuro |
| P2.1 | Video Edit Plan + FFmpeg Dry Run | Futuro |
| P2.2 | Campaign Package 10 Posts | Futuro |
| P2.3 | Manual Publishing Tracker | Futuro |
| P2.4 | Client Delivery ZIP | Futuro |
| P2.5 | Quality Scoring Layer | Futuro |
| P1.6 | Manual OAuth Gate | CONGELADO |

---

## O que NAO fazer enquanto esta decisao estiver ativa

- NAO executar OAuth
- NAO chamar Meta API
- NAO conectar contas reais
- NAO criar package-campaign (P2.2)
- NAO criar package-calendar (nao priorizado)
- NAO testar post real

---

## Arquivos afetados por esta decisao

- `src/offline_factory/` — foco principal de desenvolvimento
- `docs/state/OMNIS_STATE_CURRENT.md` — estado atualizado
- `docs/night_shift/CURRENT_HANDOFF.md` — handoff atualizado
