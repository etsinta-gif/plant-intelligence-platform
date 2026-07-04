# core/models/equipment.py

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from .base import Entity

if TYPE_CHECKING:
    from .instrument import Instrument

@dataclass
class Equipment(Entity):
    code: str = ""
    subsystem_id: str = ""
    instruments: List["Instrument"] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.code:
            self.code = self.name[:6].upper()

    def add_instrument(self, instrument: "Instrument"):
        if instrument not in self.instruments:
            self.instruments.append(instrument)
            if instrument.equipment_id != self.id:
                instrument.equipment_id = self.id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"code": self.code, "subsystem_id": self.subsystem_id, "instrument_ids": [i.id for i in self.instruments]})
        return data