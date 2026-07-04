# core/models/calculation.py

from dataclasses import dataclass, field
from typing import List
from .base import Entity

@dataclass
class Calculation(Entity):
    code: str = ""
    name: str = ""
    asset_type: str = ""
    description: str = ""
    formula: str = ""
    unit: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    category: str = "Performance"
    is_active: bool = True
    version: str = "1.0"

    def __post_init__(self):
        super().__post_init__()
        if not self.code and self.name:
            self.code = self.name[:8].upper()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "code": self.code,
            "name": self.name,
            "asset_type": self.asset_type,
            "description": self.description,
            "formula": self.formula,
            "unit": self.unit,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "category": self.category,
            "is_active": self.is_active,
            "version": self.version,
        })
        return data