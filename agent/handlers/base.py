from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class TriageContext:
    service_name: str
    error_type: str
    identifier: str
    raw_log: str
    fetched_data: dict[str, Any]
    warnings: list[str]  # ← where "unknown service" warnings go

class BaseHandler(ABC):
    @abstractmethod
    def fetch_context(self, identifier: str) -> dict[str, Any]:
        """Go get whatever data this service needs."""

    @abstractmethod
    def describe_context(self) -> str:
        """Tell the LLM what kind of system this is."""