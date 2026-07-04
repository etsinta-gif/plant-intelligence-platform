"""
EngineerOS — Engineering Operating System.

Provides higher‑level services for building plant intelligence platforms.
"""

__version__ = "0.1.0"

from .services.asset_registry import AssetRegistry
from .services.calculation_template_service import CalculationTemplateService

__all__ = ["AssetRegistry", "CalculationTemplateService"]