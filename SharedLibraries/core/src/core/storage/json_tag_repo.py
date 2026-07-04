# core/storage/json_tag_repo.py

from typing import Optional, List
from ..models import Tag
from ..repositories import TagRepository
from .base import JSONRepository

class JSONTagRepository(JSONRepository[Tag], TagRepository):
    def __init__(self, file_path: str = "data/tags.json"):
        super().__init__(file_path, Tag)

    def get_by_instrument(self, instrument_id: str) -> List[Tag]:
        return [t for t in self.get_all() if t.instrument_id == instrument_id]

    def get_by_code(self, code: str) -> Optional[Tag]:
        for t in self.get_all():
            if t.code == code:
                return t
        return None

    def get_by_asset(self, asset_id: str) -> List[Tag]:
        # Simple implementation – can be optimized later
        return self.get_all()

    def get_calculated_tags(self) -> List[Tag]:
        return [t for t in self.get_all() if t.is_calculated]