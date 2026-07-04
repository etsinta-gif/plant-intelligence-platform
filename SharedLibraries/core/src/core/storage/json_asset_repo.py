# core/storage/json_asset_repo.py

from typing import Optional, List
from ..models import Asset
from ..repositories import AssetRepository
from .base import JSONRepository

class JSONAssetRepository(JSONRepository[Asset], AssetRepository):
    def __init__(self, file_path: str = "data/assets.json"):
        super().__init__(file_path, Asset)

    def get_by_unit(self, unit_id: str) -> List[Asset]:
        return [a for a in self.get_all() if a.unit_id == unit_id]

    def get_by_type(self, asset_type: str) -> List[Asset]:
        return [a for a in self.get_all() if a.asset_type == asset_type]

    def get_by_code(self, code: str, unit_id: str) -> Optional[Asset]:
        for a in self.get_all():
            if a.code == code and a.unit_id == unit_id:
                return a
        return None