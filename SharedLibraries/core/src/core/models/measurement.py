# core/models/measurement.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from .base import Entity

@dataclass
class Measurement(Entity):
    tag_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    value: float = 0.0
    quality: str = "Good"

    def __post_init__(self):
        super().__post_init__()
        if not self.name:
            self.name = f"Measurement at {self.timestamp.isoformat()}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "tag_id": self.tag_id,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "quality": self.quality,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Measurement":
        if data.get("timestamp") and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return super().from_dict(data)