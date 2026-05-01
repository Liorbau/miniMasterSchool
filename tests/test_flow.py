import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime
from models import Candidate, Command, StepStatus
from graph import FLOW, TASK_HANDLERS, FlowManager, Step


def make_candidate(**kwargs) -> Candidate:
    defaults = dict(
        user_id=1,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        timestamp=datetime(2026, 1, 1),
    )
    return Candidate(**{**defaults, **kwargs})


# --- StepStatus ---

def test_step_status_values_are_enum_members():
    assert StepStatus.COMPLETED.value == "completed"
    assert StepStatus.FAILED.value == "failed"
    assert StepStatus.PENDING.value == "pending"

def test_step_status_invalid_value_raises():
    with pytest.raises(ValueError):
        StepStatus("typo")


# --- Candidate defaults ---

def test_candidate_completed_steps_not_shared():
    """Mutable default must not be shared across instances."""
    a = make_candidate(user_id=1)
    b = make_candidate(user_id=2)
    a.completed_steps["iq_test"] = StepStatus.COMPLETED
    assert "iq_test" not in b.completed_steps


# --- FLOW integrity ---

def test_flow_order():
    names = [s.name for s in FLOW]
    assert names == [
        "personal_details", "iq_test", "interview",
        "sign_contract", "payment", "join_slack",
    ]

def test_every_task_has_a_handler():
    for step in FLOW:
        for task in step.tasks:
            assert task in TASK_HANDLERS, f"No handler for task '{task}'"

def test_no_hidden_steps_in_base_flow():
    assert all(not step.is_hidden for step in FLOW)


# --- FlowManager.get_next_task ---

fm = FlowManager()

def test_get_next_task_within_step():
    assert fm.get_next_task("schedule_interview") == "perform_interview"

def test_get_next_task_crosses_step_boundary():
    assert fm.get_next_task("iq_test") == "schedule_interview"

def test_get_next_task_last_task_returns_none():
    assert fm.get_next_task("join_slack") is None

def test_get_next_task_unknown_raises():
    with pytest.raises(ValueError):
        fm.get_next_task("nonexistent_task")


# --- FlowManager.get_visible_flow ---

def test_visible_flow_hides_hidden_steps():
    hidden_step = Step(name="secret", tasks=["secret"], is_hidden=True)
    original_flow = FLOW.copy()
    FLOW.append(hidden_step)
    try:
        visible = fm.get_visible_flow(make_candidate())
        assert all(s.name != "secret" for s in visible)
    finally:
        FLOW.clear()
        FLOW.extend(original_flow)

def test_visible_flow_returns_all_when_nothing_hidden():
    visible = fm.get_visible_flow(make_candidate())
    assert visible == FLOW
