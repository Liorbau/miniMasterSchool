"""
FastAPI entry point. Routing, Pydantic validation, and HTTP responses only.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from service import AdmissionsService, InvalidFlowOperationError, UserNotFoundError

app = FastAPI(title="miniMasterSchool")
service = AdmissionsService()


class CreateUserRequest(BaseModel):
    email: str


class CreateUserResponse(BaseModel):
    user_id: int


class TaskRequest(BaseModel):
    user_id: int
    step_name: str
    task_name: str
    payload: dict


class TaskResponse(BaseModel):
    current_step: str | None
    completed_steps: dict[str, str]


@app.post("/users", response_model=CreateUserResponse, status_code=201)
def create_user(body: CreateUserRequest):
    user_id = service.create_user(body.email)
    return CreateUserResponse(user_id=user_id)


@app.get("/flow")
def get_flow(user_id: int):
    flow = service.get_flow(user_id)
    if flow is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"flow": flow}


@app.get("/users/{user_id}/current")
def get_current(user_id: int):
    current = service.get_current(user_id)
    if current is None:
        raise HTTPException(status_code=404, detail="User not found")
    return current


@app.put("/tasks", response_model=TaskResponse, status_code=200)
def complete_task(body: TaskRequest):
    try:
        candidate = service.complete_task(
            body.user_id, body.step_name, body.task_name, body.payload
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
    except InvalidFlowOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskResponse(
        current_step=candidate.current_step,
        completed_steps=dict(candidate.completed_steps),
    )


@app.get("/users/{user_id}/status")
def get_status(user_id: int):
    status = service.get_status(user_id)
    if status is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": status}
