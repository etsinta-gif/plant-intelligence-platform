# core/models/company.py

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from .base import Entity

if TYPE_CHECKING:
    from .plant import Plant

@dataclass
class Company(Entity):
    code: str = ""
    plants: List["Plant"] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.code:
            self.code = self.name[:4].upper()

    def add_plant(self, plant: "Plant"):
        if plant not in self.plants:
            self.plants.append(plant)
            if plant.company_id != self.id:
                plant.company_id = self.id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"code": self.code, "plant_ids": [p.id for p in self.plants]})
        return data