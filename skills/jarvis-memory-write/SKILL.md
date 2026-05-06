---
name: jarvis-memory-write
description: |
  Salva resultado de execução em Akasha + Notion + Git. CHAMADA OBRIGATÓRIA
  ao final de qualquer skill setorial executada. Sem isso, não há aprendizado.
trigger:
  - ao final de skill setorial
  - quando Lucas explicitamente pede "salva isso"
sector: cross-cutting
risk: medium
model: sonnet
approval_required:
  - overwrite_critical_notion_page
  - mass_chunk_insert  # >100 chunks de uma vez
status: active
version: 1.0
---

# Skill: jarvis-memory-write

Skill cross-cutting — chamada ao final de qualquer skill setorial para persistir aprendizado.

## Quando usar

- Ao final de qualquer skill setorial (sdr-hotel, content-machine, campaign-planner etc.)
- Quando Lucas pede explicitamente "salva isso" / "registra" / "grava no Akasha"
- Quando uma decisão estratégica é tomada
- Quando um resultado mensurável acontece (fechamento, engajamento real, erro corrigido)

## Processo

### 1. Inserir chunk no Akasha

```python
import requests, psycopg2, hashlib, json
from datetime import datetime

DB = {"host":"localhost","port":5432,"user":"akasha","password":"akasha123","database":"akasha"}
OLLAMA = "http://localhost:11434/api/embeddings"

def salvar_akasha(conteudo: str, setor: str, skill_origem: str, tags: list[str]) -> dict:
    # Gera fingerprint para evitar duplicatas
    fingerprint = hashlib.sha256(conteudo.encode()).hexdigest()[:16]

    # Verifica duplicata
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM memoria_conversas WHERE titulo LIKE %s LIMIT 1", (f"%{fingerprint}%",))
    if cur.fetchone():
        cur.close(); conn.close()
        return {"status": "duplicate_skipped", "fingerprint": fingerprint}

    # Gera embedding
    r = requests.post(OLLAMA, json={"model":"nomic-embed-text","prompt":conteudo}, timeout=30)
    emb = r.json().get("embedding")

    metadata = {
        "setor": setor,
        "skill_origem": skill_origem,
        "tags": tags,
        "fingerprint": fingerprint,
        "timestamp": datetime.utcnow().isoformat(),
    }

    cur.execute("""
        INSERT INTO memoria_conversas (titulo, summary, embedding, metadata)
        VALUES (%s, %s, %s::vector, %s)
        RETURNING id
    """, (
        f"[{skill_origem}] {conteudo[:80]} | {fingerprint}",
        conteudo[:500],
        str(emb),
        json.dumps(metadata),
    ))
    chunk_id = cur.fetchone()[0]
    conn.commit()
    cur.close(); conn.close()
    return {"status": "saved", "chunk_id": chunk_id, "fingerprint": fingerprint}
```

### 2. Atualizar Notion (se setor tem notion_dashboard em sectors.yaml)

```python
# Verificar se setor tem dashboard Notion
import yaml

with open("/c/Users/lucas/.claude/registry/sectors.yaml") as f:
    sectors = yaml.safe_load(f)

setor_cfg = next((s for s in sectors["sectors"] if s["id"] == setor), None)
notion_url = setor_cfg.get("notion_dashboard") if setor_cfg else None

if notion_url:
    # Append bloco de texto na página Notion correspondente
    # REQUER: NOTION_TOKEN configurado no .env
    # Bloco: data + skill + resumo 2-3 linhas
    # Se NOTION_TOKEN ausente: registra pendência em ~/.claude/PENDENCIAS_NOTION.md
    pass
```

> ⚠️ **Bloqueio ativo:** NOTION_TOKEN não configurado. Até resolver, salva pendências em `~/.claude/PENDENCIAS_NOTION.md` com data + conteúdo para sync manual.

### 3. Commit Git (se skill modificou código ou arquivo)

```bash
# Só executa se houve mudança de arquivo (verifica git status)
cd ~/[REPO_CORRESPONDENTE]
git status --short
# Se houver mudanças:
git add -A
git commit -m "feat([setor]): [skill_origem] — [resumo 1 linha]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### 4. Retornar JSON estruturado

```json
{
  "status": "saved",
  "akasha": {
    "chunk_id": 12345,
    "fingerprint": "a1b2c3d4e5f6g7h8"
  },
  "notion": {
    "page_id": "35122eba-8f08-8109-8dae-fcacbe662032",
    "status": "appended"
  },
  "git": {
    "sha": "abc1234",
    "message": "feat(midia_conteudo): content-machine — carousel @oinatalrn gerado"
  }
}
```

Se alguma das 3 operações falhar: retorna parcial com `"status": "partial"` e lista `"errors": [...]`.

## Regras

- **Não trava** se Notion ou git falharem — salva no Akasha e reporta o que ficou pendente
- **Fingerprint obrigatório** — nunca insere chunk duplicado (mesmo conteúdo = skip)
- **Aprovação requerida** antes de: sobrescrever página Notion crítica, inserir >100 chunks de uma vez
- **Custo:** Haiku para síntese final antes de salvar (evitar verbosidade cara)

## Exemplo de uso

```
# Ao final do sdr-hotel:
jarvis-memory-write(
  conteudo="SDR: Hotel Majestic Natal respondeu DM. Proposta enviada R$990. Objeção: 'não preciso de mais seguidores'.",
  setor="comercial_sdr",
  skill_origem="sdr-hotel",
  tags=["hotel", "natal", "objecao", "proposta"]
)
→ {"status":"saved","akasha":{"chunk_id":4521},"notion":{"status":"pending_token"},"git":{"status":"no_changes"}}
```
