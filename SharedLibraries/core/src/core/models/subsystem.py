# core/models/subsystem.py

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from .base import Entity

if TYPE_CHECKING:
    from .equipment import Equipment

@dataclass
class Subsystem(Entity):
    code: str = ""
    asset_id: str = ""
    equipment: List["Equipment"] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.code:
            self.code = self.name[:6].upper()

    def add_equipment(self, equipment: "Equipment"):
        if equipment not in self.equipment:
            self.equipment.append(equipment)
            if equipment.subsystem_id != self.id:
                equipment.subsystem_id = self.id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"code": self.code, "asset_id": self.asset_id, "equipment_ids": [e.id for e in self.equipment]})
        return data