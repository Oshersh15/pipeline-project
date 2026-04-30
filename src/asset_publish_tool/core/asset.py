from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Asset:
    name: str
    asset_type: str
    source_scene: Path
    version: str
    publish_path: str
    author: str
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "asset_type": self.asset_type,
            "source_scene": str(self.source_scene) if self.source_scene else None,
            "version": self.version,
            "publish_path": str(self.publish_path) if self.publish_path else None,
            "author": self.author,
            "created_at": self.created_at,
        }
