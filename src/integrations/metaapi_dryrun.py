"""MetaAPIDryRun — mock local da Meta Graph API.

Em vez de chamar a API real, persiste o resultado em JSONL
em data/dryrun_publishes/ para inspecao posterior.
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnis.integrations.metaapi_dryrun")

DRY_RUN_DIR = Path(__file__).parent.parent.parent / "data" / "dryrun_publishes"


class MetaAPIDryRun:
    """Mock do MetaAPIClient — registra em JSONL, nunca chama API real."""

    def __init__(self, dry_run_dir: Optional[Path] = None):
        self.dir = dry_run_dir or DRY_RUN_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    async def publish(
        self,
        caption: str,
        hashtags: List[str],
        media_urls: List[str],
        format: str,
        idempotency_key: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Simula publicacao — retorna ID ficticio e persiste em JSONL."""
        mock_id = f"dryrun_{uuid.uuid4().hex[:12]}"
        entry = {
            "id": mock_id,
            "idempotency_key": idempotency_key,
            "caption": caption,
            "hashtags": hashtags,
            "media_urls": media_urls,
            "format": format,
            "status": "published_dry_run",
            "timestamp": datetime.utcnow().isoformat(),
        }
        log_path = self.dir / f"{idempotency_key[:16]}.jsonl"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

        logger.info(
            "dry_run_publish",
            extra={**entry, "log_path": str(log_path)},
        )
        return entry

    async def get_media_stats(self, media_id: str) -> Dict[str, Any]:
        """Simula retorno de metricas."""
        return {
            "id": media_id,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "reach": 0,
            "impressions": 0,
            "source": "dry_run",
        }

    def list_publishes(self) -> List[Dict[str, Any]]:
        """Lista todas as publicacoes dry-run."""
        entries = []
        for f in sorted(self.dir.glob("*.jsonl")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return entries
