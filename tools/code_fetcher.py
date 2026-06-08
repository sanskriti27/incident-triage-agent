# tools/code_fetcher.py
import re
import os
import requests
from agent.state import AgentState

STACK_TRACE_PATTERN = re.compile(r'at ([\w.]+)\(([\w]+\.java):(\d+)\)')
SAMPLE_DIR = "sample_service"
USE_LOCAL = os.getenv("USE_LOCAL", "true").lower() == "true"
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_REPO = os.getenv("GITLAB_REPO")

def fetch_code(state: AgentState) -> AgentState:
    """
    Tool B: Fetches source code windows for every frame in the stack trace.
    Input:  state["raw_log"]
    Output: state["source_code"] — concatenated windows from all frames
    """
    try:
        raw_log = state["raw_log"]

        # Extract ALL frames from stack trace, not just the first
        matches = STACK_TRACE_PATTERN.findall(raw_log)

        if not matches:
            return {
                **state,
                "error": "No stack frames found in log",
                "retry_count": state["retry_count"] + 1
            }

        code_windows = []
        seen_files = set()  # avoid fetching same file twice

        for full_path, filename, line_number in matches:
            if filename in seen_files:
                continue
            seen_files.add(filename)

            class_name = full_path.split(".")[-2]  # e.g. PaymentService
            line_number = int(line_number)

            try:
                source = _fetch_local(filename) if USE_LOCAL else _fetch_remote(filename)
                window = _extract_window(source, line_number)
                code_windows.append(
                    f"--- {class_name} ({filename}:{line_number}) ---\n{window}"
                )
            except FileNotFoundError:
                code_windows.append(
                    f"--- {filename} not found in sample_service ---"
                )

        return {
            **state,
            "source_code": "\n\n".join(code_windows),
            "error": None
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "retry_count": state["retry_count"] + 1
        }


def _extract_window(source: str, line_number: int) -> str:
    """Extract 10 lines above and below the failure point"""
    lines = source.splitlines()
    start = max(0, line_number - 10)
    end = min(len(lines), line_number + 10)
    return "\n".join(
        f"{i+1}: {line}"
        for i, line in enumerate(lines[start:end], start=start)
    )


def _fetch_local(filename: str) -> str:
    path = os.path.join(SAMPLE_DIR, filename)
    with open(path, "r") as f:
        return f.read()


def _fetch_remote(filename: str) -> str:
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_REPO}/repository/files/{filename}/raw"
    response = requests.get(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})
    response.raise_for_status()
    return response.text