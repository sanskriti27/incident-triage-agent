# kafka_consumer/consumer.py
import re
import time
import os
from collections import deque
import redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from agent.graph import build_graph
from agent.state import AgentState
from redis.exceptions import ConnectionError, TimeoutError

LOG_PATH = "sample_logs/errors.log"
POLL_INTERVAL = 2
TIME_WINDOW = 50

STACK_TRACE_PATTERN = re.compile(r'at [\w.]+\([\w]+\.java:\d+\)')
REQUEST_ID_PATTERN = re.compile(r'req-[\w-]+', re.IGNORECASE)
THREAD_ID_PATTERN = re.compile(r'\[([^\]]+)\]')

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

REDIS_DEDUPE_PORT = int(os.getenv("REDIS_DEDUPE_PORT", 6379))
REDIS_DEDUPE_TTL = int(os.getenv("REDIS_DEDUPE_TTL", 300))
REDIS_DEDUPE_TIMEOUT = int(os.getenv("REDIS_DEDUPE_TIMEOUT", 1))

# TODO Add redis caching

r = redis.Redis(
    host=REDIS_HOST, port=REDIS_DEDUPE_PORT, decode_responses=True,
    socket_connect_timeout=REDIS_DEDUPE_TIMEOUT,
    socket_timeout=REDIS_DEDUPE_TIMEOUT
    )
r.set_retry(Retry(NoBackoff(), 1))

def tail_log(filepath: str):
    with open(filepath, "r") as f:
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

def should_trigger(line: str) -> bool:
    return "ERROR" in line and bool(STACK_TRACE_PATTERN.search(line))

def store_in_redis(req_id: str, line: str):
    """Append log line to Redis list for this req_id, reset TTL"""
    r.rpush(f"logs:{req_id}", line)
    r.expire(f"logs:{req_id}", REDIS_DEDUPE_TTL)

def get_correlated_logs(req_id: str, thread_id: str, buffer: list) -> str:
    """Try Redis first, fall back to local buffer"""
    if req_id:
        try:
            redis_logs = r.lrange(f"logs:{req_id}", 0, -1)
            if redis_logs:
                print(f"[Consumer] Fetched {len(redis_logs)} lines from Redis")
                return "\n".join(redis_logs)
        except (ConnectionError, TimeoutError) as e:
            print(f"[Consumer] Redis unavailable: {e}")
            
    return get_correlated_logs_from_buffer(req_id, thread_id, buffer)

def get_correlated_logs_from_buffer(req_id: str, thread_id: str, buffer: list) -> str:
    """Fallback — correlate from local buffer"""
    print(f"[Consumer] Falling back to local buffer")
    correlated = []
    for log_line in buffer:
        matches_req = req_id and req_id in log_line
        matches_thread = thread_id and f"[{thread_id}]" in log_line
        if matches_req or matches_thread:
            correlated.append(log_line)
    return "\n".join(correlated)

def is_active(req_id: str) -> bool:
    try:
        is_active_flag = r.exists(f"active:{req_id}") == 1
        return is_active_flag
    except Exception as e:
        print(f"[Consumer] Failed is_active with error: {e}")
        return False

def mark_active(req_id: str):
    r.set(f"active:{req_id}", "1", ex=REDIS_DEDUPE_TTL)

def clear_active(req_id: str):
    r.delete(f"active:{req_id}")

def start_consumer():
    graph = build_graph()
    print(f"[Consumer] Watching {LOG_PATH} for errors...")

    for line, buffer in tail_log(LOG_PATH):

        req_id, thread_id = extract_identifiers(line)
        
        # Store every line in Redis grouped by req_id
        if req_id:
            try:
                store_in_redis(req_id, line)
            except (ConnectionError, TimeoutError) as e:
                print(f"[Consumer] Redis unavailable: {e}")      

        if should_trigger(line):
            print(f"\n[Consumer] Exception detected")
            print(f"[Consumer] Request ID: {req_id} | Thread: {thread_id}")

            # Deduplication — skip if triage already running for this req_id
            if req_id and is_active(req_id):
                print(f"[Consumer] Triage already active for {req_id} — skipping duplicate")
                continue

            correlated_log = get_correlated_logs(req_id, thread_id, buffer)
            print(f"[Consumer] Correlated {len(correlated_log.splitlines())} log lines")

            if req_id:
                try:
                    mark_active(req_id)
                except Exception as e:
                    print(f"[Consumer] Error while mark_active: {e}")

            try:
                initial_state: AgentState = {
                    "raw_log": correlated_log or line,
                    "error": None,
                    "retry_count": 0
                }
                graph.invoke(initial_state)
            finally:
                if req_id:
                    try:
                        clear_active(req_id)
                    except Exception as e:
                        print(f"[Consumer] Error while clear_active: {e}")
