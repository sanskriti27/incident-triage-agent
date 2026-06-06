from typing import TypedDict, Optional

class AgentState(TypedDict):
    raw_log: str
    function_name: Optional[str]
    line_number: Optional[int]
    source_code: Optional[str]
    db_record: Optional[dict]
    triage_summary: Optional[str]
    retry_count: int
    error: Optional[str]