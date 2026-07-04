# core/services/config_service.py

from typing import Any, Dict, Optional
import json
from pathlib import Path

class ConfigService:
    _instance: Optional["ConfigService"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None, file_path: Optional[str] = None):
        self._config: Dict[str, Any] = config or {}
        self._file_path = file_path
        if file_path and not config:
            self.load_from_file(file_path)

    @classmethod
    def get_instance(cls) -> "ConfigService":
        if cls._instance is None:
            raise RuntimeError("ConfigService not initialized.")
        return cls._instance

    @classmethod
    def set_instance(cls, service: "ConfigService"):
        cls._instance = service

    def load_from_file(self, file_path: str):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(path, "r") as f:
            self._config = json.load(f)
        self._file_path = file_path

    def save(self, file_path: Optional[str] = None):
        path = file_path or self._file_path
        if not path:
            raise ValueError("No file path specified.")
        with open(path, "w") as f:
            json.dump(self._config, f, indent=2, default=str)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        keys = key.split(".")
        target = self._config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        return self._config.copy()

    def merge(self, updates: Dict[str, Any]):
        def _merge(base: dict, update: dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    _merge(base[key], value)
                else:
                    base[key] = value
        _merge(self._config, updates)