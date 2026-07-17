"""Tests for participant environment setup helpers."""

from pathlib import Path

from ruamel.yaml import YAML

from career_sim_runner import setup


def test_tool_availability_accepts_windows_executables(monkeypatch, tmp_path: Path) -> None:
    """Resolve companion commands beside a ``.exe`` JiuwenSwarm launcher."""
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    commands = {
        "jiuwenswarm-start": scripts_dir / "jiuwenswarm-start.EXE",
        "career-emulator-mcp": scripts_dir / "career-emulator-mcp.EXE",
        "fastmcp": scripts_dir / "fastmcp.EXE",
    }

    def fake_which(command: str, path: str | None = None) -> str | None:
        resolved = commands.get(command)
        if resolved is None or (path is not None and Path(path) != scripts_dir):
            return None
        return str(resolved)

    setup.tool_availability.cache_clear()
    monkeypatch.setattr(setup.shutil, "which", fake_which)

    availability = setup.tool_availability()

    assert availability["career-emulator-mcp"] is True
    assert availability["jiuwenswarm-start"] is True
    assert availability["path"] == str(scripts_dir.resolve())
    setup.tool_availability.cache_clear()


def test_instance_config_uses_absolute_mcp_command(monkeypatch, tmp_path: Path) -> None:
    """The named instance must not depend on its background PATH on Windows."""
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    mcp_command = scripts_dir / "career-emulator-mcp.EXE"
    mcp_command.write_text("fixture", encoding="utf-8")
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(setup, "ensure_instance_initialized", lambda: tmp_path)
    monkeypatch.setattr(setup, "jiuwenswarm_config_path", lambda: config_path)
    monkeypatch.setattr(setup, "ensure_instance_env_overlay", lambda: tmp_path / ".env")
    monkeypatch.setattr(
        setup,
        "tool_availability",
        lambda: {"career-emulator-mcp": True, "jiuwenswarm-start": True, "path": str(scripts_dir)},
    )
    monkeypatch.setattr(
        setup.shutil,
        "which",
        lambda command, path=None: str(mcp_command) if command == "career-emulator-mcp" else None,
    )

    setup.ensure_instance_configured()

    yaml = YAML(typ="safe")
    payload = yaml.load(config_path.read_text(encoding="utf-8"))
    configured = payload["mcp"]["servers"][0]
    assert Path(configured["command"]).is_absolute()
    assert Path(configured["command"]) == mcp_command
    assert configured["args"] == ["--update", "distribution", "-c"]
