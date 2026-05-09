"""Client delivery models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DeliveryStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ZIPPED = "zipped"


class DeliverySource(str, Enum):
    PACKAGE = "package"
    CAMPAIGN = "campaign"


@dataclass
class Delivery:
    delivery_id: str
    source_type: DeliverySource
    source_id: str
    status: DeliveryStatus
    output_dir: str
    created_at: str
    zip_path: Optional[str] = None
    files_generated: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "delivery_id": self.delivery_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "status": self.status.value,
            "output_dir": self.output_dir,
            "created_at": self.created_at,
            "zip_path": self.zip_path,
            "files_generated": self.files_generated,
            "warnings": self.warnings,
        }
