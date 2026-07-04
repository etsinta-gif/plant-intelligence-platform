# core/storage/json_measurement_repo.py

from datetime import datetime
from typing import Optional, List
from ..models import Measurement
from ..repositories import MeasurementRepository
from .base import JSONRepository

class JSONMeasurementRepository(JSONRepository[Measurement], MeasurementRepository):
    def __init__(self, file_path: str = "data/measurements.json"):
        super().__init__(file_path, Measurement)

    def get_by_tag(self, tag_id: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Measurement]:
        result = [m for m in self.get_all() if m.tag_id == tag_id]
        if start:
            result = [m for m in result if m.timestamp >= start]
        if end:
            result = [m for m in result if m.timestamp <= end]
        return result

    def get_latest(self, tag_id: str) -> Optional[Measurement]:
        measurements = self.get_by_tag(tag_id)
        if not measurements:
            return None
        return max(measurements, key=lambda m: m.timestamp)

    def create_batch(self, measurements: List[Measurement]) -> List[Measurement]:
        created = []
        for m in measurements:
            created.append(self.create(m))
        return created

    def delete_by_tag(self, tag_id: str) -> int:
        all_data = self._read_data()
        initial_len = len(all_data)
        filtered = [m for m in all_data if m.get("tag_id") != tag_id]
        if len(filtered) < initial_len:
            self._write_data(filtered)
            return initial_len - len(filtered)
        return 0