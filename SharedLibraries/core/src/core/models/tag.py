# core/models/tag.py

from dataclasses import dataclass
from typing import Optional
from .base import Entity

@dataclass
class Tag(Entity):
    code: str = ""
    instrument_id: str = ""
    data_type: str = "float"
    unit: str = ""
    description: str = ""
    is_calculated: bool = False
    formula: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if not self.code and self.name:
            self.code = self.name

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "code": self.code,
            "instrument_id": self.instrument_id,
            "data_type": self.data_type,
            "unit": self.unit,
            "description": self.description,
            "is_calculated": self.is_calculated,
            "formula": self.formula,
        })
        return data