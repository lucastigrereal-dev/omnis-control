"""Package generator — creates delivery packages from queue items.

Reuses creative_production/exporter.py for artifact generation.
Adds carousel-specific slides outline and Reels-specific script/audio notes.
NEVER calls external APIs. NEVER publishes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import DeliveryPackage, PackageType, PackageStatus
from .errors import MissingDependencyError, PackageCreationError
from .manifest import generate_manifest

BASE = Path(__file__).resolve().parent.parent.parent
EXPORT_ROOT = BASE / "exports" / "offline_factory"


def _safe_write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _load_caption(queue_id: str) -> Optional[dict]:
    """Load approved caption for a queue item."""
    try:
        from src.caption_approval.drafts import DraftsManager
        dm = DraftsManager()
        # Check all drafts for this queue — find any approved one (prefix match)
        all_drafts = [
            d for d in dm.list_all()
            if (d.queue_id == queue_id or d.queue_id.startswith(queue_id))
            and d.status == "approved"
        ]
        if all_drafts:
            # Most recent approved draft
            return all_drafts[-1].to_dict()
    except Exception:
        pass
    return None


def _load_queue_item(queue_id: str) -> Optional[dict]:
    """Load queue item metadata (date, time, format, account, status). Never raises."""
    try:
        from src.content_queue.queue import Queue
        q = Queue()
        item = q.get(queue_id)
        if item:
            return item.to_dict()
    except Exception:
        pass
    return None


def _load_asset(queue_id: str) -> Optional[dict]:
    """Load video/image asset assigned to this queue slot. Patchable in tests."""
    try:
        from src.content_queue.queue import Queue
        q = Queue()
        item = q.get(queue_id)
        if item and getattr(item, "asset_id", None):
            from src.video_assets.registry import Registry
            reg = Registry()
            asset = reg.get(item.asset_id)
            if asset:
                return asset.to_dict()
    except Exception:
        pass
    return None


def _build_carousel_slides_outline(caption_data: dict | None, num_slides: int = 5) -> str:
    """Generate a carousel slides outline based on caption."""
    lines = ["# Carousel Slides Outline", ""]
    for i in range(1, num_slides + 1):
        if i == 1:
            lines.append(f"## Slide {i} — Hook / Capa")
            lines.append("- Objetivo: Parar o scroll com imagem impactante")
            lines.append("- Texto overlay: Titulo curto e magnetico")
        elif i == num_slides:
            lines.append(f"## Slide {i} — CTA / Fechamento")
            lines.append("- Objetivo: Call-to-action claro")
            lines.append("- Texto overlay: O que fazer depois de ver")
        else:
            lines.append(f"## Slide {i} — Corpo {i - 1}")
            lines.append(f"- Objetivo: Entregar valor ou emocao (parte {i - 1})")
            lines.append("- Texto overlay: Frase curta complementar")
        lines.append("")
    if caption_data:
        lines.append("## Legenda vinculada")
        lines.append(f"- Draft ID: {caption_data.get('draft_id', 'N/A')}")
        lines.append(f"- Objetivo: {caption_data.get('objective', 'N/A')}")
    return "\n".join(lines)


def _build_visual_brief(caption_data: dict | None) -> str:
    """Generate visual direction brief."""
    lines = [
        "# Visual Brief",
        "",
        "## Direcao Visual",
        "- **Paleta de cores:** Tons quentes, naturais, vibrantes",
        "- **Tipografia:** Limpa, legivel em mobile",
        "- **Estilo fotografico:** Natural, luz disponivel, composicao aberta",
        "- **Mood:** Inspirador, aspiracional, acolhedor",
        "",
        "## Especificacoes Tecnicas",
        "- **Resolucao:** 1080x1080 (feed) ou 1080x1350 (portrait)",
        "- **Formato:** JPG/PNG para imagens, MP4 para videos",
        "- **Peso maximo por slide:** 8MB",
        "",
        "## Referencias",
        "- Feed do perfil para consistencia visual",
        "- Manter identidade: @lucastigrereal = autoridade, @afamiliatigrereal = familia",
    ]
    if caption_data:
        lines.append(f"\n## Notas da Legenda\n- Objetivo: {caption_data.get('objective', 'N/A')}")
        cta = caption_data.get('cta', '')
        if cta:
            lines.append(f"- CTA: {cta}")
    return "\n".join(lines)


def _build_seo_metadata(caption_data: dict | None, hashtags: list[str]) -> str:
    """Generate SEO metadata JSON string."""
    import json
    seo = {
        "title": caption_data.get("caption_text", "")[:60] if caption_data else "",
        "description": caption_data.get("caption_text", "")[:150] if caption_data else "",
        "hashtags": hashtags,
        "keywords": [],
        "alt_text_suggestions": [
            "Imagem de paisagem natural com ceu azul",
            "Vista panoramica de destino turistico",
            "Close de comida tipica regional",
            "Familia aproveitando dia ensolarado",
            "Texto com call-to-action sobre o destino",
        ],
    }
    return json.dumps(seo, indent=2, ensure_ascii=False)


def _build_publishing_checklist(package_type: PackageType) -> str:
    """Generate a publishing checklist specific to the package type."""
    common = [
        "[ ] Legenda revisada e aprovada (sem [BOT] placeholders)",
        "[ ] Hashtags conferidas (max 30, relevantes)",
        "[ ] CTA definido e claro",
        "[ ] Conteudo alinhado com identidade do perfil",
        "[ ] Formatos corretos (resolucao, aspecto, peso)",
        "[ ] Credito de imagem/video se necessario",
        "[ ] Lucas acordado e autorizando publicacao",
    ]
    specific = []
    if package_type == PackageType.SINGLE_POST:
        specific = [
            "[ ] Imagem/video com qualidade minima 1080px",
            "[ ] Legenda revisada e sem erros",
            "[ ] Hashtags no comentario (opcional: 1a resposta)",
        ]
    elif package_type == PackageType.CAROUSEL:
        specific = [
            "[ ] Ordem dos slides verificada",
            "[ ] Primeiro slide com hook forte",
            "[ ] Ultimo slide com CTA visivel",
            "[ ] Cada slide funciona isolado (se viralizar sozinho)",
        ]
    elif package_type == PackageType.REELS_SCRIPT:
        specific = [
            "[ ] Primeiros 3 segundos com hook visual forte",
            "[ ] Audio conferido (copyright liberado?)",
            "[ ] Legendas sincronizadas com audio",
            "[ ] Duracao ideal: 15-30s (ou 60-90s para imersivo)",
        ]
    lines = ["# Publishing Checklist", ""] + common + [""] + specific
    return "\n".join(lines)


def create_carousel_package(
    queue_id: str,
    num_slides: int = 5,
    account_handle: str = "",
) -> DeliveryPackage:
    """Create a carousel delivery package from a queue item.

    Args:
        queue_id: The queue item ID (e.g. '0b79aa1c').
        num_slides: Number of slides in the carousel.
        account_handle: Override account handle.

    Returns:
        DeliveryPackage with status and files populated.

    NEVER calls external APIs. NEVER publishes.
    """
    pkg_id = f"carousel_{queue_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_dir = EXPORT_ROOT / pkg_id

    caption_data = _load_caption(queue_id)
    queue_item = _load_queue_item(queue_id)

    warnings: list[str] = []
    blockers: list[str] = []
    next_actions: list[str] = []
    files: list[str] = []
    seo_keywords: list[str] = []
    hashtags: list[str] = []
    cta = ""
    title = f"Carousel Package — {queue_id}"

    if caption_data:
        title = f"Carousel — {caption_data.get('objective', 'conteudo')} — {queue_id[:8]}"
        seo_keywords = caption_data.get("hashtags", [])[:10]
        hashtags = caption_data.get("hashtags", [])
        cta = caption_data.get("cta", "")
        if not account_handle:
            account_handle = caption_data.get("account_handle", "")
    else:
        warnings.append("Nenhuma caption aprovada encontrada — pacote parcial")
        # Fallback: try queue item for account when caption is absent
        if not account_handle and queue_item:
            account_handle = queue_item.get("account_handle", "")
        if not account_handle:
            account_handle = "desconhecido"

    if not caption_data:
        blockers.append("Caption ausente — necessario aprovar legenda antes do pacote")
        next_actions.append("Aprovar legenda: python jarvis.py captions approve <draft_id>")

    asset_data = _load_asset(queue_id)
    has_asset = asset_data is not None

    if not has_asset:
        warnings.append("Nenhum asset atribuido ao slot — pacote parcial")
        next_actions.append("Atribuir asset: python jarvis.py queue assign <queue_id> <asset_id>")

    if not hashtags:
        warnings.append("Hashtags nao definidas")
        next_actions.append("Preencher hashtags no draft de legenda")

    if not cta:
        warnings.append("CTA nao definido")
        next_actions.append("Definir CTA no draft de legenda")

    # Status determination
    status = PackageStatus.PARTIAL
    if not caption_data:
        status = PackageStatus.BLOCKED
    elif has_asset and not warnings:
        status = PackageStatus.READY
    elif not blockers and warnings:
        status = PackageStatus.PARTIAL

    # Generate files
    package_dir.mkdir(parents=True, exist_ok=True)

    # 1. manifest.json (generated after other files)

    # 2. caption.md
    caption_text = caption_data.get("caption_text", "") if caption_data else "(Legenda pendente)"
    _safe_write(package_dir / "caption.md", caption_text)
    files.append("caption.md")

    # 3. seo_metadata.json
    _safe_write(package_dir / "seo_metadata.json", _build_seo_metadata(caption_data, hashtags))
    files.append("seo_metadata.json")

    # 4. visual_brief.md
    _safe_write(package_dir / "visual_brief.md", _build_visual_brief(caption_data))
    files.append("visual_brief.md")

    # 5. slides_outline.md
    _safe_write(package_dir / "slides_outline.md", _build_carousel_slides_outline(caption_data, num_slides))
    files.append("slides_outline.md")

    # 6. publishing_checklist.md
    _safe_write(package_dir / "publishing_checklist.md", _build_publishing_checklist(PackageType.CAROUSEL))
    files.append("publishing_checklist.md")

    # 7. README.md
    readme = [
        f"# {title}",
        "",
        f"**Package ID:** {pkg_id}",
        f"**Queue ID:** {queue_id}",
        f"**Account:** {account_handle}",
        f"**Type:** Carousel ({num_slides} slides)",
        f"**Status:** {status.value}",
        f"**Generated:** {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Arquivos",
    ]
    for f in files:
        readme.append(f"- [{f}]({f})")
    if warnings:
        readme.append("\n## Warnings")
        for w in warnings:
            readme.append(f"- {w}")
    if blockers:
        readme.append("\n## Blockers")
        for b in blockers:
            readme.append(f"- {b}")
    if next_actions:
        readme.append("\n## Next Actions")
        for a in next_actions:
            readme.append(f"- {a}")
    _safe_write(package_dir / "README.md", "\n".join(readme))
    files.append("README.md")

    # Optional HTML preview (no hard dependency)
    try:
        from src.creative_production.html_renderer import render_carousel_preview
        _safe_write(package_dir / "carousel_preview.html", render_carousel_preview(
            title=title, caption=caption_text, slides=num_slides,
        ))
        files.append("carousel_preview.html")
    except Exception:
        pass  # Preview unavailable — not a blocker

    # Build package object
    pkg = DeliveryPackage(
        package_id=pkg_id,
        package_type=PackageType.CAROUSEL,
        title=title,
        account_handle=account_handle,
        source_queue_id=queue_id,
        source_caption_id=caption_data.get("draft_id") if caption_data else None,
        output_dir=str(package_dir),
        files=files,
        status=status,
        warnings=warnings,
        blockers=blockers,
        next_actions=next_actions,
        seo_keywords=seo_keywords,
        hashtags=hashtags,
        cta=cta,
    )

    # Generate manifest last (includes file catalog)
    manifest_path = generate_manifest(pkg, package_dir)
    pkg.manifest_path = str(manifest_path)
    files.append("manifest.json")

    return pkg


def create_reels_script_package(
    queue_id: str,
    account_handle: str = "",
) -> DeliveryPackage:
    """Create a Reels script package from a queue item.

    Args:
        queue_id: The queue item ID.
        account_handle: Override account handle.

    Returns:
        DeliveryPackage with status and files populated.

    NEVER calls external APIs. NEVER publishes.
    """
    pkg_id = f"reels_{queue_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_dir = EXPORT_ROOT / pkg_id

    caption_data = _load_caption(queue_id)

    warnings: list[str] = []
    blockers: list[str] = []
    next_actions: list[str] = []
    files: list[str] = []
    hashtags: list[str] = []
    title = f"Reels Script Package — {queue_id}"

    if caption_data:
        title = f"Reels Script — {caption_data.get('objective', 'conteudo')} — {queue_id[:8]}"
        hashtags = caption_data.get("hashtags", [])
        if not account_handle:
            account_handle = caption_data.get("account_handle", "")
    else:
        warnings.append("Nenhuma caption aprovada encontrada — pacote parcial")
        if not account_handle:
            account_handle = "desconhecido"
        blockers.append("Caption ausente")
        next_actions.append("Aprovar legenda antes do script de Reels")

    if not account_handle or account_handle == "desconhecido":
        blockers.append("Conta desconhecida — necessario definir account_handle")

    status = PackageStatus.PARTIAL
    if not caption_data:
        status = PackageStatus.BLOCKED
    elif not blockers and not warnings:
        status = PackageStatus.READY

    package_dir.mkdir(parents=True, exist_ok=True)

    # 1. caption.md
    caption_text = caption_data.get("caption_text", "") if caption_data else "(Legenda pendente)"
    _safe_write(package_dir / "caption.md", caption_text)
    files.append("caption.md")

    # 2. script.md
    script_lines = [
        "# Reels Script",
        "",
        "## Hook (0-3s)",
        "- Visual: [ABERTURA IMPACTANTE — definir]",
        "- Audio: [SOM ou FALA INICIAL — definir]",
        "- Texto overlay: Frase magnetica em 3-5 palavras",
        "",
        "## Corpo (3-25s)",
        "- Cena 1: [DESCREVER] — duracao ~7s",
        "- Cena 2: [DESCREVER] — duracao ~7s",
        "- Cena 3: [DESCREVER] — duracao ~8s",
        "",
        "## Fechamento (ultimos 5s)",
        "- CTA visual: [O QUE APARECE NA TELA]",
        "- Audio final: [SOM ou FALA FINAL]",
        "",
        "## Legenda vinculada",
    ]
    if caption_data:
        script_lines.append(f"Draft: {caption_data.get('draft_id', 'N/A')}")
        script_lines.append(f"Objetivo: {caption_data.get('objective', 'N/A')}")
    _safe_write(package_dir / "script.md", "\n".join(script_lines))
    files.append("script.md")

    # 3. shot_list.md
    _safe_write(package_dir / "shot_list.md", (
        "# Shot List\n\n"
        "| # | Tipo | Descricao | Duracao | Transicao | Audio |\n"
        "|---+------+-----------+---------+-----------+-------|\n"
        "| 1 | Abertura | Hook visual forte | 0-3s | Corte seco | Som ambiente ou fala |\n"
        "| 2 | Corpo | Desenvolvimento | 3-10s | Suave | Musica de fundo |\n"
        "| 3 | Corpo | Clímax / emocao | 10-20s | Corte | Musica de fundo |\n"
        "| 4 | Corpo | Resolucao | 20-25s | Suave | Musica de fundo |\n"
        "| 5 | Fechamento | CTA | 25-30s | Fade out | Fala final + logo |\n"
    ))
    files.append("shot_list.md")

    # 4. voiceover.md
    _safe_write(package_dir / "voiceover.md", (
        "# Voiceover Guide\n\n"
        "## Tom\n- Natural, conversacional, entusiasta\n- Velocidade: Moderada (nem rapido, nem arrastado)\n\n"
        "## Instrucoes\n- Pausa de 1s entre secoes\n- Enfatizar palavras-chave (destino, emocao, acao)\n"
        "- Respirar antes do CTA final\n\n"
        "## Texto sugerido\n```\n[HOOK — 3s]\n[DESENVOLVIMENTO — 20s]\n[CTA — 5s]\n```\n\n"
        "## Notas\n- Gravar em ambiente silencioso\n- Testar com fone de ouvido\n- Manter distancia constante do microfone\n"
    ))
    files.append("voiceover.md")

    # 5. editing_notes.md
    _safe_write(package_dir / "editing_notes.md", (
        "# Editing Notes\n\n"
        "## Software Sugerido\n- CapCut (gratuito, mobile+desktop)\n- InShot (mobile)\n\n"
        "## Ordem de Edicao\n"
        "1. Importar assets de video/imagem\n"
        "2. Cortar cenas na ordem do shot list\n"
        "3. Adicionar musica de fundo (verificar copyright)\n"
        "4. Sincronizar cortes com batida da musica\n"
        "5. Adicionar texto overlay nos momentos certos\n"
        "6. Ajustar cor/exposicao\n"
        "7. Exportar 1080x1920 (9:16) — 30fps\n"
        "8. Assistir 3x antes de publicar\n"
    ))
    files.append("editing_notes.md")

    # 6. publishing_checklist.md
    _safe_write(package_dir / "publishing_checklist.md", _build_publishing_checklist(PackageType.REELS_SCRIPT))
    files.append("publishing_checklist.md")

    # 7. README.md
    readme = [
        f"# {title}",
        "",
        f"**Package ID:** {pkg_id}",
        f"**Queue ID:** {queue_id}",
        f"**Account:** {account_handle}",
        f"**Type:** Reels Script",
        f"**Status:** {status.value}",
        f"**Generated:** {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Arquivos",
    ]
    for f in files:
        readme.append(f"- [{f}]({f})")
    if warnings:
        readme.append("\n## Warnings")
        for w in warnings:
            readme.append(f"- {w}")
    if blockers:
        readme.append("\n## Blockers")
        for b in blockers:
            readme.append(f"- {b}")
    _safe_write(package_dir / "README.md", "\n".join(readme))
    files.append("README.md")

    pkg = DeliveryPackage(
        package_id=pkg_id,
        package_type=PackageType.REELS_SCRIPT,
        title=title,
        account_handle=account_handle,
        source_queue_id=queue_id,
        source_caption_id=caption_data.get("draft_id") if caption_data else None,
        output_dir=str(package_dir),
        files=files,
        status=status,
        warnings=warnings,
        blockers=blockers,
        next_actions=next_actions,
        hashtags=hashtags,
    )

    manifest_path = generate_manifest(pkg, package_dir)
    pkg.manifest_path = str(manifest_path)
    files.append("manifest.json")

    return pkg


def create_post_package(
    queue_id: str,
    account_handle: str = "",
) -> DeliveryPackage:
    """Create a single-post delivery package from a queue item.

    Minimal package: caption, hashtags, cta, checklist, manifest.
    No slides. No visual brief. No script.
    NEVER calls external APIs. NEVER publishes.
    """
    pkg_id = f"post_{queue_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_dir = EXPORT_ROOT / pkg_id

    caption_data = _load_caption(queue_id)
    queue_item = _load_queue_item(queue_id)
    asset_data = _load_asset(queue_id)
    has_asset = asset_data is not None

    warnings: list[str] = []
    blockers: list[str] = []
    next_actions: list[str] = []
    files: list[str] = []
    hashtags: list[str] = []
    cta = ""
    title = f"Post Package — {queue_id}"

    if caption_data:
        title = f"Post — {caption_data.get('objective', 'conteudo')} — {queue_id[:8]}"
        hashtags = caption_data.get("hashtags", [])
        cta = caption_data.get("cta", "")
        if not account_handle:
            account_handle = caption_data.get("account_handle", "")
    else:
        blockers.append("Caption ausente — necessario aprovar legenda antes do pacote")
        next_actions.append("Aprovar legenda: python jarvis.py captions approve <draft_id>")
        if not account_handle and queue_item:
            account_handle = queue_item.get("account_handle", "")
        if not account_handle:
            account_handle = "desconhecido"

    if not has_asset:
        warnings.append("Nenhum asset atribuido ao slot — pacote parcial")
        next_actions.append("Atribuir asset: python jarvis.py queue assign <queue_id> <asset_id>")

    status = PackageStatus.PARTIAL
    if blockers:
        status = PackageStatus.BLOCKED
    elif has_asset and not warnings:
        status = PackageStatus.READY

    package_dir.mkdir(parents=True, exist_ok=True)

    caption_text = caption_data.get("caption_text", "") if caption_data else "(Legenda pendente)"
    _safe_write(package_dir / "caption.md", caption_text)
    files.append("caption.md")

    _safe_write(package_dir / "hashtags.md", "\n".join(hashtags) if hashtags else "(Hashtags pendentes)")
    files.append("hashtags.md")

    _safe_write(package_dir / "cta.md", cta if cta else "(CTA pendente)")
    files.append("cta.md")

    _safe_write(package_dir / "publishing_checklist.md", _build_publishing_checklist(PackageType.SINGLE_POST))
    files.append("publishing_checklist.md")

    readme = [
        f"# {title}",
        "",
        f"**Package ID:** {pkg_id}",
        f"**Queue ID:** {queue_id}",
        f"**Account:** {account_handle}",
        f"**Type:** Single Post",
        f"**Status:** {status.value}",
        f"**Generated:** {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Arquivos",
    ]
    for f in files:
        readme.append(f"- [{f}]({f})")
    if warnings:
        readme.append("\n## Warnings")
        for w in warnings:
            readme.append(f"- {w}")
    if blockers:
        readme.append("\n## Blockers")
        for b in blockers:
            readme.append(f"- {b}")
    if next_actions:
        readme.append("\n## Next Actions")
        for a in next_actions:
            readme.append(f"- {a}")
    _safe_write(package_dir / "README.md", "\n".join(readme))
    files.append("README.md")

    pkg = DeliveryPackage(
        package_id=pkg_id,
        package_type=PackageType.SINGLE_POST,
        title=title,
        account_handle=account_handle,
        source_queue_id=queue_id,
        source_caption_id=caption_data.get("draft_id") if caption_data else None,
        output_dir=str(package_dir),
        files=files,
        status=status,
        warnings=warnings,
        blockers=blockers,
        next_actions=next_actions,
        hashtags=hashtags,
        cta=cta,
    )

    manifest_path = generate_manifest(pkg, package_dir)
    pkg.manifest_path = str(manifest_path)
    files.append("manifest.json")

    return pkg


def list_packages() -> list[dict]:
    """List all packages on disk."""
    if not EXPORT_ROOT.exists():
        return []
    results = []
    for d in sorted(EXPORT_ROOT.iterdir(), reverse=True):
        if d.is_dir():
            manifest = d / "manifest.json"
            if manifest.is_file():
                import json
                data = json.loads(manifest.read_text(encoding="utf-8"))
                results.append(data)
    return results
