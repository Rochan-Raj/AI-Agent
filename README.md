# OpenOps Agent — Autonomous Company Operations Agent

A runnable prototype for the CentrAlign AI Founding Engineer problem statement. It interprets an invoice task, searches local invoice documents, extracts structured fields, writes to a SQLite mock finance system, handles a simulated transient error, verifies the saved record, and logs its execution trace.

## Requirements
- Python 3.10+
- Hosted LLM API key optional; deterministic fallback is included.
- Your Ryzen 5 5600H / 8 GB RAM / GTX 1650 is sufficient; no local LLM or GPU is required.

## Setup — Windows PowerShell
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Add your hosted API key to `.env` if desired. Never commit `.env`.

## Run
```powershell
python main.py "Find the latest invoice from Acme Ltd, enter the amount and due date into finance, and verify it"
```
Simulate one transient write failure:
```powershell
python main.py "Process the latest invoice from Acme Ltd" --fail-first-save
```
Run tests:
```powershell
pytest -q
```

## Architecture
Natural-language task -> task interpreter -> restricted workflow validation -> orchestrator -> invoice tools + finance tools -> read-after-write verification -> evidence-based summary. SQLite stores finance records and task events.

## Project structure
- `main.py`: CLI entry point
- `planner.py`: hosted LLM intent extraction plus fallback
- `agent.py`: orchestration, bounded retry, verification
- `invoice_tools.py`: local invoice discovery and parsing
- `finance_tools.py`: mock finance-system interface and idempotent writes
- `storage.py`: SQLite persistence and audit events
- `models.py`: typed data structures
- `data/invoices/`: sample data
- `tests/`: unit and integration tests

## Engineering choices
- LLM output is not executable code; only the predefined invoice workflow is allowed.
- An explicit orchestration loop is easier to debug and test than an unconstrained agent loop.
- The invoice ID is unique, so repeated writes are idempotent.
- Completion requires reading the finance record back and comparing invoice ID, vendor, amount, and due date.
- Retries are bounded.

## Demo plan
1. Run the Acme task and show extracted values.
2. Run with `--fail-first-save` and show the retry.
3. Run the same invoice again to show idempotency.
4. Inspect the trace and point to the read-after-write verification.
5. Explain how a second connector or workflow would be added.

## Limitations and next steps
This prototype parses text-based `.txt` invoices only, uses a local SQLite mock finance system, and supports one workflow. Next add a Playwright UI, PDF/OCR support, durable checkpoints, approval queue, connector interfaces, and a repeatable evaluation suite. Production would require tenant isolation, authentication, authorization, secret management, encryption, concurrency controls, and stronger audit/security review.

Use mock data only. Do not connect this prototype to real finance systems or use confidential company data.

## Real browser workflow (Playwright + local finance website)

This optional extension opens a local finance UI in Chromium, fills the invoice form using Playwright, submits it, and verifies the saved record by reading the table back. It uses the same SQLite database as the original CLI workflow.

### Install browser support

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

### Terminal 1 — start the local finance website

```powershell
python finance_web.py
```

Keep this terminal running. Open `http://127.0.0.1:5000` in your browser if you want to inspect the demo finance app manually.

### Terminal 2 — run the browser agent

Open a second VS Code terminal in this same `openops_agent` folder and ensure `.venv` is activated, then run:

```powershell
python browser_workflow.py "Acme Ltd"
```

The default mode opens a visible Chromium window. To run headless:

```powershell
python browser_workflow.py "Acme Ltd" --headless
```

Expected invoice: `ACME-1043`, amount `25000.00`, due date `2026-10-20`. Re-running is idempotent for the same invoice ID: the app does not create duplicate rows. The website is a local demo, not a production finance system. Only use sample or non-sensitive data.
