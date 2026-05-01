""" 
This file contains the flow definition and the engine that
routes the tasks through the ordered flow.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from models import Candidate, Command
import nodes


@dataclass
class Step:
    name: str
    tasks: List[str]
    is_hidden: bool = False


FLOW: List[Step] = [
    Step(name="personal_details", tasks=["personal_details"]),
    Step(name="iq_test",          tasks=["iq_test"]),
    Step(name="interview",        tasks=["schedule_interview", "perform_interview"]),
    Step(name="sign_contract",    tasks=["upload_id", "sign_contract"]),
    Step(name="payment",          tasks=["payment"]),
    Step(name="join_slack",       tasks=["join_slack"]),
]

# Flat ordered sequence of every task across all steps — used for next-task look-ups.
_ALL_TASKS: List[str] = [task for step in FLOW for task in step.tasks]

TASK_HANDLERS: Dict[str, Callable[[Candidate, dict], Command]] = {
    "personal_details":   nodes.personal_details_form,
    "iq_test":            nodes.iq_test,
    "schedule_interview": nodes.schedule_interview,
    "perform_interview":  nodes.perform_interview,
    "upload_id":          nodes.upload_id,
    "sign_contract":      nodes.sign_contract,
    "payment":            nodes.payment,
    "join_slack":         nodes.join_slack,
}


class FlowManager:
    def get_next_task(self, current_task_name: str) -> Optional[str]:
        idx = _ALL_TASKS.index(current_task_name)
        next_idx = idx + 1
        return _ALL_TASKS[next_idx] if next_idx < len(_ALL_TASKS) else None

    def get_visible_flow(self, candidate: Candidate) -> List[Step]:
        return [step for step in FLOW if not step.is_hidden]
