# kafka_consumer/consumer.py
import re
import time
from collections import deque
from agent.graph import build_graph
from agent.state import AgentState

LOG_PATH = "sample_logs/errors.log"
POLL_INTERVAL = 2
TIME_WINDOW = 50  # collect logs within 50 lines before/after exception

STACK_TRACE_PATTERN = re.compile(r'at [\w.]+\([\w]+\.java:\d+\)')
REQUEST_ID_PATTERN = re.compile(r'req-[\w-]+', re.IGNORECASE)
THREAD_ID_PATTERN = re.compile(r'\[([^\]]+)\]')  # e.g. [main] or [thread-12]

def tail_log(filepath: str):
    with open(filepath, "r") as f:
        # Keep a rolling buffer of recent lines for correlation
        buffer = deque(maxlen=TIME_WINDOW)
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                buffer.append(line.strip())
                yield line.strip(), list(buffer)
            else:
                time.sleep(POLL_INTERVAL)

def extract_identifiers(line: str) -> tuple:
    req_match = REQUEST_ID_PATTERN.search(line)
    thread_match = THREAD_ID_PATTERN.search(line)
    req_id = req_match.group(0) if req_match else None
    thread_id = thread_match.group(1) if thread_match else None
    return req_id, thread_id

def correlate_logs(buffer: list, req_id: str, thread_id: str) -> str:
    """Gather all lines from buffer matching req_id or thread_id"""
    correlated = []
    for line in buffer:
        matches_req = req_id and req_id in line
        matches_thread = thread_id and f"[{thread_id}]" in line
        if matches_req or matches_thread:
            correlated.append(line)
    return "\n".join(correlated)

def should_trigger(line: str) -> bool:
    return "ERROR" in line and bool(STACK_TRACE_PATTERN.search(line))

def start_consumer():
    graph = build_graph()
    print(f"[Consumer] Watching {LOG_PATH} for errors...")

    for line, buffer in tail_log(LOG_PATH):
        if should_trigger(line):
            req_id, thread_id = extract_identifiers(line)
            correlated_log = correlate_logs(buffer, req_id, thread_id)

            print(f"\n[Consumer] Exception detected")
            print(f"[Consumer] Request ID: {req_id} | Thread: {thread_id}")
            print(f"[Consumer] Correlated {len(correlated_log.splitlines())} log lines")

            initial_state: AgentState = {
                "raw_log": correlated_log or line,  # fallback to single line
                "function_name": None,
                "line_number": None,
                "source_code": None,
                "db_record": None,
                "triage_summary": None,
                "retry_count": 0,
                "error": None
            }
            graph.invoke(initial_state)