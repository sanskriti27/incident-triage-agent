# agent/graph.py
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from tools.log_parser import parse_log
from tools.code_fetcher import fetch_code
from tools.db_fetcher import fetch_db
from tools.debugger import debug
from notifier.emailer import notify

def should_retry(state: AgentState) -> str:
    if state["error"] and state["retry_count"] < 3:
        return "retry"
    elif state["error"]:
        return "fail"
    return "continue"

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("parse_log", parse_log)
    graph.add_node("fetch_code", fetch_code)
    graph.add_node("fetch_db", fetch_db)
    graph.add_node("debug", debug)
    graph.add_node("notify", notify)

    # Fixed pipeline edges
    graph.set_entry_point("parse_log")
    graph.add_conditional_edges("parse_log", should_retry, {
        "continue": "fetch_code",
        "retry": "parse_log",
        "fail": "notify"
    })
    graph.add_conditional_edges("fetch_code", should_retry, {
        "continue": "fetch_db",
        "retry": "fetch_code",
        "fail": "notify"
    })
    graph.add_conditional_edges("fetch_db", should_retry, {
        "continue": "debug",
        "retry": "fetch_db",
        "fail": "notify"
    })
    graph.add_edge("debug", "notify")
    graph.add_edge("notify", END)

    return graph.compile()