.PHONY: format lint docstring sync test setup run score
.DEFAULT_GOAL := sync

# ----- Useful for participants of the competition -----

# Install dependencies
sync:
	uv sync

# Setup environment variables and mcp config
setup:
	uv run python -m career_sim_runner setup

# Play a game with current solution
play:
	@uv pip install -U career-emulator-bdci26
	uv run python -m career_sim_runner play-headless --submission solution

# Check last run's score
score:
	uv run python -m career_sim_runner score

# Start JiuwenSwarm instance in current terminal
start-jiuwen:
	uv run jiuwenswarm-start --name career_emu all

# ----- Please ignore, this is only used by internal developers -----

# Resume an unfinished game
resume:
	uv run python -m career_sim_runner play-headless --submission solution --continue

# Format code with ruff
format:
	uv run ruff check --select I --select E --select F --fix || true
	uv run ruff format || true

# Type check with mypy
lint:
	@uv run --group format mypy -p career_sim_runner

# Check docstring convention (with pydocstyle rules in ruff)
docstring:
	@uv run uv run ruff check --select D career_sim_runner/

# Check format, docstring, typing
check: format docstring lint

# Run unit tests
test:
	@uv run pytest tests/
