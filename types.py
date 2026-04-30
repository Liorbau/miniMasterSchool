from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from turtle import update
from typing import Optional, Dict, Any


class StepStatus:
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
    completed_steps: Dict[str, StepStatus] = {}  # step_name -> status

@dataclass
class Command:
    """Step handler return value: controls flow and state updates."""
    goto: Optional[str] = None  # jump to a specific step
    status: Optional[StepStatus] = None  # mark current step status
    update: Optional[Dict[str, Any]] = {}  # merge into candidate data