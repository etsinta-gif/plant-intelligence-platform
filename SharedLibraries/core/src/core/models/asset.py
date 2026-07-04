# core/models/asset.py

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from datetime import date
from .base import Entity

if TYPE_CHECKING:
    from .subsystem import Subsystem

@dataclass
class Asset(Entity):
    code: str = ""
    unit_id: str = ""
    asset_type: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    installation_date: Optional[date] = None
    subsystems: List["Subsystem"] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.code:
            self.code = self.name[:6].upper()

    def add_subsystem(self, subsystem: "Subsystem"):
        if subsystem not in self.subsystems:
            self.subsystems.append(subsystem)
            if subsystem.asset_id != self.id:
                subsystem.asset_id = self.id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "code": self.code,
            "unit_id": self.unit_id,
            "asset_type": self.asset_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "installation_date": self.installation_date.isoformat() if self.installation_date else None,
            "subsystem_ids": [s.id for s in self.subsystems],
        })
        return data