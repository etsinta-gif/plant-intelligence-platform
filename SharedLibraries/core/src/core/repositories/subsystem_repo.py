# core/repositories/subsystem_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Subsystem
from .base import Repository

class SubsystemRepository(Repository[Subsystem]):
    @abstractmethod
    def get_by_asset(self, asset_id: str) -> List[Subsystem]:
        pass

    @abstractmethod
    def get_by_code(self, code: str, asset_id: str) -> Optional[Subsystem]:
        pass