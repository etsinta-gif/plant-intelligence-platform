# core/repositories/tag_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Tag
from .base import Repository

class TagRepository(Repository[Tag]):
    @abstractmethod
    def get_by_instrument(self, instrument_id: str) -> List[Tag]:
        pass

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Tag]:
        pass

    @abstractmethod
    def get_by_asset(self, asset_id: str) -> List[Tag]:
        pass

    @abstractmethod
    def get_calculated_tags(self) -> List[Tag]:
        pass