""" 
This file contains the nodes for the project,
each node is a function that receives a candidate and a payload,
performs the node's logics, and returns a command. 
"""

from models import Candidate, Command
from typing import Any


def personal_details_form(candidate: Candidate, payload: Any) -> Command:
    pass


def iq_test(candidate: Candidate, payload: Any) -> Command:
    pass


def schedule_interview(candidate: Candidate, payload: Any) -> Command:
    pass


def perform_interview(candidate: Candidate, payload: Any) -> Command:
    pass


def upload_id(candidate: Candidate, payload: Any) -> Command:
    pass


def sign_contract(candidate: Candidate, payload: Any) -> Command:
    pass


def payment(candidate: Candidate, payload: Any) -> Command:
    pass


def join_slack(candidate: Candidate, payload: Any) -> Command:
    pass
