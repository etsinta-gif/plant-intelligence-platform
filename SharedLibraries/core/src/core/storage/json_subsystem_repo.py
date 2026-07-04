# core/storage/json_subsystem_repo.py

from typing import Optional, List
from ..models import Subsystem
from ..repositories import SubsystemRepository
from .base import JSONRepository

class JSONSubsystemRepository(JSONRepository[Subsystem], SubsystemRepository):
    def __init__(self, file_path: str = "data/subsystems.json"):
        super().__init__(file_path, Subsystem)

    def get_by_asset(self, asset_id: str) -> List[Subsystem]:
        return [s for s in self.get_all() if s.asset_id == asset_id]

    def get_by_code(self, code: str, asset_id: str) -> Optional[Subsystem]:
        for s in self.get_all():
            if s.code == code and s.asset_id == asset_id:
                return s
        return None