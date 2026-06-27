from agent.handlers.base import BaseHandler
import requests
from urllib.parse import quote
class ApiHandler(BaseHandler):
    def __init__(self, service_config) -> None:
        self._api_url = service_config.get("api_url")
        self._description = service_config.get("description")

    def fetch_context(self, identifier: str) -> dict[str, Any]:
        safe_id = quote(identifier, safe='')  # URL-encode any special characters
        url = self._api_url.replace("{id}", safe_id)
        try:
            response = requests.get(url, timeout=5)
        except requests.exceptions.RequestException as e:
            return {"found": False, "error": str(e), "identifier": identifier}

        if response.status_code == 404:
            return {"found": False, "identifier": identifier}

        if response.status_code != 200:
            return {"found": False, "error": f"API returned {response.status_code}", "identifier": identifier}

        return {"found": True, "result": response.json()}

    def describe_context(self) -> str:
        return self._description