# P1.6A — Safe First Post Plan

**Data:** 2026-05-08

---

## Regras do Primeiro Post Real

1. **NAO usar @lucastigrereal** — bloqueio permanente para primeiro teste
2. Usar **@afamiliatigrereal** (320K, familia) — menor risco entre contas ativas
3. Asset 100% organico — sem contrato, sem copyright, sem crianca exposta
4. Conteudo simples e controlado — idealmente 1 imagem de paisagem/destino generico
5. Lucas acordado e revisando ANTES de publicar
6. OAuth functional e token valido

---

## Candidato Atual (problema)

| Campo | Valor |
|---|---|
| Queue ID | `0b79aa1c` |
| Conta | @lucastigrereal (CRITICAL — 690K) |
| Status | caption_ready |
| Draft ID | `1d482d82` (v2, approved) |
| Asset | AUSENTE |
| CTA | Nao definido |
| Hashtags | Nenhuma |

**Veredito: NAO USAR para primeiro post real.**

---

## Candidato Recomendado

| Campo | Valor |
|---|---|
| Conta | @afamiliatigrereal (MEDIUM — 320K) |
| Status desejado | caption_ready |
| Asset | A definir — imagem organica simples |
| CTA | Opcional para primeiro teste |
| Hashtags | Opcional para primeiro teste |

---

## Passos Concretos (Lucas)

### 1. Verificar/Criar slot para @afamiliatigrereal

```bash
python jarvis.py queue list
```

Se nao existir slot caption_ready para @afamiliatigrereal:

```bash
python jarvis.py queue create @afamiliatigrereal
```

### 2. Selecionar asset seguro

Criterios:
- Imagem propria (foto que Lucas tirou)
- Sem pessoas expostas (paisagem/destino)
- Sem marcas ou contratos comerciais
- Sem localizacao sensivel
- Formato: JPG ou MP4

Ideal: foto de praia, por do sol, comida ou destino generico.

### 3. Atribuir asset ao slot

```bash
python jarvis.py queue assign <queue_id> <asset_id>
```

### 4. Gerar package local

```bash
python jarvis.py post package <queue_id>
```

### 5. Revisar legenda e midia

- Confirmar que nao tem placeholder [BOT]
- Confirmar que texto combina com a midia
- Verificar se CTA e hashtags fazem sentido (se preenchidos)

### 6. Rodar preflight final

```bash
python jarvis.py post preflight
```

Confirmar 8/8 passam.

### 7. Publicar (futuro, com OAuth real)

```bash
# Comando ainda a ser implementado
python jarvis.py post publish <queue_id> --account @afamiliatigrereal
```

---

## O que NAO fazer

- NAO testar em @lucastigrereal
- NAO usar asset de cliente/contrato
- NAO publicar sem revisar legenda + midia
- NAO publicar com OAuth dry-run
- NAO publicar sem Lucas acordado

---

**Plano pronto. Execucao quando OAuth for GO.**
