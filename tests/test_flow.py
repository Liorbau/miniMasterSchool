from datetime import datetime

import pytest

from graph import FLOW, TASK_HANDLERS, FlowManager
from models import Candidate, Command, StepStatus
from service import AdmissionsService, InvalidFlowOperationError


def test_get_status_rejected_when_off_spine_task_marked_failed():
    svc = AdmissionsService()
    uid = svc.create_user("offspine@example.com")
    c = svc.candidates_info.get_by_id(uid)
    c.completed_steps["second_chance_iq"] = StepStatus.FAILED
    svc.candidates_info.update(c)
    assert svc.get_status(uid) == "rejected"


def make_candidate(**kwargs) -> Candidate:
    defaults = {
        "user_id": 1,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "timestamp": datetime(2026, 1, 1),
    }
    return Candidate(**{**defaults, **kwargs})


# --- StepStatus ---


def test_step_status_values_are_enum_members():
    assert StepStatus.COMPLETED.value == "completed"
    assert StepStatus.FAILED.value == "failed"


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
        "personal_details",
        "iq_test",
        "interview",
        "sign_contract",
        "payment",
        "join_slack",
    ]


def test_every_task_has_a_handler():
    for step in FLOW:
        for task in step.tasks:
            assert task in TASK_HANDLERS, f"No handler for task '{task}'"


def test_step_is_name_and_tasks_only():
    step = FLOW[0]
    assert step.name == "personal_details"
    assert step.tasks == ["personal_details"]
    assert not hasattr(step, "is_hidden")


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


def test_process_task_unknown_task_leaves_candidate_unchanged():
    candidate = make_candidate(current_step="iq_test")
    before_steps = dict(candidate.completed_steps)
    before_step = candidate.current_step
    fm.process_task(candidate, "not_a_real_task", {})
    assert candidate.completed_steps == before_steps
    assert candidate.current_step == before_step


def test_process_task_sets_accepted_when_last_task_in_sequence_completes():
    candidate = make_candidate(current_step="join_slack", user_id=1)
    candidate.task_sequence = [t for step in FLOW for t in step.tasks]
    fm.process_task(
        candidate,
        "join_slack",
        {"user_id": 1, "email": "ada@example.com", "timestamp": "2026-01-01"},
    )
    assert candidate.is_accepted is True
    assert candidate.current_step is None


def test_goto_splices_target_into_task_sequence(monkeypatch):
    def fake_iq(_, payload):
        return Command(status=StepStatus.COMPLETED, goto="bonus_round")

    monkeypatch.setitem(TASK_HANDLERS, "iq_test", fake_iq)
    candidate = make_candidate(current_step="iq_test")
    candidate.task_sequence = ["iq_test", "schedule_interview"]
    fm.process_task(
        candidate,
        "iq_test",
        {"user_id": 1, "test_id": "t1", "score": 80, "timestamp": "2026-01-01"},
    )
    assert candidate.task_sequence == ["iq_test", "bonus_round", "schedule_interview"]
    assert candidate.current_step == "bonus_round"


# --- AdmissionsService guards ---


def test_complete_task_rejects_mismatched_payload_user_id():
    svc = AdmissionsService()
    uid = svc.create_user("test@example.com")
    with pytest.raises(
        InvalidFlowOperationError, match="Payload user_id does not match"
    ):
        svc.complete_task(
            uid, "personal_details", "personal_details", {"user_id": uid + 99}
        )


def test_complete_task_accepts_matching_payload_user_id():
    svc = AdmissionsService()
    uid = svc.create_user("test2@example.com")
    # Should not raise — user_id in payload matches the URL user_id
    svc.complete_task(
        uid,
        "personal_details",
        "personal_details",
        {
            "user_id": uid,
            "first_name": "Ada",
            "last_name": "L",
            "email": "x@x.com",
            "timestamp": "2026-01-01",
        },
    )


def test_complete_task_blocked_after_rejection():
    svc = AdmissionsService()
    uid = svc.create_user("reject@example.com")
    # Fail the iq_test step to put candidate in rejected state
    svc.complete_task(
        uid,
        "personal_details",
        "personal_details",
        {
            "user_id": uid,
            "first_name": "X",
            "last_name": "Y",
            "email": "a@b.com",
            "timestamp": "2026-01-01",
        },
    )
    svc.complete_task(
        uid,
        "iq_test",
        "iq_test",
        {"user_id": uid, "test_id": "t1", "score": 10, "timestamp": "2026-01-01"},
    )  # score < 75 → rejected
    with pytest.raises(InvalidFlowOperationError, match="already closed"):
        svc.complete_task(uid, "iq_test", "iq_test", {"score": 90})
