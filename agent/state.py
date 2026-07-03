from typing import Annotated, TypedDict
from operator import add

def take_max(a: int, b: int) -> int:
    return max(a, b)

def merge_error(a: str | None, b: str | None) -> str | None:
    return a or b

class AgentState(TypedDict):
    raw_log: str
    service_name: str | None
    error_type: str | None
    request_id: str | None
    identifier: str | None
    source_code: str | None
    fetched_data: dict
    warnings: Annotated[list[str], add]          # concatenate
    error: Annotated[str | None, merge_error]    # surface any error
    retry_count: Annotated[int, take_max]        # highest value wins
    triage_summary: str | None
    notification_sent: bool
    file_name: str | None
    line_number: int | None