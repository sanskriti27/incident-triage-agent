# tools/debugger.py
import os
from openai import OpenAI
from agent.state import AgentState

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def debug(state: AgentState) -> AgentState:
    """
    Tool D: Reasons over full call chain context to produce triage summary.
    Input:  source_code (multi-frame), db_record, raw_log, function_name, line_number
    Output: triage_summary
    """
    prompt = f"""
    You are a senior Java backend engineer performing incident triage.
    
    An exception was detected in production. You have been given:
    - The correlated log bundle for this request
    - Source code windows for every frame in the call chain
    - The database record at the time of failure
    
    Your job is to trace the failure from the entry point down to the 
    root cause, following the call chain.

    CORRELATED LOGS:
    {state["raw_log"]}

    CALL CHAIN SOURCE CODE:
    {state["source_code"]}

    DATABASE RECORD:
    {state["db_record"]}

    Produce a triage report with exactly these sections:

    1. ENTRY POINT
       Where did the request enter the system? 
       Which controller/service initiated the flow?

    2. CALL CHAIN SUMMARY
       Trace the flow from entry point to crash site.
       One line per frame — what each method did and passed forward.

    3. ROOT CAUSE
       One sentence. What exactly caused the failure?
       Reference the specific variable, method, and line number.

    4. WHY IT HAPPENED
       Two to three sentences. Reference both the code and DB record.
       What data condition triggered this code path?

    5. RECOMMENDED FIX
       Concrete and specific. Reference the exact method and line.
       Include a code snippet if helpful.

    6. SEVERITY
       Low / Medium / High — and why.

    7. PREVENTION
       One recommendation to stop this class of bug recurring.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a senior Java engineer. Be precise, technical, and concise. Always reference specific line numbers and variable names from the code provided."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2  # low temperature = more precise, less creative
    )

    return {
        **state,
        "triage_summary": response.choices[0].message.content,
        "error": None
    }