# core/repositories/equipment_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Equipment
from .base import Repository

class EquipmentRepository(Repository[Equipment]):
    @abstractmethod
    def get_by_subsystem(self, subsystem_id: str) -> List[Equipment]:
        pass

    @abstractmethod
    def get_by_code(self, code: str, subsystem_id: str) -> Optional[Equipment]:
        pass