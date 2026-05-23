"""OMNIS Qdrant Indexer — cria colecoes e indexa drafts. Graceful fallback."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any

QDRANT_URL = "http://localhost:6333"
COLLECTION = "omnis_drafts"
VECTOR_SIZE = 384
ROOT = Path(__file__).parent.parent.parent


def _get_client() -> Any:
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(url=QDRANT_URL, timeout=5)
    except Exception:
        return None


def _embed_text(text: str) -> list[float]:
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2").encode(text).tolist()
    except Exception:
        pass
    digest = list(hashlib.sha256(text.encode()).digest())
    expanded = (digest * 13)[:384]
    return [(b / 127.5) - 1.0 for b in expanded]


def get_status() -> dict[str, object]:
    """Retorna status do Qdrant e colecoes. Nunca lanca excecao."""
    client = _get_client()
    if client is None:
        return {"available": False, "reason": "qdrant-client ausente ou inacessivel",
                "collections": [], "collection_omnis_drafts": False}
    try:
        cols = client.get_collections().collections
        names = [c.name for c in cols]
        counts = {}
        for name in names:
            try:
                counts[name] = client.get_collection(name).points_count
            except Exception:
                counts[name] = -1
        return {"available": True, "collections": names, "collections_count": len(names),
                "points_per_collection": counts, "collection_omnis_drafts": COLLECTION in names}
    except Exception as e:
        return {"available": False, "reason": str(e), "collections": [], "collection_omnis_drafts": False}


def ensure_collection() -> bool:
    """Cria colecao omnis_drafts se nao existir. Retorna True se ok."""
    client = _get_client()
    if client is None:
        return False
    try:
        from qdrant_client.models import Distance, VectorParams
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION not in existing:
            client.create_collection(COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE))
        return True
    except Exception:
        return False


def index_drafts(drafts_path: str | None = None) -> dict[str, object]:
    """Indexa drafts no Qdrant. Retorna {indexed, skipped, errors, fallback_embedding}."""
    client = _get_client()
    if client is None:
        return {"indexed": 0, "skipped": 0, "errors": ["qdrant-client ausente"],
                "collection": COLLECTION, "fallback_embedding": False}
    if not ensure_collection():
        return {"indexed": 0, "skipped": 0, "errors": ["falha ao criar colecao"],
                "collection": COLLECTION, "fallback_embedding": False}

    p = Path(drafts_path) if drafts_path else ROOT / "data" / "caption_drafts.jsonl"
    if not p.exists():
        return {"indexed": 0, "skipped": 0, "errors": [f"nao encontrado: {p}"],
                "collection": COLLECTION, "fallback_embedding": False}

    try:
        drafts = [json.loads(l) for l in p.read_text(encoding="utf-8").strip().splitlines() if l.strip()]
    except Exception as e:
        return {"indexed": 0, "skipped": 0, "errors": [str(e)], "collection": COLLECTION, "fallback_embedding": False}

    try:
        from sentence_transformers import SentenceTransformer  # noqa
        using_fallback = False
    except ImportError:
        using_fallback = True

    from qdrant_client.models import PointStruct
    points, indexed, skipped, errors = [], 0, 0, []

    for draft in drafts:
        did = str(draft.get("id") or draft.get("caption_id") or "")
        content = str(draft.get("content") or draft.get("caption") or "")
        if not content.strip() or not did:
            skipped += 1
            continue
        try:
            vec = _embed_text(content)
            numeric_id = int(hashlib.md5(did.encode()).hexdigest()[:8], 16)
            points.append(PointStruct(id=numeric_id, vector=vec,
                payload={"draft_id": did, "status": draft.get("status",""),
                         "account_id": draft.get("account_id",""), "preview": content[:200]}))
            indexed += 1
        except Exception as e:
            errors.append(f"{did}: {e}"); skipped += 1

    if points:
        try:
            client.upsert(collection_name=COLLECTION, points=points)
        except Exception as e:
            errors.append(f"upsert: {e}"); indexed = 0

    return {"indexed": indexed, "skipped": skipped, "errors": errors,
            "collection": COLLECTION, "fallback_embedding": using_fallback}
