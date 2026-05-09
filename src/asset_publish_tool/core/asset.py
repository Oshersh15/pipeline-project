from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Asset:
    name: str
    asset_type: str
    source_scene: Path
    version: str
    publish_path: str
    author: str
    exports: dict = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    package_file_id: Optional[str] = None
    preview_image: Optional[bytes] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "asset_type": self.asset_type,
            "source_scene": str(self.source_scene) if self.source_scene else None,
            "version": self.version,
            "publish_path": str(self.publish_path) if self.publish_path else None,
            "author": self.author,
            "exports": self.exports,
            "created_at": self.created_at,
            "package_file_id": self.package_file_id,
        }

    def to_mongo_dict(self) -> dict:
        data = self.to_dict()

        data["preview_image"] = self.preview_image

        return data
