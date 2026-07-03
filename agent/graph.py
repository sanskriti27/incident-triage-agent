# agent/graph.py
from langgraph.graph import StateGraph, END
from agent.register import ServiceRegistry
from agent.state import AgentState
from tools.log_parser import LogParser
from tools.code_fetcher import fetch_code
from tools.debugger import debug
from notifier.emailer import notify

CONFIG_PATH = "./config/services.yaml"

def should_retry(state: AgentState) -> str:
    if state["error"] and state["retry_count"] < 3:
        print(f"Retrying {state['service_name']}...")
        return "retry"
    elif state["error"]:
        print(f"Failed {state['service_name']}...")
        return "fail"
    return "continue"

def make_parse_node(services: dict):
    def parse_log(state: AgentState) -> AgentState:
        parser = LogParser(services)
        parsed = parser.parse(state["raw_log"])
        return {
            **state,
            "service_name": parsed.service_name,
            "error_type": parsed.error_type,
            "request_id": parsed.request_id,
            "identifier": parsed.identifier,
            "warnings": state["warnings"] + parsed.warnings
        }
    
    return parse_log

def make_fetch_node(registry: ServiceRegistry):
    def fetch_context(state: AgentState) -> AgentState:
        handler = registry.get_handler(state["service_name"])
        fetched = handler.fetch_context(state["identifier"])
        return {
            "fetched_data": fetched
        }
    return fetch_context


def build_graph():
    graph = StateGraph(AgentState)
    registry = ServiceRegistry(CONFIG_PATH)
    services = registry.get_all_services();
    print("Building graph...")
    # Add nodes
    graph.add_node("parse_log", make_parse_node(services))
    graph.add_node("fetch_code", fetch_code)
    graph.add_node("fetch_db", make_fetch_node(registry))
    graph.add_node("debug", debug)
    graph.add_node("notify", notify)

    # Fixed pipeline edges
    graph.set_entry_point("parse_log")
    graph.add_edge("parse_log", "fetch_code")
    graph.add_edge("parse_log", "fetch_db")
    graph.add_conditional_edges("fetch_code", should_retry, {
        "continue": "debug",
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