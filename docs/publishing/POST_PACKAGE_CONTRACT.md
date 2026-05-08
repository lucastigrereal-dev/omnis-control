# Post Package Contract — P1.4

**Versao:** 0.1.0 | **Data:** 2026-05-08

---

## O que e um PostPackage

Um `PostPackage` e um snapshot local de conteudo pronto para revisao humana antes de publicar no Instagram.

**NUNCA PUBLICA.** E um artefato de dry-run/revisao.

---

## Estrutura (modelo Pydantic v2)

```python
class PostPackage(BaseModel):
    package_id: str          # UUID unico do pacote
    queue_id: str            # ID do slot na fila de conteudo
    account_handle: str      # @handle do Instagram alvo
    format: str              # carrossel | reels | story | single
    caption_text: str        # Legenda completa (texto real, sem [BOT])
    cta: str                 # Call to action (ex: "Link na bio")
    hashtags: List[str]      # Lista de hashtags
    asset_id: Optional[str]  # ID do asset de midia (imagem/video)
    asset_file: str          # Path do arquivo de midia
    warnings: List[str]      # Avisos nao-bloqueantes
    ready: bool              # True = todas as condicoes atendidas
    created_at: str          # Timestamp ISO 8601
```

---

## Condicoes para `ready: true`

1. **Draft aprovado** — `draft.status == "approved"` (ou equivalente `caption_ready` com draft).
2. **Legenda preenchida** — `caption_text` com mais de 10 caracteres.
3. **Sem placeholders** — Nenhum `[BOT]` no texto.
4. **Asset atribuido** — `asset_id` nao-nulo.
5. **Conta ativa** — `account_handle` existe no AccountRegistry com status ativo.

---

## Condicoes que geram `warnings` (nao bloqueiam)

- CTA ausente ou vazio.
- Hashtags vazias.
- Carrossel com menos de 2 imagens.
- Asset com formato nao-ideal (ex: muito pesado, proporcao errada).
- Draft status diferente de `approved` mas com texto valido.

---

## Como criar um pacote

```bash
# Por queue_id especifico
python jarvis.py post package 0b79aa1c
python jarvis.py post package 0b79aa1c --json

# Proximo pronto automatico
python jarvis.py post package
python jarvis.py post package --json
```

---

## O que o PostPackage NAO faz

- NAO chama API do Instagram.
- NAO carrega token OAuth.
- NAO agenda publicacao.
- NAO move arquivos de midia.
- NAO altera estado da fila (status permanece `caption_ready`).
- NAO substitui decisao humana.

---

## Fluxo normal ate publicacao

```
1. omnis post preflight        → verifica se ha algo pronto
2. omnis post package <id>     → gera pacote para revisao
3. [Lucas revisa]              → abre pacote, le legenda, ve asset
4. [Lucas decide]              → GO ou NO-GO
5. omnis post publish <id>     → (FUTURO P1.6) publica de verdade
```

---

## Futuro (P1.5+)

- `omnis post package --account @handle` — busca automatica por conta.
- `omnis post package --format carrossel` — filtra por formato.
- `package.metadata` — metadados adicionais (localizacao, tags, colaboradores).
- `package.preview_url` — URL para preview visual (se disponivel).
