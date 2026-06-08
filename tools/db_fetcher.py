# tools/db_fetcher.py
import re
import sqlite3
import os
from agent.state import AgentState

DB_PATH = "sample_service/transactions.db"

def fetch_db(state: AgentState) -> AgentState:
    """
    Tool C: Extracts transaction ID from log and queries DB for record.
    Input:  state["raw_log"]
    Output: state["db_record"]
    """
    try:
        # Try to find a transaction ID in the raw log
        match = re.search(r'TX-\d+', state["raw_log"])
        
        if not match:
            # No ID found — return empty record, don't fail pipeline
            return {
                **state,
                "db_record": {"note": "No transaction ID found in log"},
                "error": None
            }

        tx_id = match.group(0)  # e.g. TX-1234
        record = _query_db(tx_id)

        return {
            **state,
            "db_record": record,
            "error": None
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "retry_count": state["retry_count"] + 1
        }


def _query_db(tx_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # returns dict-like rows
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE tx_id = ?", 
        (tx_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {"note": f"No record found for {tx_id}"}