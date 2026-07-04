# engineeros/services/calculation_template_service.py

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from core import Calculation, CalculationEngine
from .asset_registry import AssetRegistry


class CalculationTemplateService:
    """
    Manages calculation templates and instantiates them for specific assets.
    Templates are stored as JSON files.
    """

    def __init__(self, registry: AssetRegistry, template_dir: str = None):
        self.registry = registry
        self.engine = CalculationEngine()
        self.template_dir = Path(template_dir) if template_dir else Path("data/calculation_templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)

    # ---- Template Management ----

    def get_templates(self, asset_type: str) -> List[Dict[str, Any]]:
        """Load all templates for a given asset type."""
        templates = []
        for f in self.template_dir.glob(f"{asset_type}_*.json"):
            try:
                with open(f, "r") as fh:
                    templates.append(json.load(fh))
            except Exception:
                continue
        return templates

    def save_template(self, asset_type: str, template_data: Dict[str, Any]) -> None:
        """Save a template to a JSON file."""
        name = template_data.get("name", "unnamed")
        filename = f"{asset_type}_{name.replace(' ', '_')}.json"
        filepath = self.template_dir / filename
        with open(filepath, "w") as f:
            json.dump(template_data, f, indent=2)

    def delete_template(self, asset_type: str, template_code: str) -> bool:
        """Delete a template by its code."""
        for f in self.template_dir.glob(f"{asset_type}_*.json"):
            with open(f, "r") as fh:
                data = json.load(fh)
                if data.get("code") == template_code:
                    f.unlink()
                    return True
        return False

    # ---- Instantiation ----

    def instantiate_for_asset(self, asset_id: str) -> int:
        """
        Apply templates to an asset. Creates Calculation instances in the Core repository.
        Returns the number of new calculations created.
        """
        asset = self.registry.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found.")

        templates = self.get_templates(asset.asset_type)
        if not templates:
            return 0

        calc_repo = self.registry._factory.get_calculation_repository()
        count = 0

        for tmpl in templates:
            # Check if a calculation with this code already exists
            existing = calc_repo.get_by_code(tmpl["code"])
            if existing:
                continue

            # Create the Calculation object
            calc = Calculation(
                code=tmpl["code"],
                name=tmpl["name"],
                asset_type=asset.asset_type,
                description=tmpl.get("description", ""),
                formula=tmpl["formula"],
                unit=tmpl.get("unit", ""),
                inputs=tmpl.get("inputs", []),
                outputs=tmpl.get("outputs", []),
                category=tmpl.get("category", "Performance"),
                is_active=True,
            )
            calc_repo.create(calc)
            count += 1

        return count

    def get_calculations_for_asset_type(self, asset_type: str) -> List[Calculation]:
        """Get all instantiated calculations for a given asset type."""
        calc_repo = self.registry._factory.get_calculation_repository()
        return calc_repo.get_by_asset_type(asset_type)

    def evaluate(self, calc_code: str, context: Dict[str, float]) -> float:
        """Evaluate a calculation by its code with the given context."""
        calc_repo = self.registry._factory.get_calculation_repository()
        calc = calc_repo.get_by_code(calc_code)
        if not calc:
            raise ValueError(f"Calculation {calc_code} not found.")
        return self.engine.evaluate(calc.formula, context)

    # ---- Default Templates ----

    def create_default_gasturbine_templates(self):
        """Create a set of default templates for GasTurbine assets."""
        templates = [
            {
                "code": "HR_GROSS",
                "name": "Gross Heat Rate",
                "category": "Performance",
                "unit": "kJ/kWh",
                "description": "Gross heat rate based on fuel flow and output",
                "formula": "(FQG * 3.6 * LHV) / DWATT",
                "inputs": ["FQG", "LHV", "DWATT"],
                "outputs": ["GROSS_HR"],
            },
            {
                "code": "EFFICIENCY_GROSS",
                "name": "Gross Thermal Efficiency",
                "category": "Efficiency",
                "unit": "%",
                "description": "Gross thermal efficiency on LHV basis",
                "formula": "3600 / HR_GROSS * 100",
                "inputs": ["HR_GROSS"],
                "outputs": ["EFFICIENCY"],
            },
            {
                "code": "PRESSURE_RATIO",
                "name": "Compressor Pressure Ratio",
                "category": "Performance",
                "unit": "",
                "description": "Compressor pressure ratio",
                "formula": "CPD / (AFPIP * 0.133322)",
                "inputs": ["CPD", "AFPIP"],
                "outputs": ["PR"],
            },
            {
                "code": "CORRECTED_HR",
                "name": "Corrected Heat Rate",
                "category": "Correction",
                "unit": "kJ/kWh",
                "description": "Heat rate corrected to ISO conditions using C1..C9",
                "formula": "GROSS_HR * CORR_FACTOR",
                "inputs": ["GROSS_HR", "CORR_FACTOR"],
                "outputs": ["CORRECTED_HR"],
            },
            {
                "code": "C1_INLET_TEMP",
                "name": "C1: Inlet Temperature Correction",
                "category": "Correction",
                "unit": "",
                "description": "Temperature correction factor (GE 9FA)",
                "formula": "1 + 0.0002434 * (CTIM - 15)",
                "inputs": ["CTIM"],
                "outputs": ["C1"],
            },
            {
                "code": "C2_HUMIDITY",
                "name": "C2: Humidity Correction",
                "category": "Correction",
                "unit": "",
                "description": "Relative humidity correction factor",
                "formula": "1 - 0.0000735 * (RH - 60)",
                "inputs": ["RH"],
                "outputs": ["C2"],
            },
            {
                "code": "C6_INLET_LOSS",
                "name": "C6: Inlet Loss Correction",
                "category": "Correction",
                "unit": "",
                "description": "Inlet filter pressure loss correction",
                "formula": "1 - 0.00000576 * AFPCS",
                "inputs": ["AFPCS"],
                "outputs": ["C6"],
            },
            {
                "code": "CORR_FACTOR",
                "name": "Total Correction Factor",
                "category": "Correction",
                "unit": "",
                "description": "Product of C1..C9",
                "formula": "C1 * C2 * C3 * C4 * C5 * C6 * C7 * C8 * C9",
                "inputs": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"],
                "outputs": ["CORR_FACTOR"],
            },
        ]

        for tmpl in templates:
            self.save_template("GasTurbine", tmpl)

    def create_default_hrsg_templates(self):
        """Create a set of default templates for HRSG assets."""
        templates = [
            {
                "code": "HR_PINCH",
                "name": "Pinch Point Temperature Difference",
                "category": "Performance",
                "unit": "°C",
                "description": "Pinch point temperature difference",
                "formula": "EXH_TEMP - DRUM_TEMP",
                "inputs": ["EXH_TEMP", "DRUM_TEMP"],
                "outputs": ["PINCH"],
            },
            {
                "code": "HR_APPROACH",
                "name": "Approach Temperature Difference",
                "category": "Performance",
                "unit": "°C",
                "description": "Approach temperature difference",
                "formula": "FEEDWATER_TEMP - EXH_TEMP",
                "inputs": ["FEEDWATER_TEMP", "EXH_TEMP"],
                "outputs": ["APPROACH"],
            },
            {
                "code": "HR_EFFICIENCY",
                "name": "HRSG Efficiency",
                "category": "Efficiency",
                "unit": "%",
                "description": "HRSG thermal efficiency",
                "formula": "((FW_OUT - FW_IN) * 4.1868) / (EXH_FLOW * CP_EXH)",
                "inputs": ["FW_OUT", "FW_IN", "EXH_FLOW", "CP_EXH"],
                "outputs": ["HR_EFF"],
            },
        ]

        for tmpl in templates:
            self.save_template("HRSG", tmpl)

    def create_default_steam_turbine_templates(self):
        """Create a set of default templates for SteamTurbine assets."""
        templates = [
            {
                "code": "ST_HR_GROSS",
                "name": "Steam Turbine Gross Heat Rate",
                "category": "Performance",
                "unit": "kJ/kWh",
                "description": "Gross heat rate of steam turbine",
                "formula": "STEAM_FLOW * (H_IN - H_OUT) / ST_POWER",
                "inputs": ["STEAM_FLOW", "H_IN", "H_OUT", "ST_POWER"],
                "outputs": ["ST_HR"],
            },
            {
                "code": "ST_EFFICIENCY",
                "name": "Steam Turbine Efficiency",
                "category": "Efficiency",
                "unit": "%",
                "description": "Steam turbine isentropic efficiency",
                "formula": "(H_IN - H_OUT) / (H_IN - H_ISENTROPIC) * 100",
                "inputs": ["H_IN", "H_OUT", "H_ISENTROPIC"],
                "outputs": ["ST_EFF"],
            },
        ]

        for tmpl in templates:
            self.save_template("SteamTurbine", tmpl)