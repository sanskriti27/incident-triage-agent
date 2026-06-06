# tools/code_fetcher.py
import os
import requests
from agent.state import AgentState

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_REPO = os.getenv("GITLAB_REPO")  # e.g. "myorg/myservice"
USE_LOCAL = os.getenv("USE_LOCAL", "true").lower() == "true"
SAMPLE_DIR = "sample_service"

def fetch_code(state: AgentState) -> AgentState:
    """
    Tool B: Fetches source code around the failing line.
    Input:  state["function_name"], state["line_number"]
    Output: state["source_code"]
    """
    try:
        class_name = state["function_name"].split(".")[0]  # PaymentService
        line_number = state["line_number"]
        filename = f"{class_name}.java"

        if USE_LOCAL:
            source = _fetch_local(filename)
        else:
            source = _fetch_remote(filename)

        # Extract a window of 10 lines around the failure point
        lines = source.splitlines()
        start = max(0, line_number - 5)
        end = min(len(lines), line_number + 5)
        window = "\n".join(
            f"{i+1}: {line}" 
            for i, line in enumerate(lines[start:end], start=start)
        )

        return {
            **state,
            "source_code": window,
            "error": None
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "retry_count": state["retry_count"] + 1
        }


def _fetch_local(filename: str) -> str:
    path = os.path.join(SAMPLE_DIR, filename)
    with open(path, "r") as f:
        return f.read()


def _fetch_remote(filename: str) -> str:
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_REPO}/repository/files/{filename}/raw"
    response = requests.get(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})
    response.raise_for_status()
    return response.text