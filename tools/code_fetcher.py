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
                "warnings": ["No stack frames found in log"]
            }

        code_windows = []
        seen_files = set()  # avoid fetching same file twice

        file_name = None
        line_num = None

        for full_path, filename, line_number in matches:

            if file_name is None:
                file_name = filename
            if line_num is None:
                line_num = int(line_number)
            
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

        print(f"Code windows: {code_windows}")

        return {
            "source_code": "\n\n".join(code_windows),
            "file_name": file_name,
            "line_number": line_num,
            "error": None
        }

    except Exception as e:
        return {
            "error": str(e),
            "retry_count": state["retry_count"] + 1
        }


def _extract_window(source: str, line_number: int) -> str:
    lines = source.splitlines()
    print(f"[Debug] File has {len(lines)} lines, extracting around line {line_number}")
    start = max(0, line_number - 10)
    end = min(len(lines), line_number + 10)
    window = "\n".join(
        f"{i+1}: {line}"
        for i, line in enumerate(lines[start:end], start=start)
    )
    print(f"[Debug] Window: {window}")
    return window


def _fetch_local(filename: str) -> str:
    path = os.path.join(SAMPLE_DIR, filename)
    with open(path, "r") as f:
        return f.read()


def _fetch_remote(filename: str) -> str:
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_REPO}/repository/files/{filename}/raw"
    response = requests.get(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})
    response.raise_for_status()
    return response.text