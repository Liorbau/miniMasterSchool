"""
Ordered flow config and orchestration: maps tasks to handlers, advances
state. Task logic stays in nodes.py, this file only wires order and visibility.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from models import Candidate, Command, StepStatus
import nodes


@dataclass
class Step:
    """
    One admissions step: logical name,
    its task keys,
    optional hide from generic flow lists.
    """

    name: str
    tasks: List[str]
    is_hidden: bool = False


# Single ordered definition
FLOW: List[Step] = [
    Step(name="personal_details", tasks=["personal_details"]),
    Step(name="iq_test", tasks=["iq_test"]),
    Step(name="interview", tasks=["schedule_interview", "perform_interview"]),
    Step(name="sign_contract", tasks=["upload_id", "sign_contract"]),
    Step(name="payment", tasks=["payment"]),
    Step(name="join_slack", tasks=["join_slack"]),
]

# Derived full task sequence for linear "what comes next".
_ALL_TASKS: List[str] = [task for step in FLOW for task in step.tasks]

# task_name string from FLOW -> node function.
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
    """
    Reads FLOW,
    exposes next-task resolution,
    per-user visible steps, and task execution.
    """

    def get_next_task(self, current_task_name: str) -> Optional[str]:
        """Next task in global order, or None."""
        idx = _ALL_TASKS.index(current_task_name)
        next_idx = idx + 1
        return _ALL_TASKS[next_idx] if next_idx < len(_ALL_TASKS) else None

    def get_visible_flow(self, candidate: Candidate) -> List[Step]:
        """Steps shown to this candidate."""
        return [step for step in FLOW if not step.is_hidden]

    def process_task(
        self, candidate: Candidate, task_name: str, payload: dict
    ) -> Candidate:
        """Run handler, merge update, record task status; advance step only on success or goto."""
        handler = TASK_HANDLERS.get(task_name)

        if handler is None:
            return candidate

        command = handler(candidate, payload)
        candidate.completed_steps[task_name] = command.status

        for key, value in command.update.items():
            if hasattr(candidate, key):
                setattr(candidate, key, value)

        if command.goto:
            candidate.current_step = command.goto
        elif command.status == StepStatus.COMPLETED:
            candidate.current_step = self.get_next_task(task_name)

        return candidate
