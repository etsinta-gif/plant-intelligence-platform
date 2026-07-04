# core/repositories/company_repo.py

from abc import abstractmethod
from typing import Optional
from ..models import Company
from .base import Repository

class CompanyRepository(Repository[Company]):
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Company]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Company]:
        pass