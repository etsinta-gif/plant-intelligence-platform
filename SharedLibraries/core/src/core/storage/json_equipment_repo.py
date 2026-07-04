# core/storage/json_equipment_repo.py

from typing import Optional, List
from ..models import Equipment
from ..repositories import EquipmentRepository
from .base import JSONRepository

class JSONEquipmentRepository(JSONRepository[Equipment], EquipmentRepository):
    def __init__(self, file_path: str = "data/equipment.json"):
        super().__init__(file_path, Equipment)

    def get_by_subsystem(self, subsystem_id: str) -> List[Equipment]:
        return [e for e in self.get_all() if e.subsystem_id == subsystem_id]

    def get_by_code(self, code: str, subsystem_id: str) -> Optional[Equipment]:
        for e in self.get_all():
            if e.code == code and e.subsystem_id == subsystem_id:
                return e
        return None