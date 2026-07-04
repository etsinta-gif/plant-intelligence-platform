# core/storage/json_instrument_repo.py

from typing import Optional, List
from ..models import Instrument
from ..repositories import InstrumentRepository
from .base import JSONRepository

class JSONInstrumentRepository(JSONRepository[Instrument], InstrumentRepository):
    def __init__(self, file_path: str = "data/instruments.json"):
        super().__init__(file_path, Instrument)

    def get_by_equipment(self, equipment_id: str) -> List[Instrument]:
        return [i for i in self.get_all() if i.equipment_id == equipment_id]

    def get_by_type(self, instrument_type: str) -> List[Instrument]:
        return [i for i in self.get_all() if i.instrument_type == instrument_type]

    def get_by_code(self, code: str, equipment_id: str) -> Optional[Instrument]:
        for i in self.get_all():
            if i.code == code and i.equipment_id == equipment_id:
                return i
        return None