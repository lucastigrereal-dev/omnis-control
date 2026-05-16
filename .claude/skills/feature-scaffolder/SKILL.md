---
name: feature-scaffolder
description: Criar feature nova com scaffold, testes e dry_run.
---

# feature-scaffolder

## Objetivo
Criar mÃ³dulo novo sem efeito real por padrÃ£o.

## Processo
1. Criar contrato pÃºblico.
2. Criar implementaÃ§Ã£o mÃ­nima.
3. Criar testes antes de ampliar lÃ³gica.
4. dry_run=True como default.
5. Gerar handoff report.

## Proibido
- Chamada externa real.
- Escrita em secrets/export/data runtime.
- AÃ§Ã£o destrutiva.
