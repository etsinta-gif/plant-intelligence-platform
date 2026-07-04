# core/__init__.py

from .models import (
    Entity,
    Company,
    Plant,
    Unit,
    Asset,
    Subsystem,
    Equipment,
    Instrument,
    Tag,
    Measurement,
    Calculation,
)
from .repositories import (
    Repository,
    CompanyRepository,
    PlantRepository,
    UnitRepository,
    AssetRepository,
    SubsystemRepository,
    EquipmentRepository,
    InstrumentRepository,
    TagRepository,
    MeasurementRepository,
    CalculationRepository,
)
from .services import RepositoryFactory, AuditService, ConfigService
from .engine import CalculationEngine

_CORE_INITIALIZED = False
_REPOSITORY_FACTORY = None

def init_core(config: dict):
    global _CORE_INITIALIZED, _REPOSITORY_FACTORY
    if _CORE_INITIALIZED:
        return
    _REPOSITORY_FACTORY = RepositoryFactory(config)
    _CORE_INITIALIZED = True

def get_repository_factory():
    if not _CORE_INITIALIZED:
        raise RuntimeError("Core not initialized. Call init_core() first.")
    return _REPOSITORY_FACTORY

__all__ = [
    "Entity", "Company", "Plant", "Unit", "Asset", "Subsystem", "Equipment",
    "Instrument", "Tag", "Measurement", "Calculation",
    "Repository", "CompanyRepository", "PlantRepository", "UnitRepository",
    "AssetRepository", "SubsystemRepository", "EquipmentRepository",
    "InstrumentRepository", "TagRepository", "MeasurementRepository",
    "CalculationRepository",
    "RepositoryFactory", "AuditService", "ConfigService",
    "CalculationEngine",
    "init_core", "get_repository_factory",
]