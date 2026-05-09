# B8A Initial Gate — Real Asset Inbox Read-Only Scanner

**Data:** 2026-05-09 | **Branch:** master

## Estado verificado

| Item | Valor |
|---|---|
| Branch | master |
| B6 commit | 1951ee7 |
| B7 commit | 69e3f0d |
| B6 isolado | 48/48 PASS |
| B7 isolado | 21/21 PASS |
| B6+B7 juntos | 69/69 PASS |
| CP2 full suite | 1250/1250 PASS |
| src/missions/ | preservado, nao tocado |

## Decisao

B8A autorizado: scanner read-only apenas.

- NÃO import
- NÃO assign
- NÃO move
- NÃO copy
- NÃO delete

## Escopo B8A

Scanner lê metadata de arquivo sem abrir conteúdo:
- Extensões permitidas: `.jpg .jpeg .png .webp .mp4 .mov .m4v`
- Fingerprint: SHA256 em chunks de 8KB (nunca carrega arquivo inteiro na memória)
- Limite default: 500 arquivos
- Exclude default: `.git __pycache__ node_modules .venv venv exports`
- Arquivos >2GB marcados como `too_large` sem abrir

## Proximos blocos

- B8B — Safe Import Registry (copiar selecionado para quarentena local)
- B8C — Assign Real Asset → Package READY
