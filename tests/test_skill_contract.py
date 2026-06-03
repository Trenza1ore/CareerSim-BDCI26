"""Tests for submission validation helpers."""

from pathlib import Path

from career_sim_runner.constants import SUBMISSION_MODE_SKILL_BUNDLE
from career_sim_runner.skill_contract import validate_submission_contract


def fixture_submission() -> Path:
    """Return the real sample submission path."""
    return Path(__file__).resolve().with_name("fixtures") / "solution"


def test_validate_submission_contract_fixture() -> None:
    """The real sample submission should validate successfully."""
    details = validate_submission_contract(fixture_submission())
    assert details["submission_mode"] == SUBMISSION_MODE_SKILL_BUNDLE
    assert details["submission_name"] == "flash-tomato"
