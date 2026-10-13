# OpenOps Agent — Autonomous Company Operations Agent

An AI-assisted company operations prototype that processes invoice requests, extracts structured data from local invoice files, interacts with a local finance application through browser automation, and verifies the results.

The project demonstrates controlled task execution, browser automation, database persistence, idempotent writes, and read-after-write verification.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Important Technical and Design Decisions](#important-technical-and-design-decisions)
- [Assumptions](#assumptions)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [Security Considerations](#security-considerations)

## Overview

OpenOps Agent is a prototype of an autonomous company operations assistant focused on invoice processing.

Given a task such as:

> Find the latest invoice from Acme Ltd, enter the amount and due date into finance, and verify it.

The CLI workflow interprets the request, locates the latest matching invoice, extracts its fields, creates a finance record in SQLite, reads the record back, and reports whether verification succeeded.

The browser extension provides an additional end-to-end workflow. It opens a local finance web application using Playwright, fills in the invoice form, submits the record, and verifies the saved data through the browser interface.

The project uses sample invoice data and a local mock finance application. It does not require access to a real company's finance system.

## Features

- **Task interpretation:** Converts supported natural-language invoice requests into a predefined workflow.
- **Invoice discovery:** Searches local sample invoice files for the requested vendor.
- **Structured extraction:** Extracts invoice ID, vendor, amount, and due date from text-based invoices.
- **Browser automation:** Uses Playwright and Chromium to interact with a local finance web application.
- **Persistent storage:** Uses SQLite to store finance records and task events.
- **Idempotent writes:** Prevents duplicate finance records for an existing invoice ID.
- **Read-after-write verification:** Reads the saved record and compares its fields with the expected invoice data.
- **Bounded retry:** The CLI workflow includes a controlled retry mechanism for a simulated transient write failure.
- **Execution trace:** Records and displays workflow events to make execution easier to inspect and debug.
- **Automated tests:** Includes pytest tests for core invoice, finance, and agent behavior.
- **Optional hosted LLM:** Supports an OpenAI-compatible chat-completions API for CLI task interpretation, with a deterministic local fallback.

## Architecture

The project has two execution paths: a CLI-based workflow and a browser-based workflow. Both use the local invoice data and SQLite-backed finance storage, but the browser workflow submits records through the local web application's HTTP interface.

### 1. CLI workflow

```text
Natural-language task
        |
        v
Task planner / interpreter
        |
        v
Workflow validation
        |
        v
Agent orchestrator
        |
        +--------------------+
        |                    |
        v                    v
Invoice tools           Finance tools
        |                    |
        v                    v
Local invoice files     SQLite database
        |                    |
        +---------+----------+
                  |
                  v
        Read-after-write verification
                  |
                  v
        Result and execution trace
```

### 2. Browser workflow

```text
Vendor request
      |
      v
Find latest matching invoice
      |
      v
Playwright + Chromium
      |
      v
Local Flask finance application
      |
      v
Validate and save invoice
      |
      v
SQLite finance database
      |
      v
Read saved record through browser UI
      |
      v
Compare expected and observed fields
      |
      v
Success or failure result
```

### Main components

- **`planner.py`** — Interprets CLI task requests using an optional hosted LLM or a deterministic fallback.
- **`agent.py`** — Orchestrates the CLI invoice workflow, retry behavior, and verification.
- **`invoice_tools.py`** — Finds and parses local invoice files.
- **`finance_tools.py`** — Provides the CLI workflow's finance-system interface and idempotent record creation.
- **`storage.py`** — Manages SQLite persistence and task-event storage.
- **`finance_web.py`** — Provides the local Flask finance application and its invoice form.
- **`browser_workflow.py`** — Uses Playwright to fill the form, submit the invoice, and verify the saved record.
- **`models.py`** — Defines the typed data structures used by the CLI workflow.
- **`main.py`** — CLI entry point.
- **`tests/`** — Contains automated tests for the existing core workflow.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Main implementation language |
| Flask | Local finance web application |
| Playwright | Browser automation |
| Chromium | Browser controlled by Playwright |
| SQLite | Local persistent finance records and task events |
| OpenAI Python SDK | Optional hosted LLM integration for CLI task interpretation |
| python-dotenv | Loads configuration from `.env` |
| pytest | Automated testing |

### Models and external services

- **Hosted language model:** The CLI planner defaults to `gpt-4o-mini` when a valid API key is configured. The model name can be changed through environment configuration.
- **LLM fallback:** If the hosted API is not configured or is unavailable, the CLI planner uses deterministic local logic for supported requests.
- **Browser workflow:** Does not require an LLM API call. It accepts a vendor name and uses the existing invoice discovery logic.
- **Local finance application:** A custom Flask application using SQLite. It is a mock system created for this project.
- **External services:** No external finance service or paid browser automation service is required. A hosted LLM API is optional for the CLI workflow.

No model is trained as part of this project, and no local GPU inference is required.

## Project Structure

```text
openops_agent/
├── main.py
├── agent.py
├── planner.py
├── models.py
├── invoice_tools.py
├── finance_tools.py
├── storage.py
├── finance_web.py
├── browser_workflow.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   └── invoices/
│       ├── acme_invoice_1042.txt
│       ├── acme_invoice_1043.txt
│       └── northwind_invoice_207.txt
└── tests/
    ├── test_agent.py
    ├── test_finance_tools.py
    └── test_invoice_tools.py
```

Runtime-generated SQLite database files may also be created, depending on the configured database path.

## Prerequisites

- Python 3.10 or newer.
- pip.
- Git, if cloning the repository.
- Internet access during dependency installation.
- Chromium installed through Playwright for browser automation.
- An OpenAI-compatible API key only if hosted LLM task interpretation is desired.

The application is designed to run on an ordinary development computer. A dedicated GPU is not required.

## Setup and Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd openops_agent
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with the actual repository URL.

If you downloaded the project ZIP instead, extract it and open the inner `openops_agent` directory in VS Code.

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install the Playwright browser

```bash
python -m playwright install chromium
```

### 5. Configure environment variables

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

On Linux or macOS:

```bash
cp .env.example .env
```

The `.env` file contains the following example configuration:

```dotenv
OPENAI_API_KEY=replace_me
OPENAI_MODEL=gpt-4o-mini
# OPENAI_BASE_URL=https://your-provider.example/v1
```

Replace the placeholder with your API key if you want to use the hosted LLM. Leave the placeholder unchanged if you want to use the local fallback.

**Never commit `.env` or expose API keys in your repository.**

## Running the Application

### Option 1: Run the CLI agent

From the project root, execute:

```bash
python main.py "Find the latest invoice from Acme Ltd, enter the amount and due date into finance, and verify it"
```

The CLI workflow should identify the latest matching sample invoice, save its details to SQLite, verify the stored record, and print an execution trace.

### Simulate a transient write failure

```bash
python main.py "Process the latest invoice from Acme Ltd" --fail-first-save
```

This enables the project's simulated first-save failure. Inspect the execution trace to see whether the bounded retry succeeds and verification completes.

### Option 2: Run the browser-based finance workflow

The browser workflow requires two terminals.

**Terminal 1 — start the local finance application:**

```bash
python finance_web.py
```

Keep the server running. The application listens on example:

`http://127.0.0.1:5000`

Open that address in a browser to inspect the invoice form and saved finance records.

**Terminal 2 — run the Playwright workflow:**

Activate the virtual environment in the second terminal, then execute:

```bash
python browser_workflow.py "Acme Ltd"
```

Playwright launches Chromium, locates the latest matching invoice, fills in the form, submits it, and verifies the resulting record.

To run without displaying the browser window:

```bash
python browser_workflow.py "Acme Ltd" --headless
```

The browser workflow verifies the invoice ID, vendor, amount, and due date by reading the saved row back from the web page.

### Sample expected result

The included Acme sample invoice has these details:

| Field | Expected value |
|---|---|
| Invoice ID | `ACME-1043` |
| Vendor | `Acme Ltd` |
| Amount | `25000.00` |
| Due date | `2026-10-20` |

The record ID can vary according to the existing database state.

Re-running the same invoice is designed not to create a duplicate row. If an existing invoice ID has conflicting details, the web application reports a conflict instead of silently replacing the record.

## Testing

Run the automated tests from the project root:

```bash
python -m pytest -q
```

The current starter test suite has been verified with five passing tests.

These tests cover parts of the invoice tools, finance tools, and CLI agent behavior. They do not constitute comprehensive end-to-end testing of the browser workflow or production reliability.

The browser workflow can also be exercised manually by starting `finance_web.py` and running `browser_workflow.py` in a second terminal.

## Important Technical and Design Decisions

### 1. Constrained workflow instead of unrestricted agent behavior

The project uses a predefined invoice-processing workflow rather than allowing an LLM to execute arbitrary code or invoke unrestricted tools.

This makes the prototype easier to inspect, debug, and test, while limiting the actions the task planner can select.

### 2. Optional LLM with a deterministic fallback

The CLI planner can use a hosted LLM to interpret supported natural-language requests. When the API is not configured or is unavailable, a local fallback handles supported invoice requests.

This reduces dependency on a paid API during basic development and testing. The fallback is intentionally limited and is not equivalent to a general-purpose language model.

### 3. SQLite for local persistence

SQLite provides a simple, self-contained database for the demo. It avoids requiring a separate database server and makes the project straightforward to run locally.

It is suitable for this prototype, but it does not provide the operational controls expected from a production finance platform.

### 4. Idempotency for duplicate prevention

Invoice IDs are treated as unique identifiers. The database's uniqueness constraint and conflict-handling logic prevent repeated submissions from creating duplicate records for the same invoice ID.

The application also checks whether an existing record's fields match the submitted values rather than silently accepting conflicting invoice details.

### 5. Read-after-write verification

The workflow does not rely solely on a successful submit action or database write result.

The CLI workflow reads the finance record back through its finance interface. The browser workflow reads the saved row through the browser interface and compares the invoice fields with the expected values.

This provides evidence that the intended data was saved and displayed correctly.

### 6. Bounded retries

The CLI workflow uses a limited retry mechanism for the simulated transient write failure. Bounded retries reduce the risk of an uncontrolled loop.

The browser workflow currently does not implement a general retry-and-resume mechanism for browser failures.

### 7. Browser automation through Playwright

Playwright interacts with a real Chromium browser and the local finance website. The browser workflow fills the invoice form, submits it, waits for the success indicator, and verifies the saved row.

This provides an end-to-end browser interaction without connecting to a real financial service.

## Assumptions

- The initial use case is processing a single vendor's latest invoice.
- The supplied `.txt` files are representative sample invoices and contain parseable fields.
- The latest invoice can be selected using the existing local invoice-discovery logic.
- Invoice IDs uniquely identify records within the mock finance system.
- The local finance application is available at `http://127.0.0.1:5000` when the browser workflow starts.
- The user runs both commands from the project root and has installed the required dependencies.
- The local machine and sample data are trusted for demonstration purposes.
- A hosted LLM is optional; the core invoice workflow can be exercised without one.

## Known Limitations

- **Single workflow:** The prototype supports invoice processing, not general company operations.
- **Text-only input:** Invoice extraction is limited to the supplied text-based `.txt` files. PDF parsing, OCR, and image-based document understanding are not implemented.
- **Limited intent handling:** The local fallback uses simple pattern matching and does not provide general natural-language understanding.
- **Optional LLM integration:** Hosted LLM interpretation is implemented for the CLI planner only. The browser workflow accepts a vendor name directly rather than autonomously planning browser actions with an LLM.
- **Mock finance application:** The Flask application is intended for local demonstration, not real financial transactions.
- **Local database:** SQLite is used instead of a production database with multi-user access controls and operational monitoring.
- **Limited recovery:** The CLI has a bounded retry for a simulated transient write failure, but the project does not yet provide durable recovery from arbitrary browser failures or process restarts.
- **Limited evaluation:** The five existing tests do not measure performance across a large invoice dataset, multiple vendors, or diverse failure scenarios.
- **No production security model:** Authentication, multi-tenant isolation, role-based authorization, and a formal approval process are not implemented.
- **Browser prerequisites:** Browser automation requires a working Playwright installation and Chromium.
- **No external integrations:** The project does not connect to actual accounting, payment, email, or enterprise resource planning systems.

## Future Improvements

Given additional development time, I would prioritize the following:

1. **Durable task checkpoints:** Persist task state and completed steps so interrupted workflows can resume after a process restart.
2. **Browser failure recovery:** Add bounded retries for navigation, element timeouts, transient HTTP failures, and submission errors, while preserving duplicate protection.
3. **Broader document support:** Add PDF text extraction and OCR for scanned invoices, with validation and confidence checks for extracted fields.
4. **Human approval and permissions:** Require approval before sensitive or consequential actions, and implement explicit tool permissions.
5. **Additional business workflows:** Add another workflow, such as purchase-order matching or expense processing, using reusable tool interfaces.
6. **Stronger testing:** Add browser integration tests, duplicate-submission tests, malformed-input tests, and failure-injection tests.
7. **Evaluation framework:** Measure task success rate, field-extraction accuracy, verification rate, retry recovery rate, duplicate prevention, and execution time.
8. **Observability:** Improve structured logs, task timelines, error reporting, and trace inspection.
9. **Production-grade security:** Add authentication, authorization, secret management, data protection, audit controls, and secure deployment practices.
10. **Deployment and usability:** Add a simple dashboard, configuration validation, and containerized development setup.

The priority would be to make the existing workflow reliable and recoverable before introducing multiple agents or broad autonomous capabilities.

## Security Considerations

This project is a local proof of concept, not a production finance system.

- Use only synthetic or non-sensitive invoice data.
- Never commit API keys, `.env` files, database credentials, or confidential business information.
- Keep the local finance server bound to `127.0.0.1` for development.
- Do not connect this prototype to real finance systems or authorize actual payments.
- Validate input and enforce explicit permissions before expanding the available actions.
- Review dependencies and security controls before deploying the application beyond a local development environment.

## Conclusion

OpenOps Agent demonstrates a constrained AI-assisted operations workflow with local data extraction, persistent finance records, browser automation, and explicit result verification.

The project emphasizes observable execution and controlled actions rather than unrestricted autonomy. Its current implementation is a foundation for exploring reliable AI agents that can perform practical business tasks, verify their outcomes, and recover safely from failures as the system evolves.
