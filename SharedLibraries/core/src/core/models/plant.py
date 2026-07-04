# core/models/plant.py

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from .base import Entity

if TYPE_CHECKING:
    from .unit import Unit

@dataclass
class Plant(Entity):
    code: str = ""
    company_id: str = ""
    location: str = ""
    units: List["Unit"] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.code:
            self.code = self.name[:6].upper()

    def add_unit(self, unit: "Unit"):
        if unit not in self.units:
            self.units.append(unit)
            if unit.plant_id != self.id:
                unit.plant_id = self.id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"code": self.code, "company_id": self.company_id, "location": self.location, "unit_ids": [u.id for u in self.units]})
        return data