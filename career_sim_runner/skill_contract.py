"""Submission layout and skill contract helpers."""

import json
from pathlib import Path
from typing import Any

from career_sim_runner.constants import (
    SUBMISSION_MODE_SKILL_BUNDLE,
)


class SubmissionError(ValueError):
    """Raised when a submission does not match the expected contract."""


def resolve_skills_root(submission_dir: Path) -> Path:
    """Return the root directory for a supported submission."""
    root = submission_dir.expanduser().resolve()
    if _is_skill_bundle(root):
        return root
    msg = "Expected a submission like `solution/` with `skills/*/SKILL.md`."
    raise SubmissionError(msg)


def load_manifest(submission_dir: Path) -> dict[str, Any]:
    """Load submission metadata from ``manifest.json``."""
    manifest_path = submission_dir / "manifest.json"
    if manifest_path.is_file():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {}


def submission_name(submission_dir: Path, manifest: dict[str, Any]) -> str:
    """Derive a stable short label for logs and reports."""
    if manifest.get("team") or manifest.get("name"):
        return str(manifest.get("team") or manifest.get("name"))
    return submission_dir.resolve().name


def validate_submission_contract(submission_dir: Path) -> dict[str, Any]:
    """Validate layout and return normalized submission metadata."""
    root = resolve_skills_root(submission_dir)
    manifest = load_manifest(root)
    mode = detect_submission_mode(root)
    details: dict[str, Any] = {
        "submission_dir": str(root),
        "submission_name": submission_name(root, manifest),
        "manifest": manifest,
        "submission_mode": mode,
    }
    skill_ids = list_bundle_skill_ids(root)
    _validate_skill_bundle(root)
    details["skill_ids"] = skill_ids
    return details


def detect_submission_mode(submission_dir: Path) -> str:
    """Detect the supported submission mode for ``submission_dir``."""
    root = submission_dir.expanduser().resolve()
    if _is_skill_bundle(root):
        return SUBMISSION_MODE_SKILL_BUNDLE
    msg = f"Unsupported submission format at {root}"
    raise SubmissionError(msg)


def list_bundle_skill_ids(submission_dir: Path) -> list[str]:
    """Return sorted skill ids from a SKILL.md bundle submission."""
    skills_root = submission_dir.expanduser().resolve() / "skills"
    if not skills_root.is_dir():
        return []
    skill_ids = [child.name for child in skills_root.iterdir() if child.is_dir() and (child / "SKILL.md").is_file()]
    return sorted(skill_ids)


def _is_skill_bundle(root: Path) -> bool:
    """Return whether ``root`` looks like a real competition skill bundle."""
    return bool(list_bundle_skill_ids(root))


def _validate_skill_bundle(root: Path) -> None:
    """Validate the real SKILL.md-based submission bundle."""
    if not (root / "manifest.json").is_file():
        msg = f"Missing submission manifest.json at {root / 'manifest.json'}"
        raise SubmissionError(msg)
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        msg = "Missing skills folder"
        raise SubmissionError(msg)
