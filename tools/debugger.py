# tools/debugger.py
import os
from openai import OpenAI
from agent.state import AgentState

def debug(state: AgentState) -> AgentState:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""An exception was detected in production. Analyse the following and produce a triage report.

    CORRELATED LOGS:
    {state["raw_log"]}

    CALL CHAIN SOURCE CODE:
    {state["source_code"]}

    DATABASE RECORD:
    {state["db_record"]}

    Produce a triage report with exactly these sections:

    1. ENTRY POINT
    Where did the request enter the system? Which controller initiated the flow?

    2. CALL CHAIN SUMMARY
    Trace the flow from entry point to crash site. One line per frame.

    3. ROOT CAUSE
    One sentence. Reference the specific variable, method, and line number.

    4. WHY IT HAPPENED
    Two to three sentences referencing both the code and DB record.

    5. RECOMMENDED FIX
    Concrete and specific. Reference the exact method and line. Include a code snippet.

    6. SEVERITY
    Low / Medium / High and why.

    7. PREVENTION
    One recommendation to stop this class of bug recurring.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a senior Java engineer. Be precise and technical. Always reference specific line numbers and variable names from the code provided."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return {
        **state,
        "triage_summary": response.choices[0].message.content,
        "error": None
    }