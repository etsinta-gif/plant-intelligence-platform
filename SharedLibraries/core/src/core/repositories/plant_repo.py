# core/repositories/plant_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Plant
from .base import Repository

class PlantRepository(Repository[Plant]):
    @abstractmethod
    def get_by_company(self, company_id: str) -> List[Plant]:
        pass

    @abstractmethod
    def get_by_code(self, code: str, company_id: str) -> Optional[Plant]:
        pass