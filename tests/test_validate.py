"""Tests for participant runtime validation."""

from pathlib import Path

from career_sim_runner.validate import _has_dataset_files


def test_dataset_validation_accepts_distribution_data(tmp_path: Path) -> None:
    """The installed BDCI distribution uses encrypted ``.data`` files."""
    (tmp_path / "health_zero.data").write_text("fixture", encoding="utf-8")

    assert _has_dataset_files(tmp_path)
