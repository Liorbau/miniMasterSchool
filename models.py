"""This file contains the models for the project."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


class StepStatus(Enum):
    """Tracks progress state of each enrollment step."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Candidate:
    """A user progressing through the enrollment workflow."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    timestamp: datetime
    current_step: str = ""
    iq_score: Optional[int] = None
    completed_steps: Dict[str, StepStatus] = field(default_factory=dict)


@dataclass
class Command:
    """Step handler return value: controls flow and state updates."""

    status: Optional[StepStatus] = None
    update: Dict[str, Any] = field(default_factory=dict)
    goto: Optional[str] = None
