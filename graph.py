"""
Ordered flow config and orchestration: maps tasks to handlers, advances state.
Default order is FLOW; nodes may return Command.goto for rare jumps off the spine.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from models import Candidate, Command, StepStatus
import nodes


@dataclass
class Step:
    """One admissions step: display name and its ordered task keys."""

    name: str
    tasks: List[str]


FLOW: List[Step] = [
    Step(name="personal_details", tasks=["personal_details"]),
    Step(name="iq_test", tasks=["iq_test"]),
    Step(name="interview", tasks=["schedule_interview", "perform_interview"]),
    Step(name="sign_contract", tasks=["upload_id", "sign_contract"]),
    Step(name="payment", tasks=["payment"]),
    Step(name="join_slack", tasks=["join_slack"]),
]

_ALL_TASKS: List[str] = [task for step in FLOW for task in step.tasks]

TASK_HANDLERS: Dict[str, Callable[[Candidate, dict], Command]] = {
    "personal_details": nodes.personal_details_form,
    "iq_test": nodes.iq_test,
    "schedule_interview": nodes.schedule_interview,
    "perform_interview": nodes.perform_interview,
    "upload_id": nodes.upload_id,
    "sign_contract": nodes.sign_contract,
    "payment": nodes.payment,
    "join_slack": nodes.join_slack,
}


class FlowManager:
    """Resolves next task from FLOW; runs handlers; applies Command (update, goto)."""

    def get_next_task(self, current_task_name: str) -> Optional[str]:
        """Next task in FLOW order after current_task_name, or None at end."""
        idx = _ALL_TASKS.index(current_task_name)
        next_idx = idx + 1
        return _ALL_TASKS[next_idx] if next_idx < len(_ALL_TASKS) else None

    def process_task(
        self, candidate: Candidate, task_name: str, payload: dict
    ) -> Candidate:
        """Run handler, merge update, record status. On success: goto if set, else next in FLOW."""
        handler = TASK_HANDLERS.get(task_name)

        if handler is None:
            return candidate

        command = handler(candidate, payload)
        candidate.completed_steps[task_name] = command.status

        for key, value in command.update.items():
            if hasattr(candidate, key):
                setattr(candidate, key, value)

        if command.goto:
            try:
                idx = candidate.task_sequence.index(task_name)
                candidate.task_sequence.insert(idx + 1, command.goto)
            except ValueError:
                candidate.task_sequence.append(command.goto)
            candidate.current_step = command.goto
        elif command.status == StepStatus.COMPLETED:
            try:
                idx = candidate.task_sequence.index(task_name)
                next_task = (
                    candidate.task_sequence[idx + 1]
                    if idx + 1 < len(candidate.task_sequence)
                    else None
                )
            except ValueError:
                next_task = None
            candidate.current_step = next_task
            if next_task is None:
                candidate.is_accepted = True

        return candidate
