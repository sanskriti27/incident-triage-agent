# Log Triage Agent 🔍

An AI-powered log triage system that watches for Java exceptions,
automatically gathers context, and delivers a root-cause analysis
to stakeholders — without human intervention.

Built with LangGraph, OpenAI, and Python.

---

## Why This Exists

In production, engineers waste hours manually triaging exceptions —
reading logs, finding the relevant code, querying the DB, piecing
together what went wrong. This agent does that in seconds.

---

## Architecture
![Project Screenshot](assets/log_triage_agent_architecture.svg)

> **Note:** the diagram above shows a Kafka-based ingestion path. The current
> implementation does **not** use Kafka — the consumer tails a local log file
> directly and correlates related lines via Redis. The `kafka_consumer/`
> module name is a holdover from an earlier design; diagram and naming will
> be updated to match once the local ingestion path is finalized.

**Why a fixed pipeline and not a dynamic agent?**
The debugging sequence for Java exceptions is deterministic —
you always need the code before the DB record, always need the
log before the code. A fixed pipeline is faster, cheaper, and
more predictable than letting the LLM decide tool order.

**Why no RAG?**
RAG solves "I don't know where to look." Stack traces tell us
exactly where to look — class name, file, line number. Deterministic
fetching is faster and more precise for this use case. RAG becomes
relevant at Goldman-scale codebases where the call chain spans
40+ functions across 15 files.

**Why gather-then-reason?**
Tools A, B, C are pure Python — no LLM involved. The LLM only
gets called once all context is cleanly assembled. This keeps
costs low and responses accurate.

**Local vs Remote mode**
Tool B supports both local file reading (for demo) and GitLab API
via a service account token (for production). Swap via env var.

---

## Running Locally

**Prerequisites:** Python 3.12+, and a running Redis instance (used for
log correlation and deduplication — the app will fail to start without one).

1. Clone the repo

2. Install dependencies
   ```
   pip install -r requirements.txt
   pip install redis pyyaml
   ```
   (`redis` and `pyyaml` aren't yet in `requirements.txt` — install them
   manually for now.)

3. Start Redis, if you don't already have it running
   ```
   docker run -p 6379:6379 redis
   ```

4. Set up your environment
   ```
   cp example.env .env
   ```
   then fill in at minimum `OPENAI_API_KEY`. `REDIS_HOST`/`REDIS_PORT`/`REDIS_TTL`
   default to `localhost` / `6379` / `300` if left unset. Kafka and GitLab
   variables are present in `example.env` for forward-compatibility but are
   not used by the current local-file/Redis ingestion path.

5. Create the log file the consumer watches
   ```
   mkdir -p sample_logs && touch sample_logs/errors.log
   ```

6. Run
   ```
   python main.py
   ```
   This seeds `sample_service/transactions.db` on first run and starts
   tailing `sample_logs/errors.log`.

7. In a separate terminal, append a sample error to trigger triage
   ```
   echo 'ERROR 2024-01-15 14:23:11 [thread-12] req-abc123 - Transaction failed java.lang.NullPointerException at com.example.PaymentService.processPayment(PaymentService.java:47) at com.example.OrderController.checkout(OrderController.java:50) at com.example.UserRepository.findById(UserRepository.java:14)' >> sample_logs/errors.log
   ```
   You should see a triage report printed to the console (and emailed, if
   SMTP settings are configured in `.env`).

**Configuring services:** `config/services.yaml` maps a service name (parsed
from the stack trace) to a handler — `database` (queries a local SQLite table)
or `api` (calls a REST endpoint). Unknown services fall back to a default
handler that only has the raw log available. See the existing `paymentservice`
and `authservice` entries as examples.
