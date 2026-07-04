# core/storage/json_unit_repo.py

from typing import Optional, List
from ..models import Unit
from ..repositories import UnitRepository
from .base import JSONRepository

class JSONUnitRepository(JSONRepository[Unit], UnitRepository):
    def __init__(self, file_path: str = "data/units.json"):
        super().__init__(file_path, Unit)

    def get_by_plant(self, plant_id: str) -> List[Unit]:
        return [u for u in self.get_all() if u.plant_id == plant_id]

    def get_by_code(self, code: str, plant_id: str) -> Optional[Unit]:
        for u in self.get_all():
            if u.code == code and u.plant_id == plant_id:
                return u
        return None

    def get_by_fuel_type(self, fuel_type: str) -> List[Unit]:
        return [u for u in self.get_all() if u.fuel_type == fuel_type]