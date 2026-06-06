import re
from agent.state import AgentState

def parse_log(state: AgentState) -> AgentState:
    """
    Tool A: Extracts function name and line number from raw Java log.
    Input:  state["raw_log"]
    Output: state["function_name"], state["line_number"]
    """
    try:
        pattern = r'at ([\w.]+)\(([\w]+\.java):(\d+)\)'
        raw_log = state['raw_log']
        match = re.search(pattern, raw_log)
        if not match:
            return {
                **state,
                "error": "Failed to extract function name and line number from log",
                "retry_count": state['retry_count'] + 1
            }

        full_path = match.group(1)   # com.example.PaymentService.processPayment
        line_number = int(match.group(3))  # 47

        # Last two parts give us Class.method — most useful for Tool B
        parts = full_path.split(".")
        function_name = f"{parts[-2]}.{parts[-1]}"  # PaymentService.processPayment
        
        return {
            **state,
            "function_name": function_name,
            "line_number": line_number,
            "error": None,
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "retry_count": state["retry_count"] + 1
        }