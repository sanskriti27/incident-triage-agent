import sqlite3
from typing import Any
from agent.handlers.base import BaseHandler

class DatabaseHandler(BaseHandler):
    def __init__(self, service_config) -> None:
        self._query = service_config.get("query");
        self._db_path = service_config.get("db_path")
        self._description = service_config.get("description")

    def fetch_context(self, identifier: str) -> dict[str, Any]:
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(self._query, (identifier,))
                row = cursor.fetchone()
                if not row:
                    return {
                        "found": False,
                        "identifier": identifier,
                        "error": f"identifier {identifier} not found in the table"
                    }
            
                columns = [desc[0] for desc in cursor.description]
                return {
                    "found": True,
                    "result": dict(zip(columns, row))
                }
        except sqlite3.Error as e:
            return {
                "found": False,
                "error": str(e),
                "identifier": identifier
            }


    def describe_context(self) -> str:

        return self._description