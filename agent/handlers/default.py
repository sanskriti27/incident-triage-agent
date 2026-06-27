from typing import Any
from agent.handlers.base import BaseHandler

class DefaultHandler(BaseHandler):

    def __init__(self, service_name: str):
        self.service_name = service_name

    def extract_identifier(self, log_line: str) -> str | None:
        self.context.raw_log = log_line
        return None
        
    def fetch_context(self, identifier: str) -> dict[str, Any]:
        return None

    def describe_context(self) -> str:
        return "Unknown service. Only raw log available."

    def get_warnings(self) -> list[str]:
        return [
            f"No config found for '{self.service_name}'. "
            f"Add an entry in services.yaml for richer triage."
        ]