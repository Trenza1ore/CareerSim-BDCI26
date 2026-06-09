"""Tests for headless JiuwenSwarm websocket helpers."""

import pytest

from career_sim_runner.models import InstallRecord
from career_sim_runner.skill_contract import SubmissionError
from career_sim_runner.ws_client import _build_envelope, build_play_prompt, resolve_run_mode


def _install_record(*, mode: str = "agent.plan", instruction: str = "") -> InstallRecord:
    """Return an install record fixture for websocket tests."""
    return InstallRecord(
        submission_dir="/tmp/submission",
        submission_name="fixture-team",
        skill_dir="/tmp/skills",
        skill_name="submission-skills",
        manifest={
            "mode": mode,
            "instruction": instruction,
            "participant_skill_names": ["monthly-action-decision", "report-generation"],
        },
    )


def test_build_play_prompt_includes_manifest_instruction() -> None:
    """Prompt rendering should append extra manifest instructions when present."""
    prompt = build_play_prompt(_install_record(instruction="Prefer conservative actions when unsure."))
    assert "monthly-action-decision" in prompt
    assert "report-generation" in prompt
    assert "Specified Instructions" in prompt
    assert "Prefer conservative actions when unsure." in prompt


def test_resolve_run_mode_uses_manifest_value() -> None:
    """Supported manifest modes should flow through to the websocket payload."""
    assert resolve_run_mode(_install_record(mode="code.team")) == "code.team"


def test_resolve_run_mode_rejects_unsupported() -> None:
    """Unsupported manifest modes should raise SubmissionError."""
    with pytest.raises(SubmissionError):
        resolve_run_mode(_install_record(mode="unsupported-mode"))


def test_build_envelope_uses_selected_mode() -> None:
    """Envelope generation should send the resolved JiuwenSwarm mode."""
    envelope = _build_envelope("prompt", "drive-session", "agent.plan")
    assert envelope["params"]["mode"] == "agent.plan"
