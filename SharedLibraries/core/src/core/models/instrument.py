# core/models/instrument.py

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from .base import Entity

if TYPE_CHECKING:
    from .tag import Tag

@dataclass
class Instrument(Entity):
    code: str = ""
    equipment_id: str = ""
    instrument_type: str = ""
    unit: str = ""
    tags: List["Tag"] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.code:
            self.code = self.name[:6].upper()

    def add_tag(self, tag: "Tag"):
        if tag not in self.tags:
            self.tags.append(tag)
            if tag.instrument_id != self.id:
                tag.instrument_id = self.id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "code": self.code,
            "equipment_id": self.equipment_id,
            "instrument_type": self.instrument_type,
            "unit": self.unit,
            "tag_ids": [t.id for t in self.tags],
        })
        return data