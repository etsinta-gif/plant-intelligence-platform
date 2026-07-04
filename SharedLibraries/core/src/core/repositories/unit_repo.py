# core/repositories/unit_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Unit
from .base import Repository

class UnitRepository(Repository[Unit]):
    @abstractmethod
    def get_by_plant(self, plant_id: str) -> List[Unit]:
        pass

    @abstractmethod
    def get_by_code(self, code: str, plant_id: str) -> Optional[Unit]:
        pass

    @abstractmethod
    def get_by_fuel_type(self, fuel_type: str) -> List[Unit]:
        pass