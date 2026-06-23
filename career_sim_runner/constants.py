"""Shared constants for the standalone participant runner."""

from pathlib import Path

RUNNER_PACKAGE_DIR: Path = Path(__file__).resolve().parent
REPO_ROOT: Path = RUNNER_PACKAGE_DIR.parent
DEFAULT_INSTANCE_NAME: str = "career_emu"
INSTANCES_ROOT: Path = Path.home() / ".jiuwenswarm-instances"
INSTANCE_ROOT: Path = INSTANCES_ROOT / DEFAULT_INSTANCE_NAME
RUNTIME_ROOT: Path = REPO_ROOT / ".career_sim_runner" / DEFAULT_INSTANCE_NAME
DEFAULT_DB_PATH: Path = RUNTIME_ROOT / "career_emulator.sqlite3"
DEFAULT_EMULATOR_LOG_DIR: Path = RUNTIME_ROOT / "emulator_logs"
DEFAULT_RUNS_DIR: Path = RUNTIME_ROOT / "runs"
DEFAULT_OUTPUT_ROOT: Path = RUNTIME_ROOT / "outputs"
DRIVE_SESSION_PREFIX: str = "career-sim-runner"
DEFAULT_TIMEOUT_S: float = 7200.0

JWS_DATA_DIR_ENV: str = "JIUWENSWARM_DATA_DIR"
RUNNER_ENV_TEMPLATE: str = ".env.example"
RUNNER_CONFIG_TEMPLATE: str = "jiuwenswarm.config.yaml"
ACTIVE_INSTALL_FILE: str = "active_install.json"
LAST_DRIVE_SESSION_FILE: str = "last_drive_session.txt"
LAST_OUTPUT_DIR_FILE: str = "last_output_dir.txt"

CAREER_EMULATOR_ACTIVE_LONG_CHAIN_LIMIT: int = 1
CAREER_EMULATOR_MONTHLY_EVENT_LIMIT: int = 3
CAREER_EMULATOR_MAX_NOTE_LENGTH: int = 1000
SUBMISSION_MODE_SKILL_BUNDLE: str = "skill_bundle"
SUPPORTED_RUN_MODES: frozenset[str] = frozenset({"agent.fast", "agent.plan", "team"})

MEMORY_MD_CONTENT = """
### 长期记忆

### 此处应保存的内容

保存所有能帮助你更高效工作的信息。这里是你的持久参考资料。

例如:

- 项目信息
- 与技能执行相关的用户设置和偏好
""".strip()
