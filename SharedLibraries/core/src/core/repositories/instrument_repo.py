# core/repositories/instrument_repo.py

from abc import abstractmethod
from typing import List, Optional
from ..models import Instrument
from .base import Repository

class InstrumentRepository(Repository[Instrument]):
    @abstractmethod
    def get_by_equipment(self, equipment_id: str) -> List[Instrument]:
        pass

    @abstractmethod
    def get_by_type(self, instrument_type: str) -> List[Instrument]:
        pass

    @abstractmethod
    def get_by_code(self, code: str, equipment_id: str) -> Optional[Instrument]:
        pass