# core/storage/json_company_repo.py

from typing import Optional
from ..models import Company
from ..repositories import CompanyRepository
from .base import JSONRepository

class JSONCompanyRepository(JSONRepository[Company], CompanyRepository):
    def __init__(self, file_path: str = "data/companies.json"):
        super().__init__(file_path, Company)

    def get_by_code(self, code: str) -> Optional[Company]:
        for c in self.get_all():
            if c.code == code:
                return c
        return None

    def get_by_name(self, name: str) -> Optional[Company]:
        for c in self.get_all():
            if c.name == name:
                return c
        return None