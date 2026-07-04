# core/services/audit_service.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

@dataclass
class AuditEntry:
    operation: str
    entity_type: str
    entity_id: str
    user: str = "system"
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user": self.user,
            "before": self.before,
            "after": self.after,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }

class AuditService:
    def __init__(self, max_entries: int = 1000):
        self._logs: List[AuditEntry] = []
        self._max_entries = max_entries

    def log(self, operation: str, entity_type: str, entity_id: str,
            before: Optional[Dict] = None, after: Optional[Dict] = None,
            user: str = "system", details: Optional[Dict] = None):
        entry = AuditEntry(
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            before=before,
            after=after,
            details=details,
        )
        self._logs.append(entry)
        if len(self._logs) > self._max_entries:
            self._logs = self._logs[-self._max_entries:]

    def get_all(self) -> List[AuditEntry]:
        return self._logs.copy()

    def get_by_entity(self, entity_id: str) -> List[AuditEntry]:
        return [e for e in self._logs if e.entity_id == entity_id]

    def get_by_entity_type(self, entity_type: str) -> List[AuditEntry]:
        return [e for e in self._logs if e.entity_type == entity_type]

    def get_by_user(self, user: str) -> List[AuditEntry]:
        return [e for e in self._logs if e.user == user]

    def get_recent(self, limit: int = 50) -> List[AuditEntry]:
        return self._logs[-limit:]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps([e.to_dict() for e in self._logs], indent=indent, default=str)

    def clear(self):
        self._logs.clear()