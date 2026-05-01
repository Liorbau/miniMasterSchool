# miniMasterSchool — AI Context File

## What This Project Is
A mini admissions flow engine for Masterschool. Candidates progress through a fixed sequence of steps; the engine handles conditional logic, sub-tasks, and exposes REST endpoints for a frontend to consume.

---

## Tech Stack
- **Language:** Python
- **Web framework:** FastAPI
- **Storage:** In-memory only (no database)

---

## Domain Model

### Flow Structure
Steps are ordered. A step is complete when all its tasks are complete. A step with no explicit tasks is itself a single task.

```
1. personal_details      — no sub-tasks
2. iq_test               — no sub-tasks, passes if score > 75
   2b. second_chance     — HIDDEN; only visible to users with score 60–75
3. interview             — tasks: schedule_interview, perform_interview (passes if decision == 'passed_interview')
4. sign_contract         — tasks: upload_id, sign_contract
5. payment               — no sub-tasks
6. join_slack            — no sub-tasks
```

### Key Rule: Hidden Steps
`second_chance` must NOT appear in `GET /flow` for users it doesn't apply to. It is a conditional, hidden node only injected into a candidate's path when `60 <= iq_score <= 75`.

---

## Architecture Decisions

### Orchestrator Pattern
The engine (`graph.py`) is the orchestrator. Nodes (`nodes.py`) are pure functions — they receive a `Candidate` and a payload, execute task logic, and return a `Command`. They do NOT know about the flow order.

### Step/Task Config as Data
The flow is defined as a data structure (list of `Step` objects), not as imperative code. This allows reordering, adding, or removing steps without touching engine logic.

```python
# Target shape — not yet implemented
FLOW = [
    Step("personal_details", personal_details_form),
    Step("iq_test", iq_test, condition=lambda c, p: p["score"] > 75),
    Step("second_chance", second_chance, condition=lambda c, p: 60 <= p["score"] <= 75, hidden=True),
    ...
]
```

### Command Object
Inspired by LangGraph. A node returns a `Command` to signal:
- `goto`: which step to move to next (optional; engine advances by default)
- `step_status`: outcome of the current step (`COMPLETED` / `FAILED`)
- `update`: dict to merge into `Candidate` state

---

## Files

| File | Role |
|---|---|
| `models.py` | `Candidate`, `Command`, `StepStatus` dataclasses/enums |
| `nodes.py` | One function per task — pure, no flow awareness |
| `graph.py` | Flow definition + engine: routes `PUT /tasks` through the correct node |
| `service.py` | `CandidatesInfo` (in-memory store) + `AdmissionsService` (glue between API and FlowManager) |
| `main.py` | FastAPI app, REST endpoints only — no business logic |

---

## REST Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/users` | Create user, return unique ID |
| `GET` | `/flow` | Return ordered step list (respects `hidden` flag per user) |
| `GET` | `/users/{id}/current` | Current step + task for the user |
| `PUT` | `/tasks` | Mark task complete; payload: `step_name, task_name, user_id, task_payload` |
| `GET` | `/users/{id}/status` | `accepted` / `rejected` / `in_progress` |

---

## Conventions
- Nodes are pure functions: `(candidate: Candidate, payload: dict) -> Command`
- No business logic in the API layer
- Step names are string constants defined once (e.g. in `models.py`) — never hard-coded in multiple places
- Do not add comments that just narrate the code; only explain non-obvious intent
