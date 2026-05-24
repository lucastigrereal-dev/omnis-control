---
name: schema-design
description: Design de schemas PostgreSQL para o OMNIS — padrões de tabela, migrations, nomenclatura
version: 1.0.0
tags: [schema, database, postgresql, omnis]
---

## Schema Design OMNIS

**Padrão de tabelas:**
- PK: sempre `UUID PRIMARY KEY DEFAULT uuid_generate_v4()`
- Timestamps: `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ`
- Soft delete: campo `deleted_at TIMESTAMPTZ` (nunca deletar fisicamente dados críticos)
- JSONB para metadados flexíveis com índice GIN
- pgvector: `embedding vector(1536)` com índice `ivfflat`

**Migrações:**
- Arquivo: `migrations/YYYYMMDD_descricao.sql`
- Nunca DROP sem backup plan
- Sempre reversível (incluir DOWN script)
- Testar em ambiente local antes de produção

**Nomenclatura:**
- Tabelas: snake_case plural (`capability_versions`)
- Colunas: snake_case (`created_by`, `risk_level`)
- Índices: `idx_tabela_coluna`

**Sempre criar:** índice na coluna de busca mais comum + índice de embedding para similarity search.
