# notifier/emailer.py
import os
import smtplib
from email.mime.text import MIMEText
from agent.state import AgentState

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")

def notify(state: AgentState) -> AgentState:
    """
    Final node: logs triage to console always, sends email if configured.
    Handles both success triage and pipeline failure gracefully.
    """
    # Build message depending on whether we have a triage or a failure
    if state.get("triage_summary"):
        subject = f"[Triage] Exception in {state.get('function_name', 'Unknown')}"
        body = f"""
    INCIDENT TRIAGE REPORT
    ======================
    File Name : {state.get('file_name')}
    Line Number : {state.get('line_number')}

    {state['triage_summary']}

    --- Raw Log ---
    {state['raw_log']}
            """
    else:
        subject = "[Triage] Pipeline failed — manual review needed"
        body = f"""
        Triage pipeline exhausted retries and could not analyse this log.

        Error    : {state.get('error')}
        Raw Log  : {state['raw_log']}
        """

    # Always print — works for everyone, no setup needed
    print("\n" + "="*50)
    print(subject)
    print("="*50)
    print(body)

    # Email only if SMTP is configured
    if all([SMTP_HOST, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL]):
        _send_email(subject, body)
    else:
        print("[Email skipped — SMTP not configured]")

    return {**state}


def _send_email(subject: str, body: str):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print("[Email sent successfully]")
    except Exception as e:
        print(f"[Email failed: {e} — triage logged to console above]")