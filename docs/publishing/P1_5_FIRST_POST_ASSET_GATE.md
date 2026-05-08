# P1.5 — First Post Asset Gate

**Data:** 2026-05-08

---

## Candidato Atual

| Campo | Valor |
|---|---|
| Queue ID | `0b79aa1c` |
| Conta | `@lucastigrereal` (690K) |
| Status | `caption_ready` |
| Formato | carrossel |
| Draft ID | `1d482d82` (v2, approved) |
| Legenda | "O Brasil tem lugares que parecem cena de..." |
| Asset | **AUSENTE** |
| CTA | Nao definido |
| Hashtags | Nenhuma |

---

## Diagnostico

### 1. O queue item 0b79aa1c pertence a qual conta?

**@lucastigrereal** — a MAIOR conta do portfolio (690K). ALTO RISCO para primeiro teste.

### 2. Existe asset vinculado?

**NAO.** `asset_id` e `None`. Publicacao impossivel sem midia.

### 3. Existe CTA?

**NAO.** CTA e campo opcional para package local, mas recomendado para post real.

### 4. Existem hashtags?

**NENHUMA.** Opcional, mas recomendado para alcance.

### 5. O que falta para package ficar ready?

1. Asset atribuido ao slot
2. CTA definido (opcional)
3. Hashtags preenchidas (opcional)

### 6. Comando exato para atribuir asset

```bash
python jarvis.py queue assign 0b79aa1c <asset_id>
```

Nota: Nao ha comando para listar assets no video-assets CLI nesta build. Lucas precisa saber qual asset_id usar.

### 7. Existe conta menor com slot candidato?

Para verificar:
```bash
python jarvis.py accounts list
python jarvis.py queue list
```

### 8. Recomendacao final

**NAO usar @lucastigrereal para primeiro post real.** Motivos:
- 690K seguidores — qualquer erro tem visibilidade maxima
- Eh a conta principal de autoridade/lifestyle
- Primeiro teste deve ser em conta de menor risco

**Recomendado:** @afamiliatigrereal (320K, conta de familia) ou @natalaivoueu (240K).

**Proxima acao concreta:**
1. Verificar se @afamiliatigrereal tem slot `caption_ready` na queue
2. Se nao tiver, criar novo item na fila para @afamiliatigrereal
3. Atribuir asset seguro (foto de familia ou destino generico)
4. Gerar package local e revisar

---

## Asset Gate Status: NO-GO

```
Blockers:
  - asset ausente
  - conta de alto risco
  - CTA nao definido
  - hashtags vazias
```
