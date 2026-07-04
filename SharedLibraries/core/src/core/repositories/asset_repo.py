# core/repositories/asset_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Asset
from .base import Repository

class AssetRepository(Repository[Asset]):
    @abstractmethod
    def get_by_unit(self, unit_id: str) -> List[Asset]:
        pass

    @abstractmethod
    def get_by_type(self, asset_type: str) -> List[Asset]:
        pass

    @abstractmethod
    def get_by_code(self, code: str, unit_id: str) -> Optional[Asset]:
        pass