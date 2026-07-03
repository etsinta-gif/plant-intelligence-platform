# rule_engine.py

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

class RuleEngine:
    """
    Loads engineering rules (thresholds, formulas, curves, constants) from JSON files.
    Supports filtering by asset_type and tags.
    """

    def __init__(self, data_dir: str = "Rules/", only_approved: bool = True):
        self.data_dir = Path(data_dir).resolve()
        self.only_approved = only_approved
        self._load_all()

    def _load_all(self):
        self.thresholds_data = self._load_file("thresholds.json")
        self.formulas_data = self._load_file("formulas.json")
        self.curves_data = self._load_file("curves.json")
        self.constants_data = self._load_file("constants.json")

        self.thresholds = self._get_rules(self.thresholds_data)
        self.formulas = self._get_rules(self.formulas_data)
        self.curves = self._get_rules(self.curves_data)
        self.constants = self._get_constants(self.constants_data)

    def _load_file(self, filename: str) -> Dict:
        path = self.data_dir / filename
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def _get_rules(self, data: Dict) -> Dict:
        if not data:
            return {}
        metadata = data.get("metadata", {})
        rules = data.get("rules", {})
        if self.only_approved and metadata.get("status") != "approved":
            return {}
        return rules

    def _get_constants(self, data: Dict) -> Dict:
        if not data:
            return {}
        if self.only_approved and data.get("metadata", {}).get("status") != "approved":
            return {}
        return data.get("constants", {})

    def save_file(self, filename: str, data: Dict):
        from datetime import datetime
        if "metadata" not in data:
            data["metadata"] = {}
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        data["metadata"]["updated_by"] = "UI_User"
        if "status" not in data["metadata"]:
            data["metadata"]["status"] = "draft"
        path = self.data_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self._load_all()

    # ---- Filtering ----
    def filter_by_asset_type(self, rules: Dict, asset_type: str) -> Dict:
        return {k: v for k, v in rules.items() if v.get("asset_type") == asset_type}

    def filter_by_tag(self, rules: Dict, tag: str) -> Dict:
        return {k: v for k, v in rules.items() if tag in v.get("tags", [])}

    # ---- Thresholds ----
    def classify(self, metric: str, value: float, asset_type: str = None) -> Dict[str, str]:
        all_rules = self.thresholds
        if asset_type:
            all_rules = self.filter_by_asset_type(all_rules, asset_type)
        rule = all_rules.get(metric)
        if not rule:
            return {"status": "Unknown", "message": f"No threshold defined for {metric}"}
        status = "Good"
        message = "OK"
        if rule.get("warn_low") is not None and value < rule["warn_low"]:
            status = "Critical"
            message = rule.get("critical_message", f"{metric} is {value:.2f} (critical low)").format(value=value)
        elif rule.get("warn_high") is not None and value > rule["warn_high"]:
            status = "Critical"
            message = rule.get("critical_message", f"{metric} is {value:.2f} (critical high)").format(value=value)
        elif rule.get("good_low") is not None and value < rule["good_low"]:
            status = "Warning"
            message = rule.get("warning_message", f"{metric} is {value:.2f} (warning low)").format(value=value)
        elif rule.get("good_high") is not None and value > rule["good_high"]:
            status = "Warning"
            message = rule.get("warning_message", f"{metric} is {value:.2f} (warning high)").format(value=value)
        return {"status": status, "message": message}

    # ---- Curves ----
    def evaluate_curve(self, curve_name: str, x_value: float, asset_type: str = None) -> float:
        """
        Evaluate a correction curve at a given X value.
        Coefficients are stored as [slope, intercept] (highest degree first).
        """
        all_curves = self.curves
        if asset_type:
            all_curves = self.filter_by_asset_type(all_curves, asset_type)
        curve = all_curves.get(curve_name)
        if not curve:
            raise ValueError(f"Curve {curve_name} not found for asset type {asset_type}.")
        coeffs = curve.get("coefficients", [1.0])
        # np.polyval expects coefficients from highest degree to lowest.
        # Our coefficients are stored as [slope, intercept] (degree 1), so they are already correct.
        result = np.polyval(coeffs, x_value)
        return float(result)

    # ---- Formulas ----
    def get_formula(self, formula_name: str, asset_type: str = None) -> Optional[Dict]:
        all_formulas = self.formulas
        if asset_type:
            all_formulas = self.filter_by_asset_type(all_formulas, asset_type)
        return all_formulas.get(formula_name)

    def get_formula_string(self, formula_name: str, asset_type: str = None) -> Optional[str]:
        formula = self.get_formula(formula_name, asset_type)
        return formula.get("formula") if formula else None

    # ---- Constants ----
    def get_constant(self, name: str) -> Any:
        return self.constants.get(name)

    def get_all_constants(self) -> Dict:
        return self.constants