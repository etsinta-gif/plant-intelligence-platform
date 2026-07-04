# core/storage/json_calculation_repo.py

from typing import Optional, List
from ..models import Calculation
from ..repositories import CalculationRepository
from .base import JSONRepository

class JSONCalculationRepository(JSONRepository[Calculation], CalculationRepository):
    def __init__(self, file_path: str = "data/calculations.json"):
        super().__init__(file_path, Calculation)

    def get_by_code(self, code: str) -> Optional[Calculation]:
        for c in self.get_all():
            if c.code == code:
                return c
        return None

    def get_by_asset_type(self, asset_type: str) -> List[Calculation]:
        return [c for c in self.get_all() if c.asset_type == asset_type]

    def get_by_category(self, category: str) -> List[Calculation]:
        return [c for c in self.get_all() if c.category == category]

    def get_active(self) -> List[Calculation]:
        return [c for c in self.get_all() if c.is_active]