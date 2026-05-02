"""This file contains the models for the project."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


class StepStatus(str, Enum):
    """Tracks progress state of each enrollment step."""

    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Candidate:
    """A user progressing through the enrollment workflow."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    current_step: str = ""
    timestamp: Optional[datetime] = None
    iq_score: Optional[int] = None
    completed_steps: Dict[str, StepStatus] = field(default_factory=dict)
    is_accepted: bool = False
    task_sequence: List[str] = field(default_factory=list)


@dataclass
class Command:
    """Step handler return value: controls flow and state updates."""

    status: Optional[StepStatus] = None
    update: Dict[str, Any] = field(default_factory=dict)
    goto: Optional[str] = None
