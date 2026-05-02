"""
Task handlers: each takes a Candidate and payload, returns a Command.
No flow order here. Only validation and what state to merge back.
"""

from typing import Any

from models import Candidate, Command, StepStatus


def personal_details_form(candidate: Candidate, payload: dict) -> Command:
    """Payload: user_id, first_name, last_name, email, timestamp."""
    required = {"user_id", "first_name", "last_name", "email", "timestamp"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    return Command(
        status=StepStatus.COMPLETED,
        update={f: payload[f] for f in required},
    )


def iq_test(candidate: Candidate, payload: dict) -> Command:
    """Payload: user_id, test_id, score, timestamp. Completes only if score > 75."""
    required = {"user_id", "test_id", "score", "timestamp"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    if payload["score"] <= 75:
        return Command(status=StepStatus.FAILED)

    return Command(
        status=StepStatus.COMPLETED,
        update={"iq_score": payload["score"], "timestamp": payload["timestamp"]},
    )


def schedule_interview(candidate: Candidate, payload: Any) -> Command:
    """Payload: user_id, interview_date."""
    required = {"user_id", "interview_date"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    return Command(status=StepStatus.COMPLETED, update={})


def perform_interview(candidate: Candidate, payload: Any) -> Command:
    """Payload: user_id, interview_date, interviewer_id, decision.
    Completes when decision is passed_interview."""
    required = {"user_id", "interview_date", "interviewer_id", "decision"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    if payload["decision"] == "passed_interview":
        return Command(status=StepStatus.COMPLETED)

    return Command(status=StepStatus.FAILED, update={})


def upload_id(candidate: Candidate, payload: Any) -> Command:
    """Payload: user_id, passport_number, timestamp. Saves passport_number only."""
    required = {"user_id", "passport_number", "timestamp"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    return Command(
        status=StepStatus.COMPLETED,
        update={
            "passport_number": payload["passport_number"],
            "timestamp": payload["timestamp"],
        },
    )


def sign_contract(candidate: Candidate, payload: Any) -> Command:
    """Payload: user_id, timestamp. Marks contract step as signed."""
    required = {"user_id", "timestamp"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    return Command(
        status=StepStatus.COMPLETED,
        update={"timestamp": payload["timestamp"]},
    )


def payment(candidate: Candidate, payload: Any) -> Command:
    """Payload: user_id, payment_id, timestamp. Records a completed payment."""
    required = {"user_id", "payment_id", "timestamp"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    return Command(
        status=StepStatus.COMPLETED,
        update={"timestamp": payload["timestamp"]},
    )


def join_slack(candidate: Candidate, payload: Any) -> Command:
    """Payload: user_id, email, timestamp. Final handoff for workspace access."""
    required = {"user_id", "email", "timestamp"}

    if not all(payload.get(f) not in (None, "") for f in required):
        return Command(status=StepStatus.FAILED)

    return Command(
        status=StepStatus.COMPLETED,
        update={"timestamp": payload["timestamp"]},
    )
