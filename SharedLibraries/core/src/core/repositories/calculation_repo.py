# core/repositories/calculation_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Calculation
from .base import Repository

class CalculationRepository(Repository[Calculation]):
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Calculation]:
        pass

    @abstractmethod
    def get_by_asset_type(self, asset_type: str) -> List[Calculation]:
        pass

    @abstractmethod
    def get_by_category(self, category: str) -> List[Calculation]:
        pass

    @abstractmethod
    def get_active(self) -> List[Calculation]:
        pass