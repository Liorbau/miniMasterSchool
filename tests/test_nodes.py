from datetime import datetime

import pytest

from models import Candidate, StepStatus
from nodes import (
    iq_test,
    join_slack,
    payment,
    perform_interview,
    personal_details_form,
    schedule_interview,
    sign_contract,
    upload_id,
)


def make_candidate(**kwargs) -> Candidate:
    defaults = {
        "user_id": 1,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "timestamp": datetime(2026, 1, 1),
    }
    return Candidate(**{**defaults, **kwargs})


CANDIDATE = make_candidate()


# --- personal_details_form ---


def test_personal_details_completes_on_valid_payload():
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "timestamp": "2026-01-01",
    }
    cmd = personal_details_form(CANDIDATE, payload)
    assert cmd.status == StepStatus.COMPLETED


def test_personal_details_update_contains_all_fields():
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "timestamp": "2026-01-01",
    }
    cmd = personal_details_form(CANDIDATE, payload)
    assert cmd.update["first_name"] == "Ada"
    assert cmd.update["email"] == "ada@example.com"


def test_personal_details_fails_on_missing_field():
    payload = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
    cmd = personal_details_form(CANDIDATE, payload)
    assert cmd.status == StepStatus.FAILED


def test_personal_details_fails_on_empty_field():
    payload = {
        "first_name": "",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "timestamp": "2026-01-01",
    }
    cmd = personal_details_form(CANDIDATE, payload)
    assert cmd.status == StepStatus.FAILED


# --- iq_test ---


def test_iq_test_passes_for_score_above_75():
    payload = {"user_id": 1, "test_id": "t1", "score": 76, "timestamp": "2026-01-01"}
    cmd = iq_test(CANDIDATE, payload)
    assert cmd.status == StepStatus.COMPLETED


def test_iq_test_fails_for_score_exactly_75():
    payload = {"user_id": 1, "test_id": "t1", "score": 75, "timestamp": "2026-01-01"}
    cmd = iq_test(CANDIDATE, payload)
    assert cmd.status == StepStatus.FAILED


def test_iq_test_fails_for_score_below_75():
    payload = {"user_id": 1, "test_id": "t1", "score": 50, "timestamp": "2026-01-01"}
    cmd = iq_test(CANDIDATE, payload)
    assert cmd.status == StepStatus.FAILED


def test_iq_test_fails_on_missing_score():
    payload = {"user_id": 1, "test_id": "t1", "timestamp": "2026-01-01"}
    cmd = iq_test(CANDIDATE, payload)
    assert cmd.status == StepStatus.FAILED


# --- perform_interview ---


def test_perform_interview_passes_on_correct_decision():
    payload = {
        "user_id": 1,
        "interview_date": "2026-02-01",
        "interviewer_id": "i1",
        "decision": "passed_interview",
    }
    cmd = perform_interview(CANDIDATE, payload)
    assert cmd.status == StepStatus.COMPLETED


def test_perform_interview_fails_on_wrong_decision():
    payload = {
        "user_id": 1,
        "interview_date": "2026-02-01",
        "interviewer_id": "i1",
        "decision": "failed_interview",
    }
    cmd = perform_interview(CANDIDATE, payload)
    assert cmd.status == StepStatus.FAILED


def test_perform_interview_fails_on_missing_decision():
    payload = {"user_id": 1, "interview_date": "2026-02-01", "interviewer_id": "i1"}
    cmd = perform_interview(CANDIDATE, payload)
    assert cmd.status == StepStatus.FAILED


# --- simple completion nodes (no special pass condition) ---


@pytest.mark.parametrize(
    "node, payload",
    [
        (
            schedule_interview,
            {"user_id": 1, "interview_date": "2026-02-01"},
        ),
        (
            upload_id,
            {"user_id": 1, "passport_number": "AB123", "timestamp": "2026-01-01"},
        ),
        (
            sign_contract,
            {"user_id": 1, "timestamp": "2026-01-01"},
        ),
        (
            payment,
            {"user_id": 1, "payment_id": "p1", "timestamp": "2026-01-01"},
        ),
        (
            join_slack,
            {"user_id": 1, "email": "ada@example.com", "timestamp": "2026-01-01"},
        ),
    ],
)
def test_simple_node_completes_on_valid_payload(node, payload):
    cmd = node(CANDIDATE, payload)
    assert cmd.status == StepStatus.COMPLETED


@pytest.mark.parametrize(
    "node, partial_payload",
    [
        (schedule_interview, {"user_id": 1}),
        (upload_id, {"user_id": 1, "passport_number": "AB123"}),
        (sign_contract, {"user_id": 1}),
        (payment, {"user_id": 1, "payment_id": "p1"}),
        (join_slack, {"user_id": 1, "email": "ada@example.com"}),
    ],
)
def test_simple_node_fails_on_missing_field(node, partial_payload):
    cmd = node(CANDIDATE, partial_payload)
    assert cmd.status == StepStatus.FAILED
