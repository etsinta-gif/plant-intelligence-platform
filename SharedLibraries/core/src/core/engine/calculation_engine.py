# core/engine/calculation_engine.py

import math
import re
from typing import Dict, Any, List, Optional
from ..models import Calculation
from ..repositories import CalculationRepository, TagRepository

class CalculationEngine:
    SAFE_BUILTINS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "pi": math.pi,
        "e": math.e,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "sqrt": math.sqrt,
    }

    def __init__(self, tag_repo: Optional[TagRepository] = None, calc_repo: Optional[CalculationRepository] = None):
        self.tag_repo = tag_repo
        self.calc_repo = calc_repo
        self._registry: Dict[str, Calculation] = {}

    def register(self, calculation: Calculation):
        self._registry[calculation.code] = calculation

    def get(self, code: str) -> Optional[Calculation]:
        return self._registry.get(code)

    def get_by_asset_type(self, asset_type: str) -> List[Calculation]:
        return [c for c in self._registry.values() if c.asset_type == asset_type]

    def get_active(self) -> List[Calculation]:
        return [c for c in self._registry.values() if c.is_active]

    def evaluate(self, formula: str, context: Dict[str, float]) -> float:
        self._validate_formula(formula)
        env = self.SAFE_BUILTINS.copy()
        env.update(context)
        env["__builtins__"] = None
        try:
            result = eval(formula, env, {})
            return float(result)
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {e}")

    def evaluate_calculation(self, calc: Calculation, context: Dict[str, float]) -> float:
        if calc.code not in self._registry:
            raise ValueError(f"Calculation '{calc.code}' not registered.")
        return self.evaluate(calc.formula, context)

    def _validate_formula(self, formula: str):
        if formula.count("(") != formula.count(")"):
            raise ValueError("Unbalanced parentheses in formula.")
        allowed = r"^[a-zA-Z0-9_+\-*/%()., \t\n]+$"
        if not re.match(allowed, formula):
            raise ValueError("Formula contains disallowed characters.")