# core/repositories/measurement_repo.py

from abc import abstractmethod
from datetime import datetime
from typing import List, Optional
from ..models import Measurement
from .base import Repository

class MeasurementRepository(Repository[Measurement]):
    @abstractmethod
    def get_by_tag(self, tag_id: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Measurement]:
        pass

    @abstractmethod
    def get_latest(self, tag_id: str) -> Optional[Measurement]:
        pass

    @abstractmethod
    def create_batch(self, measurements: List[Measurement]) -> List[Measurement]:
        pass

    @abstractmethod
    def delete_by_tag(self, tag_id: str) -> int:
        pass