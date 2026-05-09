# Manual Publishing Tracker

**Modulo:** `src/manual_publishing/`
**Fase:** P2.3
**Status:** Ativo

---

## Responsabilidade

Registra publicacoes manuais feitas por humano.
Sem API. Sem OAuth. Sem Meta.

---

## Dados locais

```
data/manual_publishing_log.jsonl
```

---

## CLI

```bash
python jarvis.py manual-publish mark <package_id>
python jarvis.py manual-publish mark <package_id> --platform instagram --url "https://..."
python jarvis.py manual-publish list
python jarvis.py manual-publish show <package_id>
```

---

## Campos

| Campo | Tipo | Descricao |
|---|---|---|
| package_id | str | ID do pacote postado |
| platform | str | instagram / tiktok / etc |
| posted_at | str | ISO 8601 UTC |
| posted_by | str | Quem postou (default: lucas) |
| url | Optional[str] | URL do post |
| notes | Optional[str] | Notas |
| status | str | posted |
