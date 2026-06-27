import re
from dataclasses import dataclass

UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
REQ_ID_PATTERN_DEFAULT = rf"\[({UUID_PATTERN})\]"
DEFAULT_IDENTIFIER_PATTERN = UUID_PATTERN
SERVICE_NAME_PATTERN = r"(\w+)(?=\.java)"

@dataclass
class ParsedLog:
    service_name: str | None
    error_type: str | None
    request_id: str | None
    identifier: str | None
    raw_log: str
    warnings: list[str]

class LogParser:
    def __init__(self, services):
        self._services = services

    def parse(self, raw_log: str) -> ParsedLog:
        warnings = []

        # 1. Extract service name
        service_match = re.search(SERVICE_NAME_PATTERN, raw_log)
        if not service_match:
            warnings.append("No service name found in stack trace")
            return ParsedLog(None, None, None, None, raw_log, warnings)

        service_name = service_match.group(1).lower().strip()

        # 2. Get service config for patterns
        service_config = self._services.get(service_name, {})
        if not service_config:
            warnings.append(f"No config found for '{service_name}'. Add to services.yaml.")

        req_id_pattern = service_config.get('request_id_pattern', REQ_ID_PATTERN_DEFAULT)
        identifier_pattern = service_config.get('identifier_pattern', DEFAULT_IDENTIFIER_PATTERN)

        # 3. Extract request ID
        req_match = re.search(req_id_pattern, raw_log)
        request_id = req_match.group(1) if req_match else None
        if not request_id:
            warnings.append("No request ID found in log")

        # 4. Extract identifier
        id_match = re.search(identifier_pattern, raw_log)
        identifier = id_match.group(1) if id_match else None
        if not identifier:
            warnings.append("No identifier found. Context fetch will be skipped.")

        # 5. Extract error type
        exc_match = re.search(r'(\w+Exception)', raw_log)
        error_type = exc_match.group(1) if exc_match else None
        if not error_type:
            warnings.append("No exception type found in log")

        return ParsedLog(
            service_name=service_name,
            error_type=error_type,
            request_id=request_id,
            identifier=identifier,
            raw_log=raw_log,
            warnings=warnings
        )