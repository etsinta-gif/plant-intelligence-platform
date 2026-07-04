# core/models/unit.py

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from .base import Entity

if TYPE_CHECKING:
    from .asset import Asset

@dataclass
class Unit(Entity):
    code: str = ""
    plant_id: str = ""
    fuel_type: str = ""
    assets: List["Asset"] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.code:
            self.code = self.name[:6].upper()

    def add_asset(self, asset: "Asset"):
        if asset not in self.assets:
            self.assets.append(asset)
            if asset.unit_id != self.id:
                asset.unit_id = self.id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"code": self.code, "plant_id": self.plant_id, "fuel_type": self.fuel_type, "asset_ids": [a.id for a in self.assets]})
        return data