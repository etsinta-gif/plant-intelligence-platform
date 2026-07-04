# core/storage/base.py

import json
from pathlib import Path
from typing import List, Optional, Type, TypeVar, Generic
from ..models import Entity
from ..repositories.base import Repository

T = TypeVar("T", bound=Entity)

class JSONRepository(Repository[T], Generic[T]):
    def __init__(self, file_path: str, entity_class: Type[T]):
        self.file_path = Path(file_path)
        self.entity_class = entity_class
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_data([])

    def _read_data(self) -> List[dict]:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_data(self, data: List[dict]):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _to_dict(self, entity: T) -> dict:
        return entity.to_dict()

    def _from_dict(self, data: dict) -> T:
        return self.entity_class.from_dict(data)

    def get(self, entity_id: str) -> Optional[T]:
        for item in self._read_data():
            if item.get("id") == entity_id:
                return self._from_dict(item)
        return None

    def get_all(self) -> List[T]:
        return [self._from_dict(item) for item in self._read_data()]

    def create(self, entity: T) -> T:
        data = self._read_data()
        if any(item.get("id") == entity.id for item in data):
            raise ValueError(f"Entity with id {entity.id} already exists.")
        data.append(self._to_dict(entity))
        self._write_data(data)
        return entity

    def update(self, entity: T) -> T:
        data = self._read_data()
        for i, item in enumerate(data):
            if item.get("id") == entity.id:
                data[i] = self._to_dict(entity)
                self._write_data(data)
                return entity
        raise ValueError(f"Entity with id {entity.id} not found.")

    def delete(self, entity_id: str) -> bool:
        data = self._read_data()
        initial_len = len(data)
        data = [item for item in data if item.get("id") != entity_id]
        if len(data) < initial_len:
            self._write_data(data)
            return True
        return False