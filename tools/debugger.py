# tools/debugger.py
import os
from openai import OpenAI
from agent.state import AgentState

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def debug(state: AgentState) -> AgentState:
    """
    Tool D: Reasons over collected context to produce triage summary.
    Input:  source_code, db_record, function_name, line_number
    Output: triage_summary
    """
    prompt = f"""
    You are a Java backend engineer performing log triage.
    
    Exception occurred in: {state["function_name"]} at line {state["line_number"]}
    
    Relevant source code:
    {state["source_code"]}
    
    Database record at time of failure:
    {state["db_record"]}
    
    Analyse what caused this exception and provide:
    1. Root cause (one sentence)
    2. Why it happened (two to three sentences referencing the code and data)
    3. Recommended fix (concrete, specific)
    4. Severity (Low / Medium / High)
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        **state,
        "triage_summary": response.choices[0].message.content,
        "error": None
    }