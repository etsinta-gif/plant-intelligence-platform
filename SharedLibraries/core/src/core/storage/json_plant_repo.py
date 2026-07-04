# core/storage/json_plant_repo.py

from typing import Optional, List
from ..models import Plant
from ..repositories import PlantRepository
from .base import JSONRepository

class JSONPlantRepository(JSONRepository[Plant], PlantRepository):
    def __init__(self, file_path: str = "data/plants.json"):
        super().__init__(file_path, Plant)

    def get_by_company(self, company_id: str) -> List[Plant]:
        return [p for p in self.get_all() if p.company_id == company_id]

    def get_by_code(self, code: str, company_id: str) -> Optional[Plant]:
        for p in self.get_all():
            if p.code == code and p.company_id == company_id:
                return p
        return None