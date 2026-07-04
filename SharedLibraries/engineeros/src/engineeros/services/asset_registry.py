# engineeros/services/asset_registry.py

from typing import List, Optional, Dict, Any
import json
from pathlib import Path

from core import (
    init_core,
    get_repository_factory,
    Company,
    Plant,
    Unit,
    Asset,
    Subsystem,
    Equipment,
    Instrument,
    Tag,
)


class AssetRegistry:
    """
    Asset Registry Service — manages the enterprise hierarchy.
    Provides high-level operations on top of the Core repositories.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config:
            init_core(config)
        self._factory = get_repository_factory()
        self._company_repo = self._factory.get_company_repository()
        self._plant_repo = self._factory.get_plant_repository()
        self._unit_repo = self._factory.get_unit_repository()
        self._asset_repo = self._factory.get_asset_repository()
        self._subsystem_repo = self._factory.get_subsystem_repository()
        self._equipment_repo = self._factory.get_equipment_repository()
        self._instrument_repo = self._factory.get_instrument_repository()
        self._tag_repo = self._factory.get_tag_repository()

    # ---- Company ----
    def create_company(self, name: str, code: str = "", description: str = "") -> Company:
        company = Company(name=name, code=code or name[:4].upper(), description=description)
        return self._company_repo.create(company)

    def get_company(self, company_id: str) -> Optional[Company]:
        return self._company_repo.get(company_id)

    def get_company_by_code(self, code: str) -> Optional[Company]:
        return self._company_repo.get_by_code(code)

    def list_companies(self) -> List[Company]:
        return self._company_repo.get_all()

    # ---- Plant ----
    def create_plant(self, name: str, company_id: str, code: str = "", location: str = "") -> Plant:
        plant = Plant(name=name, code=code or name[:6].upper(), company_id=company_id, location=location)
        return self._plant_repo.create(plant)

    def get_plants_by_company(self, company_id: str) -> List[Plant]:
        return self._plant_repo.get_by_company(company_id)

    # ---- Unit ----
    def create_unit(self, name: str, plant_id: str, code: str = "", fuel_type: str = "") -> Unit:
        unit = Unit(name=name, code=code or name[:6].upper(), plant_id=plant_id, fuel_type=fuel_type)
        return self._unit_repo.create(unit)

    def get_units_by_plant(self, plant_id: str) -> List[Unit]:
        return self._unit_repo.get_by_plant(plant_id)

    # ---- Asset ----
    def create_asset(self, name: str, unit_id: str, asset_type: str, code: str = "",
                     manufacturer: str = "", model: str = "", serial_number: str = "") -> Asset:
        asset = Asset(
            name=name,
            code=code or name[:6].upper(),
            unit_id=unit_id,
            asset_type=asset_type,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
        )
        return self._asset_repo.create(asset)

    def get_assets_by_unit(self, unit_id: str) -> List[Asset]:
        return self._asset_repo.get_by_unit(unit_id)

    def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        return self._asset_repo.get_by_type(asset_type)

    def list_assets(self) -> List[Asset]:
        return self._asset_repo.get_all()

    # ---- Subsystem ----
    def create_subsystem(self, name: str, asset_id: str, code: str = "") -> Subsystem:
        subsystem = Subsystem(name=name, code=code or name[:6].upper(), asset_id=asset_id)
        return self._subsystem_repo.create(subsystem)

    def get_subsystems_by_asset(self, asset_id: str) -> List[Subsystem]:
        return self._subsystem_repo.get_by_asset(asset_id)

    # ---- Equipment ----
    def create_equipment(self, name: str, subsystem_id: str, code: str = "") -> Equipment:
        equipment = Equipment(name=name, code=code or name[:6].upper(), subsystem_id=subsystem_id)
        return self._equipment_repo.create(equipment)

    def get_equipment_by_subsystem(self, subsystem_id: str) -> List[Equipment]:
        return self._equipment_repo.get_by_subsystem(subsystem_id)

    # ---- Instrument ----
    def create_instrument(self, name: str, equipment_id: str, instrument_type: str = "",
                          unit: str = "", code: str = "") -> Instrument:
        instrument = Instrument(
            name=name,
            code=code or name[:6].upper(),
            equipment_id=equipment_id,
            instrument_type=instrument_type,
            unit=unit,
        )
        return self._instrument_repo.create(instrument)

    def get_instruments_by_equipment(self, equipment_id: str) -> List[Instrument]:
        return self._instrument_repo.get_by_equipment(equipment_id)

    # ---- Tag ----
    def create_tag(self, name: str, code: str, instrument_id: str,
                   data_type: str = "float", unit: str = "",
                   description: str = "", is_calculated: bool = False,
                   formula: Optional[str] = None) -> Tag:
        tag = Tag(
            name=name,
            code=code,
            instrument_id=instrument_id,
            data_type=data_type,
            unit=unit,
            description=description,
            is_calculated=is_calculated,
            formula=formula,
        )
        return self._tag_repo.create(tag)

    def get_tags_by_instrument(self, instrument_id: str) -> List[Tag]:
        return self._tag_repo.get_by_instrument(instrument_id)

    def get_tags_by_asset(self, asset_id: str) -> List[Tag]:
        subsystems = self._subsystem_repo.get_by_asset(asset_id)
        tags = []
        for subsystem in subsystems:
            equipment_list = self._equipment_repo.get_by_subsystem(subsystem.id)
            for equipment in equipment_list:
                instruments = self._instrument_repo.get_by_equipment(equipment.id)
                for instrument in instruments:
                    tags.extend(self._tag_repo.get_by_instrument(instrument.id))
        return tags

    def get_tag_by_code(self, code: str) -> Optional[Tag]:
        return self._tag_repo.get_by_code(code)

    def load_from_config(self, config_path: str) -> None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(path, "r") as f:
            data = json.load(f)

        company_data = data.get("company", {})
        company = self.create_company(
            name=company_data.get("name", "Default Company"),
            code=company_data.get("code", "DEF"),
        )
        for plant_data in data.get("plants", []):
            plant = self.create_plant(
                name=plant_data["name"],
                code=plant_data.get("code", ""),
                company_id=company.id,
                location=plant_data.get("location", ""),
            )
            for unit_data in plant_data.get("units", []):
                unit = self.create_unit(
                    name=unit_data["name"],
                    code=unit_data.get("code", ""),
                    plant_id=plant.id,
                    fuel_type=unit_data.get("fuel_type", ""),
                )
                for asset_data in unit_data.get("assets", []):
                    self.create_asset(
                        name=asset_data["name"],
                        code=asset_data.get("code", ""),
                        unit_id=unit.id,
                        asset_type=asset_data.get("asset_type", "Unknown"),
                        manufacturer=asset_data.get("manufacturer", ""),
                        model=asset_data.get("model", ""),
                        serial_number=asset_data.get("serial_number", ""),
                    )