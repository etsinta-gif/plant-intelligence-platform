# core/services/repository_factory.py

from typing import Optional
from ..repositories import (
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
from ..storage import (
    JSONCompanyRepository,
    JSONPlantRepository,
    JSONUnitRepository,
    JSONAssetRepository,
    JSONSubsystemRepository,
    JSONEquipmentRepository,
    JSONInstrumentRepository,
    JSONTagRepository,
    JSONMeasurementRepository,
    JSONCalculationRepository,
)

class RepositoryFactory:
    def __init__(self, config: dict):
        self.config = config
        self._backend = config.get("storage_backend", "json")
        self._data_dir = config.get("data_dir", "data/")

    def get_company_repository(self) -> CompanyRepository:
        if self._backend == "json":
            return JSONCompanyRepository(f"{self._data_dir}companies.json")
        raise NotImplementedError()

    def get_plant_repository(self) -> PlantRepository:
        if self._backend == "json":
            return JSONPlantRepository(f"{self._data_dir}plants.json")
        raise NotImplementedError()

    def get_unit_repository(self) -> UnitRepository:
        if self._backend == "json":
            return JSONUnitRepository(f"{self._data_dir}units.json")
        raise NotImplementedError()

    def get_asset_repository(self) -> AssetRepository:
        if self._backend == "json":
            return JSONAssetRepository(f"{self._data_dir}assets.json")
        raise NotImplementedError()

    def get_subsystem_repository(self) -> SubsystemRepository:
        if self._backend == "json":
            return JSONSubsystemRepository(f"{self._data_dir}subsystems.json")
        raise NotImplementedError()

    def get_equipment_repository(self) -> EquipmentRepository:
        if self._backend == "json":
            return JSONEquipmentRepository(f"{self._data_dir}equipment.json")
        raise NotImplementedError()

    def get_instrument_repository(self) -> InstrumentRepository:
        if self._backend == "json":
            return JSONInstrumentRepository(f"{self._data_dir}instruments.json")
        raise NotImplementedError()

    def get_tag_repository(self) -> TagRepository:
        if self._backend == "json":
            return JSONTagRepository(f"{self._data_dir}tags.json")
        raise NotImplementedError()

    def get_measurement_repository(self) -> MeasurementRepository:
        if self._backend == "json":
            return JSONMeasurementRepository(f"{self._data_dir}measurements.json")
        raise NotImplementedError()

    def get_calculation_repository(self) -> CalculationRepository:
        if self._backend == "json":
            return JSONCalculationRepository(f"{self._data_dir}calculations.json")
        raise NotImplementedError()