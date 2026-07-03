# Inside registry.py — this is the orchestrator
from agent.handlers.api import ApiHandler
from agent.handlers.base import BaseHandler
from agent.handlers.database import DatabaseHandler
from agent.handlers.default import DefaultHandler
import yaml

class ServiceRegistry:
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)
        self._services = raw["services"]  # the section you actually use

    def get_handler(self, service_name: str) -> BaseHandler:
        service_name = service_name.lower().strip()
        config_service = self._services.get(service_name)  # not self._config['services']

        if config_service is None:
            return DefaultHandler(service_name)

        handler = config_service.get("handler_type")

        if handler == 'api':
            return ApiHandler(config_service)
        elif handler == 'database':
            return DatabaseHandler(config_service)
        else:
            return DefaultHandler(service_name)

    def get_service_config(self, service_name: str) -> dict:
        return self._services.get(service_name, {})

    def get_all_services(self) -> dict:
        return self._services
        