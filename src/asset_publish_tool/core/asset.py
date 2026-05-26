"""
Asset data model used by the publishing pipeline.

This module defines the Asset dataclass used for storing publish
metadata, exported file paths, preview data, and GridFS package
references before persistence to MongoDB.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Asset:
    """
    Container representing a published asset and its associated metadata.

    Attributes:
        name (str): Published asset name.
        asset_type (str): Asset category/type.
        source_scene (Path): Original Maya scene path.
        version (str): Published version string.
        publish_path (str): Temporary local publish directory.
        author (str): Username of the publishing user.
        exports (dict): Exported file paths grouped by export type.
        created_at (str): Publish timestamp in ISO format.
        package_file_id (Optional[str]): GridFS package identifier.
        preview_image (Optional[bytes]): Binary preview image data.
    """

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
        """
        Convert the asset into a serialisable metadata dictionary.

        Returns:
            dict: Asset metadata excluding binary preview data.
        """
        return {
            "name": self.name,
            "asset_type": self.asset_type,
            "source_scene": str(self.source_scene) if self.source_scene else None,
            "version": self.version,
            "publish_path": str(self.publish_path) if self.publish_path else None,
            "author": self.author,
            "exports": self.exports,
            "created_at": self.created_at,
        }

    def to_mongo_dict(self) -> dict:
        """
        Convert the asset into a MongoDB-ready document.

        This extends the standard metadata dictionary with
        GridFS package references and binary preview image data.

        Returns:
            dict: MongoDB-ready asset document.
        """
        data = self.to_dict()

        data["package_file_id"] = self.package_file_id
        data["preview_image"] = self.preview_image

        return data
