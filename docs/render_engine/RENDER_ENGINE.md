# Render Engine

**Modulo:** `src/render_engine/`
**Fase:** P2.0
**Status:** Ativo

---

## Responsabilidade

Gera preview HTML local para pacotes offline.
Sem CDN. Sem API externa. Sem Canva/Figma. CSS inline puro.

---

## Modulos

```
src/render_engine/
  __init__.py      — exports publicos
  models.py        — RenderResult, RenderStatus
  html_renderer.py — render_html(package_dir) -> str
  service.py       — render_package(), list_renders(), get_render()
  errors.py        — RenderEngineError, PackageNotFoundError, RenderFailedError
```

---

## API

### `render_package(package_id, export_root, render_root) -> RenderResult`

Busca pacote por prefixo de ID, gera HTML e manifest.

### `list_renders(render_root) -> list[dict]`

Lista todos os renders em `exports/rendered/`.

### `get_render(render_id_prefix, render_root) -> Optional[dict]`

Busca render por prefixo de ID.

---

## CLI

```bash
python jarvis.py render --help
python jarvis.py render package <package_id>
python jarvis.py render package <package_id> --json
python jarvis.py render list
python jarvis.py render show <render_id>
```

---

## Saida runtime

```
exports/rendered/<package_dir_name>/
  preview.html
  render_manifest.json
```

---

## Regras

- Nunca chama Meta
- Nunca publica
- CSS inline (sem CDN)
- XSS-safe (HTML escaped)
- Patchavel em testes
