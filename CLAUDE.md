# miniMasterSchool — AI Context File

## What This Project Is
A mini admissions flow engine for Masterschool. Candidates move through an ordered list of tasks; each task is a pure handler that returns a `Command`. The engine merges updates, records pass/fail, advances (or splices a `goto`), and exposes REST endpoints for a frontend or Swagger.

---

## Tech Stack
- **Language:** Python
- **Web framework:** FastAPI
- **Storage:** In-memory only (no database)

---

## Domain Model

### Flow structure (`FLOW` in `graph.py`)
Steps are ordered. Each step has a `name` and an ordered list of **task** keys. A step is done when all its tasks are completed.

```
1. personal_details — tasks: personal_details
2. iq_test — tasks: iq_test (passes if score > 75)
3. interview — tasks: schedule_interview, perform_interview (pass if decision == passed_interview)
4. sign_contract — tasks: upload_id, sign_contract
5. payment — tasks: payment
6. join_slack — tasks: join_slack
```

### Per-candidate path: `task_sequence`
On user creation, `task_sequence` is initialized as the flat list of all spine tasks from `FLOW`. The engine advances using this list (not only the global spine), so **dynamic tasks** inserted via `Command.goto` appear in the same sequence and in **`GET /flow`** for that user.

### Branching (`Command.goto`)
If a node sets `goto` to another **task** name, the engine inserts that task immediately after the current task in `task_sequence` and sets `current_step` to it. If `goto` is absent and the command is `COMPLETED`, `current_step` becomes the next entry in `task_sequence` (or `None` at the end).

### Acceptance and rejection
- **`rejected`:** any task in `completed_steps` is `FAILED` (spine or dynamic / `goto` tasks).
- **`accepted`:** `candidate.is_accepted` is set when the last task in `task_sequence` completes successfully (no further next task).
- **`in_progress`:** otherwise.

### Nodes and candidate updates (`nodes.py`)
- **`personal_details_form`** is the only place **first_name, last_name, email** are written onto `Candidate`; payload must include **user_id** (validated; not merged into identity).
- Other nodes validate webhook payloads but only merge **task-specific** fields (e.g. `iq_score`, `passport_number` if the model has it) and **`timestamp`** as “last activity” — not `user_id` or identity email from later steps.

---

## Architecture

### Orchestrator (`graph.py` — `FlowManager`)
Registers `TASK_HANDLERS`, runs the handler for the current task, applies `Command.update` (only keys that exist on `Candidate`), records `completed_steps`, then handles `goto` vs linear advance using `task_sequence`.

### Nodes (`nodes.py`)
Pure functions: `(candidate, payload) -> Command`. They do not define default order; that lives in `FLOW` and `task_sequence`.

### Service (`service.py`)
`CandidatesInfo` (store) + `AdmissionsService`: load candidate, enforce **payload `user_id` vs path/body user id**, block updates when status is **rejected/accepted**, validate step vs task via `_task_to_step`, call `FlowManager`, persist.

### API (`main.py`)
Routes and Pydantic models only. **Global handlers** for `UserNotFoundError` (404) and `InvalidFlowOperationError` (400). Missing-user paths on read endpoints use `HTTPException(404)`.

---

## Files

| File | Role |
|------|------|
| `models.py` | `Candidate`, `Command`, `StepStatus` |
| `nodes.py` | One function per task |
| `graph.py` | `FLOW`, `TASK_HANDLERS`, `FlowManager` |
| `service.py` | Store + `AdmissionsService` + `_task_to_step` |
| `main.py` | FastAPI app, exception handlers, endpoints |
| `tests/` | Pytest coverage for flow, nodes, API |

---

## REST API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users` | Body: `{ "email" }` — create candidate, returns `user_id` |
| `GET` | `/flow?user_id=` | Step list derived from that candidate’s `task_sequence` |
| `GET` | `/users/{user_id}/current` | `{ "step", "task" }` |
| `PUT` | `/tasks` | Body: `user_id`, `step_name`, `task_name`, `payload` or `task_payload` (same object) |
| `GET` | `/users/{user_id}/status` | `{ "status": "accepted" \| "rejected" \| "in_progress" }` |

Interactive docs: **`/docs`**.

---

## Conventions
- Nodes stay pure; no default flow encoded in nodes.
- Prefer single source of truth for step names (`FLOW` / shared constants).
- Avoid comments that only restate the code; explain non-obvious intent only.
