"""
Service layer: glue between REST endpoints and FlowManager.
"""

from typing import Dict, List, Optional

from graph import FLOW, FlowManager
from models import Candidate, StepStatus


class UserNotFoundError(Exception):
    pass


class InvalidFlowOperationError(Exception):
    pass


class CandidatesInfo:
    """In-memory store for all candidates, keyed by user_id."""

    def __init__(self) -> None:
        self._store: Dict[int, Candidate] = {}
        self._next_id: int = 1

    def create(self, email: str) -> Candidate:
        """Create a new Candidate with the first task pre-set as current_step."""
        first_task = FLOW[0].tasks[0]
        candidate = Candidate(
            user_id=self._next_id,
            first_name="",
            last_name="",
            email=email,
            current_step=first_task,
        )
        self._store[self._next_id] = candidate
        self._next_id += 1
        return candidate

    def get_by_id(self, user_id: int) -> Optional[Candidate]:
        return self._store.get(user_id)

    def update(self, candidate: Candidate) -> None:
        self._store[candidate.user_id] = candidate


class AdmissionsService:
    """Coordinates CandidatesInfo and FlowManager for all admission operations."""

    def __init__(self) -> None:
        self.candidates_info = CandidatesInfo()
        self.flow_manager = FlowManager()

    def create_user(self, email: str) -> int:
        candidate = self.candidates_info.create(email)
        return candidate.user_id

    def get_flow(self, user_id: int) -> Optional[List[dict]]:
        """Visible steps for this candidate. None if user not found."""
        candidate = self.candidates_info.get_by_id(user_id)

        if candidate is None:
            return None

        steps = self.flow_manager.get_visible_flow(candidate)
        return [{"name": step.name, "tasks": step.tasks} for step in steps]

    def get_current(self, user_id: int) -> Optional[dict]:
        """Current step name + task name. None if user not found."""
        candidate = self.candidates_info.get_by_id(user_id)
        if candidate is None:
            return None

        current_task = candidate.current_step
        step_name = _task_to_step(current_task)
        return {"step": step_name, "task": current_task}

    def complete_task(
        self, user_id: int, step_name: str, task_name: str, payload: dict
    ) -> Candidate:
        """Run the task handler and persist.
        Raises UserNotFoundError or InvalidFlowOperationError on invalid input."""
        candidate = self.candidates_info.get_by_id(user_id)
        if candidate is None:
            raise UserNotFoundError(user_id)

        actual_step = _task_to_step(task_name)
        if actual_step is None or actual_step != step_name:
            raise InvalidFlowOperationError(
                f"task '{task_name}' does not belong to step '{step_name}'"
            )

        if candidate.current_step != task_name:
            raise InvalidFlowOperationError(
                f"candidate is at '{candidate.current_step}', not '{task_name}'"
            )

        candidate = self.flow_manager.process_task(candidate, task_name, payload)
        self.candidates_info.update(candidate)
        return candidate

    def get_status(self, user_id: int) -> Optional[str]:
        """Returns accepted / rejected / in_progress. None if user not found."""
        candidate = self.candidates_info.get_by_id(user_id)

        if candidate is None:
            return None

        visible_steps = self.flow_manager.get_visible_flow(candidate)
        all_tasks = []
        for step in visible_steps:
            all_tasks.extend(step.tasks)

        if any(
            candidate.completed_steps.get(task) == StepStatus.FAILED
            for task in all_tasks
        ):
            return "rejected"

        if all(
            candidate.completed_steps.get(task) == StepStatus.COMPLETED
            for task in all_tasks
        ):
            return "accepted"

        return "in_progress"


def _task_to_step(task_name: Optional[str]) -> Optional[str]:
    """Reverse lookup: task_name -> parent Step name."""
    for step in FLOW:
        if task_name in step.tasks:
            return step.name
    return None
