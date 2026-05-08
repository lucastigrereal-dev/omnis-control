# P1.4 — First Post Candidate Report

**Data:** 2026-05-08

---

## Candidato Principal

| Campo | Valor |
|---|---|
| Queue ID | `0b79aa1c` |
| Conta | `@lucastigrereal` (ALERTA: 690K — alto risco) |
| Status | `caption_ready` |
| Formato | carrossel |
| Draft ID | `1d482d82` (v2) |
| Draft Status | `approved` |
| Legenda | "O Brasil tem lugares que parecem cena de..." |
| CTA | Nao definido |
| Hashtags | Nenhuma |
| Asset | **AUSENTE** |

---

## Diagnostico

- Draft aprovado com texto real — nao e placeholder `[BOT]`.
- Nao ha asset atribuido ao slot — publicacao impossivel sem midia.
- CTA e hashtags nao definidos — warnings, nao bloqueios.
- Conta `@lucastigrereal` e a maior do portfolio — risco maximo para teste.

---

## Bloqueio Atual

```
PostPackage ready: False
Warnings:
  - Sem asset atribuido ao slot
  - CTA nao definido (opcional)
  - Hashtags vazias (opcional)
  - Conta de alto risco para primeiro teste
```

---

## Menor Acao Segura para Preparar

```bash
# 1. Atribuir asset (acao humana)
python jarvis.py queue assign 0b79aa1c <asset_id>

# 2. Gerar pacote para revisao
python jarvis.py post package 0b79aa1c

# 3. Se aprovado por Lucas, pacote fica ready
```

---

## Candidato Alternativo (conta menor)

Se `@afamiliatigrereal` (320K) estiver ativa no AccountRegistry e tiver um slot `caption_ready`, seria a conta ideal para o primeiro teste.

Para verificar:
```bash
python jarvis.py accounts list
python jarvis.py queue list
```

---

## Recomendacao

1. **NAO** usar @lucastigrereal para primeiro post real.
2. **Preferir** @afamiliatigrereal ou @natalaivoueu (contas menores).
3. **Preencher** CTA e hashtags antes de publicar.
4. **Atribuir** asset antes de gerar pacote final.
