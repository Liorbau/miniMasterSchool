# miniMasterSchool

## What this is

miniMasterSchool is a small admissions workflow demo: a candidate moves through steps with pass/fail rules and optional branching. It exposes a REST API (FastAPI) so a real UI or another service could drive the flow. State is kept in memory, good for learning and tests, not for production persistence.

## LangGraph-style

This project borrows the same architectural idea of LangGraph: a flow config plus small node functions that take shared state and return a structured result (`Command` with status, optional `goto`, and a small `update` dict). A central orchestrator applies that result and decides what happens next.

So: same separation of concerns (config + nodes + orchestrator), without a framework aimed mainly at language-model workflows.

## Architecture 

1. `graph.py` - Defines `FLOW` (steps and tasks), maps task names to handlers, and implements `FlowManager`: run handler, merge safe updates into `Candidate`, record step outcome, then follow `goto` or advance along the candidate’s `task_sequence`.
2. `nodes.py` - One function per task: validate payload, return `Command`. `personal_details_form` is the only node that sets core identity (`first_name`, `last_name`, `email`), later steps validate webhooks but avoid overwriting identity.
3. `service.py` - In-memory users, guards (closed flows, step/task consistency, payload `user_id` checks), `get_flow` from each user’s `task_sequence`, and rejection when any task (including dynamic ones) is marked failed.
4. `main.py` - FastAPI routes, Pydantic models, and global exception handlers for domain errors.

## How to run

From the project root, install dependencies (Python 3.10+ recommended):

```bash
pip install -r requirements.txt
```

Start the API:

```bash
py -m uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs to try the API interactively.

Run tests:

```bash
py -m pytest tests/ -q
```
